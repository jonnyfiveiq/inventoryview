"""AAP metrics utility archive import service.

Handles extraction of ZIP/tar.gz archives, CSV parsing with 2-line metadata
header stripping, and persistence of AAP host and job execution data.
"""

import csv
import io
import json
import logging
import re
import tarfile
import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import PurePosixPath

from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

# CSV filename patterns for identification
CSV_PATTERNS = {
    "main_host": re.compile(r"main_host[_\.]"),
    "job_host_summary": re.compile(r"job_host_summary[_\.]"),
    "main_jobevent": re.compile(r"main_jobevent[_\.]"),
    "indirect_managed": re.compile(r"main_indirectmanagednodeaudit[_\.]"),
}


def _classify_csv(filename: str) -> str | None:
    """Classify a CSV file by its filename pattern."""
    name = PurePosixPath(filename).name.lower()
    for csv_type, pattern in CSV_PATTERNS.items():
        if pattern.search(name):
            return csv_type
    return None


def _strip_metadata_header(content: str) -> str:
    """Strip the 2-line metadata header from AAP metrics CSV content.

    AAP metrics CSVs have:
      Line 1: collection timestamp metadata
      Line 2: AAP version info
      Line 3: actual CSV header row
      Line 4+: data rows
    """
    lines = content.split("\n")
    if len(lines) <= 2:
        return ""
    return "\n".join(lines[2:])


def _parse_csv(content: str) -> list[dict]:
    """Parse CSV content into list of dicts using DictReader."""
    stripped = _strip_metadata_header(content)
    if not stripped.strip():
        return []
    reader = csv.DictReader(io.StringIO(stripped))
    return list(reader)


def _extract_smbios_uuid(canonical_facts_str: str | None) -> str | None:
    """Extract SMBIOS UUID from canonical_facts JSON string."""
    if not canonical_facts_str:
        return None
    try:
        facts = json.loads(canonical_facts_str)
        if isinstance(facts, dict):
            machine_id = facts.get("ansible_machine_id") or facts.get("machine_id")
            if machine_id and isinstance(machine_id, str) and machine_id.strip():
                return machine_id.strip().lower()
    except (json.JSONDecodeError, ValueError):
        pass
    return None


async def extract_archive(file_content: bytes, filename: str) -> dict[str, list[dict]]:
    """Extract and parse CSVs from a metrics utility archive.

    Returns {csv_type: [rows]} for each recognised CSV type.
    Raises ValueError for invalid archives.
    """
    csvs: dict[str, list[dict]] = {
        "main_host": [],
        "job_host_summary": [],
        "main_jobevent": [],
        "indirect_managed": [],
    }

    file_count = 0

    if filename.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    if not info.filename.lower().endswith(".csv"):
                        continue
                    csv_type = _classify_csv(info.filename)
                    if csv_type is None:
                        continue
                    content = zf.read(info.filename).decode("utf-8", errors="replace")
                    rows = _parse_csv(content)
                    csvs[csv_type].extend(rows)
                    file_count += 1
        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid ZIP archive: {e}") from e

    elif filename.endswith((".tar.gz", ".tgz")):
        try:
            with tarfile.open(fileobj=io.BytesIO(file_content), mode="r:gz") as tf:
                for member in tf.getmembers():
                    if not member.isfile():
                        continue
                    if not member.name.lower().endswith(".csv"):
                        continue
                    csv_type = _classify_csv(member.name)
                    if csv_type is None:
                        continue
                    f = tf.extractfile(member)
                    if f is None:
                        continue
                    content = f.read().decode("utf-8", errors="replace")
                    rows = _parse_csv(content)
                    csvs[csv_type].extend(rows)
                    file_count += 1
        except tarfile.TarError as e:
            raise ValueError(f"Invalid tar.gz archive: {e}") from e
    else:
        raise ValueError(f"Unsupported file format: {filename}. Expected .zip or .tar.gz")

    if file_count == 0:
        raise ValueError(
            "No valid AAP CSV files found in archive. "
            "Expected files matching: main_host_*, job_host_summary_*, "
            "main_jobevent_*, main_indirectmanagednodeaudit_*"
        )

    return csvs


async def persist_import(
    pool: AsyncConnectionPool,
    csvs: dict[str, list[dict]],
    source_label: str,
) -> dict:
    """Persist parsed AAP data into relational tables.

    Returns import statistics.
    """
    now = datetime.now(UTC)
    stats = {
        "hosts_imported": 0,
        "hosts_updated": 0,
        "jobs_imported": 0,
        "events_counted": len(csvs.get("main_jobevent", [])),
        "indirect_nodes_imported": 0,
    }

    async with pool.connection() as conn:
        # --- Persist hosts ---
        host_id_map: dict[str, str] = {}  # aap host_id -> db uuid

        for row in csvs.get("main_host", []):
            host_id = row.get("id") or row.get("host_id") or ""
            hostname = row.get("hostname") or row.get("name") or ""
            if not host_id or not hostname:
                continue

            canonical_facts_str = row.get("canonical_facts")
            smbios_uuid = _extract_smbios_uuid(canonical_facts_str)
            org_id = row.get("org_id") or row.get("organization_id") or "default"
            inventory_id = row.get("inventory_id") or "default"

            canonical_facts_json = None
            if canonical_facts_str:
                try:
                    canonical_facts_json = json.loads(canonical_facts_str)
                except (json.JSONDecodeError, ValueError):
                    canonical_facts_json = None

            # Upsert host
            result = await conn.execute(
                """
                INSERT INTO aap_host (
                    host_id, hostname, canonical_facts, smbios_uuid,
                    org_id, inventory_id, first_seen, last_seen,
                    total_jobs, total_events, correlation_type, import_source
                ) VALUES (
                    %(host_id)s, %(hostname)s, %(canonical_facts)s, %(smbios_uuid)s,
                    %(org_id)s, %(inventory_id)s, %(now)s, %(now)s,
                    0, 0, 'direct', %(source_label)s
                )
                ON CONFLICT (host_id, org_id) DO UPDATE SET
                    hostname = EXCLUDED.hostname,
                    canonical_facts = COALESCE(EXCLUDED.canonical_facts, aap_host.canonical_facts),
                    smbios_uuid = COALESCE(EXCLUDED.smbios_uuid, aap_host.smbios_uuid),
                    last_seen = EXCLUDED.last_seen,
                    import_source = EXCLUDED.import_source,
                    updated_at = now()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                {
                    "host_id": host_id,
                    "hostname": hostname,
                    "canonical_facts": json.dumps(canonical_facts_json) if canonical_facts_json else None,
                    "smbios_uuid": smbios_uuid,
                    "org_id": org_id,
                    "inventory_id": inventory_id,
                    "now": now,
                    "source_label": source_label,
                },
            )
            row_result = await result.fetchone()
            if row_result:
                db_id = str(row_result["id"])
                is_insert = row_result["is_insert"]
                host_id_map[host_id] = db_id
                if is_insert:
                    stats["hosts_imported"] += 1
                else:
                    stats["hosts_updated"] += 1

        # --- Persist indirect managed nodes as hosts ---
        for row in csvs.get("indirect_managed", []):
            hostname = row.get("hostname") or ""
            if not hostname:
                continue

            managed_type = row.get("managed_type") or "indirect"
            unique_id = row.get("unique_identifier") or ""
            org_id = row.get("org_id") or "default"
            synthetic_host_id = f"indirect:{hostname}:{org_id}"

            result = await conn.execute(
                """
                INSERT INTO aap_host (
                    host_id, hostname, smbios_uuid,
                    org_id, inventory_id, first_seen, last_seen,
                    total_jobs, total_events, correlation_type, import_source
                ) VALUES (
                    %(host_id)s, %(hostname)s, %(unique_id)s,
                    %(org_id)s, 'indirect', %(now)s, %(now)s,
                    0, 0, 'indirect', %(source_label)s
                )
                ON CONFLICT (host_id, org_id) DO UPDATE SET
                    hostname = EXCLUDED.hostname,
                    smbios_uuid = COALESCE(EXCLUDED.smbios_uuid, aap_host.smbios_uuid),
                    last_seen = EXCLUDED.last_seen,
                    updated_at = now()
                RETURNING id, (xmax = 0) AS is_insert
                """,
                {
                    "host_id": synthetic_host_id,
                    "hostname": hostname,
                    "unique_id": unique_id or None,
                    "org_id": org_id,
                    "now": now,
                    "source_label": source_label,
                },
            )
            row_result = await result.fetchone()
            if row_result:
                db_id = str(row_result["id"])
                host_id_map[synthetic_host_id] = db_id
                if row_result["is_insert"]:
                    stats["indirect_nodes_imported"] += 1

        # --- Persist job executions ---
        for row in csvs.get("job_host_summary", []):
            host_id = row.get("host_id") or ""
            job_id = row.get("job_id") or row.get("id") or ""
            if not host_id or not job_id:
                continue

            db_host_id = host_id_map.get(host_id)
            if not db_host_id:
                continue

            job_name = row.get("job_name") or row.get("job__unified_job_name") or "unknown"
            executed_at_str = row.get("created") or row.get("modified") or ""

            try:
                executed_at = datetime.fromisoformat(
                    executed_at_str.replace("Z", "+00:00")
                ) if executed_at_str else now
            except ValueError:
                executed_at = now

            try:
                await conn.execute(
                    """
                    INSERT INTO aap_job_execution (
                        aap_host_id, job_id, job_name,
                        ok, changed, failures, dark, skipped,
                        project, org_name, inventory_name, executed_at
                    ) VALUES (
                        %(host_id)s::uuid, %(job_id)s, %(job_name)s,
                        %(ok)s, %(changed)s, %(failures)s, %(dark)s, %(skipped)s,
                        %(project)s, %(org_name)s, %(inventory_name)s, %(executed_at)s
                    )
                    ON CONFLICT (aap_host_id, job_id) DO UPDATE SET
                        job_name = EXCLUDED.job_name,
                        ok = EXCLUDED.ok,
                        changed = EXCLUDED.changed,
                        failures = EXCLUDED.failures,
                        dark = EXCLUDED.dark,
                        skipped = EXCLUDED.skipped
                    """,
                    {
                        "host_id": db_host_id,
                        "job_id": job_id,
                        "job_name": job_name,
                        "ok": int(row.get("ok", 0) or 0),
                        "changed": int(row.get("changed", 0) or 0),
                        "failures": int(row.get("failures", 0) or 0),
                        "dark": int(row.get("dark", 0) or 0),
                        "skipped": int(row.get("skipped", 0) or 0),
                        "project": row.get("project") or row.get("job__project__name"),
                        "org_name": row.get("org_name") or row.get("host__organization__name"),
                        "inventory_name": row.get("inventory_name") or row.get("job__inventory__name"),
                        "executed_at": executed_at,
                    },
                )
                stats["jobs_imported"] += 1
            except Exception:
                logger.warning("Failed to insert job %s for host %s", job_id, host_id)

        # --- Update host aggregates ---
        await conn.execute(
            """
            UPDATE aap_host h SET
                total_jobs = sub.cnt,
                first_seen = sub.first_exec,
                last_seen = sub.last_exec,
                updated_at = now()
            FROM (
                SELECT aap_host_id,
                       COUNT(*) AS cnt,
                       MIN(executed_at) AS first_exec,
                       MAX(executed_at) AS last_exec
                FROM aap_job_execution
                GROUP BY aap_host_id
            ) sub
            WHERE h.id = sub.aap_host_id
            """
        )

        # --- Update event counts ---
        event_counts: dict[str, int] = {}
        for row in csvs.get("main_jobevent", []):
            hid = row.get("host_id") or ""
            if hid in host_id_map:
                event_counts[host_id_map[hid]] = event_counts.get(host_id_map[hid], 0) + 1

        for db_id, count in event_counts.items():
            await conn.execute(
                "UPDATE aap_host SET total_events = %(count)s, updated_at = now() WHERE id = %(id)s::uuid",
                {"count": count, "id": db_id},
            )

        await conn.commit()

    return stats
