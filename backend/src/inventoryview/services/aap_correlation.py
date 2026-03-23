"""AAP host-to-resource correlation service.

Implements a 6-tier cascading matching strategy to correlate AAP hosts
to inventory resources. Creates AAPHost graph nodes and AUTOMATED_BY edges.
"""

import json
import logging
from datetime import UTC, datetime

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from inventoryview.services.asset_correlation import _extract_hw_ids
from inventoryview.services.graph import execute_cypher

logger = logging.getLogger(__name__)

AUTO_MATCH_THRESHOLD = 80


async def correlate_hosts(
    pool: AsyncConnectionPool,
    graph_name: str,
    source_label: str,
) -> dict:
    """Run correlation for all pending AAP hosts.

    Returns summary: {auto_matched, pending_review, unmatched}.
    """
    now = datetime.now(UTC).isoformat()
    summary = {"auto_matched": 0, "pending_review": 0, "unmatched": 0}

    # Get all uncorrelated hosts
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        result = await conn.execute(
            """
            SELECT id, host_id, hostname, smbios_uuid, org_id, inventory_id,
                   correlation_type, canonical_facts
            FROM aap_host
            WHERE correlation_status = 'pending'
            """
        )
        hosts = await result.fetchall()

    if not hosts:
        return summary

    # Pre-fetch all resource data for matching
    async with pool.connection() as conn:
        resources = await _fetch_resources_for_matching(conn, graph_name)

    # Pre-fetch learned mappings
    learned = await _fetch_learned_mappings(pool)

    for host in hosts:
        # Ensure all string fields are proper str (psycopg may return memoryview/bytes)
        host = {
            k: (v.decode("utf-8") if isinstance(v, (bytes, memoryview)) else v)
            for k, v in host.items()
        }
        match = await _match_host(host, resources, learned)

        if match:
            resource_uid, score, reason = match

            if score >= AUTO_MATCH_THRESHOLD:
                # Auto-match: create graph edge and update host
                await _create_automation_link(
                    pool, graph_name, host, resource_uid, score, reason, now
                )
                summary["auto_matched"] += 1
            else:
                # Queue for review
                await _create_pending_match(
                    pool, host, resource_uid, score, reason
                )
                summary["pending_review"] += 1
        else:
            # No match found — create pending with no suggestion
            await _create_pending_match(pool, host, None, 0, "no_match")
            summary["unmatched"] += 1

    return summary


async def _fetch_resources_for_matching(conn, graph_name: str) -> list[dict]:
    """Fetch all resources with their identifiers for matching."""
    cypher = (
        " MATCH (r:Resource) "
        "RETURN r.uid AS uid, r.name AS name, r.vendor AS vendor, "
        "r.normalised_type AS ntype, r.raw_properties AS raw_props"
    )
    rows = await execute_cypher(
        conn, graph_name, cypher,
        columns="(uid agtype, name agtype, vendor agtype, ntype agtype, raw_props agtype)",
    )

    resources = []
    for row in rows:
        if isinstance(row, dict):
            raw = row.get("raw_props")
            hw_ids = _extract_hw_ids(raw) if raw else {}
            name_val = str(row.get("name", "")).strip('"')
            uid_val = str(row.get("uid", "")).strip('"')
            resources.append({
                "uid": uid_val,
                "name": name_val,
                "vendor": str(row.get("vendor", "")).strip('"'),
                "normalised_type": str(row.get("ntype", "")).strip('"'),
                "hw_ids": hw_ids,
                "name_lower": name_val.lower(),
            })

    logger.info("Fetched %d resources for AAP correlation matching", len(resources))

    return resources


async def _fetch_learned_mappings(pool: AsyncConnectionPool) -> dict[str, str]:
    """Fetch learned mappings as {hostname_lower: resource_uid}."""
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        result = await conn.execute(
            "SELECT hostname, resource_uid FROM aap_learned_mapping"
        )
        rows = await result.fetchall()

    def _to_str(v):
        if isinstance(v, (bytes, memoryview)):
            return bytes(v).decode("utf-8") if isinstance(v, memoryview) else v.decode("utf-8")
        return str(v) if v is not None else ""

    return {_to_str(row["hostname"]).lower(): _to_str(row["resource_uid"]) for row in rows}


async def _match_host(
    host: dict,
    resources: list[dict],
    learned: dict[str, str],
) -> tuple[str, int, str] | None:
    """Run 6-tier cascade matching for a single host.

    Returns (resource_uid, score, reason) or None.
    """
    hostname = str(host["hostname"]).lower().strip()
    smbios_uuid = str(host.get("smbios_uuid") or "").lower().strip()

    # Tier 1: Learned mapping
    if hostname in learned:
        return (learned[hostname], 100, "learned_mapping")

    # Tier 2: SMBIOS/machine_id UUID match
    if smbios_uuid:
        for res in resources:
            for _key, val in res["hw_ids"].items():
                if val == smbios_uuid:
                    return (res["uid"], 96, "smbios_match")

    # Tier 3: Exact hostname/FQDN match
    for res in resources:
        if res["name_lower"] == hostname:
            return (res["uid"], 95, "exact_hostname")

    # Tier 4: IP address match (check if hostname looks like an IP)
    # This is a simplified check; real implementation would query resource IPs
    if _looks_like_ip(hostname):
        for res in resources:
            if res["name_lower"] == hostname:
                return (res["uid"], 88, "ip_match")

    # Tier 5: Hostname prefix / FQDN short name
    short_name = hostname.split(".")[0] if "." in hostname else None
    if short_name:
        for res in resources:
            res_short = res["name_lower"].split(".")[0]
            if res_short == short_name:
                return (res["uid"], 65, "hostname_prefix")

    # Also check if a resource's name starts with the hostname
    for res in resources:
        if res["name_lower"].startswith(hostname + "."):
            return (res["uid"], 65, "hostname_prefix")
        if hostname.startswith(res["name_lower"] + "."):
            return (res["uid"], 65, "hostname_prefix")

    # Tier 6: Partial/fuzzy (basic substring match)
    for res in resources:
        if hostname in res["name_lower"] or res["name_lower"] in hostname:
            if len(hostname) > 3 and len(res["name_lower"]) > 3:
                return (res["uid"], 35, "partial_match")

    return None


def _looks_like_ip(s: str) -> bool:
    """Quick check if a string looks like an IPv4 address."""
    parts = s.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


async def _create_automation_link(
    pool: AsyncConnectionPool,
    graph_name: str,
    host: dict,
    resource_uid: str,
    score: int,
    reason: str,
    now: str,
):
    """Create AAPHost graph node + AUTOMATED_BY edge + update relational host."""
    host_id = host["host_id"]
    hostname = host["hostname"]
    smbios_uuid = host.get("smbios_uuid") or ""
    org_id = host["org_id"]
    inventory_id = host["inventory_id"]
    ctype = host.get("correlation_type", "direct")
    confidence = score / 100.0

    # Escape for Cypher
    def esc(s):
        return str(s).replace("'", "\\'").replace("\\", "\\\\")

    async with pool.connection() as conn:
        # Check if AAPHost node exists
        check_node = (
            f" MATCH (a:AAPHost {{host_id: '{esc(host_id)}', org_id: '{esc(org_id)}'}}) "
            f"RETURN a"
        )
        existing_node = await execute_cypher(conn, graph_name, check_node)

        if existing_node:
            # Update existing node
            update_node = (
                f" MATCH (a:AAPHost {{host_id: '{esc(host_id)}', org_id: '{esc(org_id)}'}}) "
                f"SET a.hostname = '{esc(hostname)}', "
                f"a.last_seen = '{now}' "
                f"RETURN a"
            )
            await execute_cypher(conn, graph_name, update_node)
        else:
            # Create new node
            create_node = (
                f" CREATE (a:AAPHost {{"
                f"host_id: '{esc(host_id)}', "
                f"org_id: '{esc(org_id)}', "
                f"hostname: '{esc(hostname)}', "
                f"smbios_uuid: '{esc(smbios_uuid)}', "
                f"inventory_id: '{esc(inventory_id)}', "
                f"correlation_type: '{esc(ctype)}', "
                f"total_jobs: 0, total_events: 0, "
                f"first_seen: '{now}', last_seen: '{now}', "
                f"import_source: 'aap_metrics_import'"
                f"}}) RETURN a"
            )
            await execute_cypher(conn, graph_name, create_node)

        # Create AUTOMATED_BY edge (check if exists first)
        check_edge = (
            f" MATCH (a:AAPHost {{host_id: '{esc(host_id)}', org_id: '{esc(org_id)}'}})"
            f"-[r:AUTOMATED_BY]->"
            f"(res:Resource {{uid: '{esc(resource_uid)}'}}) "
            f"RETURN r"
        )
        existing = await execute_cypher(conn, graph_name, check_edge)

        if not existing:
            correlation_key = f"smbios:{smbios_uuid}" if reason == "smbios_match" else f"hostname:{hostname}"
            create_edge = (
                f" MATCH (a:AAPHost {{host_id: '{esc(host_id)}', org_id: '{esc(org_id)}'}}), "
                f"(res:Resource {{uid: '{esc(resource_uid)}'}}) "
                f"CREATE (a)-[r:AUTOMATED_BY {{"
                f"confidence: {confidence}, "
                f"correlation_key: '{esc(correlation_key)}', "
                f"correlation_type: '{esc(ctype)}', "
                f"inference_method: '{esc(reason)}', "
                f"source_collector: 'aap_metrics_import', "
                f"established_at: '{now}', "
                f"last_confirmed: '{now}'"
                f"}}]->(res) "
                f"RETURN r"
            )
            await execute_cypher(conn, graph_name, create_edge)

    # Update relational host record
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE aap_host SET
                correlated_resource_uid = %(uid)s::uuid,
                correlation_status = 'auto_matched',
                match_score = %(score)s,
                match_reason = %(reason)s,
                updated_at = now()
            WHERE id = %(id)s::uuid
            """,
            {"uid": resource_uid, "score": score, "reason": reason, "id": str(host["id"])},
        )
        await conn.commit()


async def _create_pending_match(
    pool: AsyncConnectionPool,
    host: dict,
    resource_uid: str | None,
    score: int,
    reason: str,
):
    """Create a pending match record for admin review."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO aap_pending_match (
                aap_host_id, suggested_resource_uid, match_score, match_reason
            ) VALUES (
                %(host_id)s::uuid, %(resource_uid)s, %(score)s, %(reason)s
            )
            ON CONFLICT DO NOTHING
            """,
            {
                "host_id": str(host["id"]),
                "resource_uid": resource_uid,
                "score": score,
                "reason": reason,
            },
        )
        await conn.commit()


async def process_review_actions(
    pool: AsyncConnectionPool,
    graph_name: str,
    actions: list,
    admin_id: str | None,
) -> list[dict]:
    """Process bulk review actions (approve/reject/ignore)."""
    now = datetime.now(UTC).isoformat()
    results = []

    for action in actions:
        pm_id = str(action.pending_match_id)
        act = action.action
        override_uid = str(action.override_resource_uid) if action.override_resource_uid else None

        try:
            async with pool.connection() as conn:
                conn.row_factory = dict_row
                # Fetch the pending match
                result = await conn.execute(
                    """
                    SELECT pm.*, h.host_id AS h_host_id, h.hostname AS h_hostname,
                           h.smbios_uuid AS h_smbios, h.org_id AS h_org_id,
                           h.inventory_id AS h_inv_id, h.correlation_type AS h_ctype
                    FROM aap_pending_match pm
                    JOIN aap_host h ON pm.aap_host_id = h.id
                    WHERE pm.id = %(id)s::uuid AND pm.status = 'pending'
                    """,
                    {"id": pm_id},
                )
                pm_row = await result.fetchone()

                if not pm_row:
                    results.append({
                        "pending_match_id": pm_id,
                        "action": act,
                        "success": False,
                        "error": "Pending match not found or already reviewed",
                    })
                    continue

                if act == "approve":
                    resource_uid = override_uid or str(pm_row["suggested_resource_uid"] or "")
                    if not resource_uid:
                        results.append({
                            "pending_match_id": pm_id,
                            "action": act,
                            "success": False,
                            "error": "No resource UID to approve",
                        })
                        continue

                    # Update pending match
                    await conn.execute(
                        """
                        UPDATE aap_pending_match SET
                            status = 'approved',
                            reviewed_by = %(admin)s,
                            reviewed_at = now(),
                            override_resource_uid = %(override)s
                        WHERE id = %(id)s::uuid
                        """,
                        {"id": pm_id, "admin": admin_id, "override": override_uid},
                    )

                    # Update host
                    await conn.execute(
                        """
                        UPDATE aap_host SET
                            correlated_resource_uid = %(uid)s::uuid,
                            correlation_status = 'manual_matched',
                            match_score = %(score)s,
                            match_reason = 'manual_approval',
                            updated_at = now()
                        WHERE id = %(host_id)s::uuid
                        """,
                        {"uid": resource_uid, "score": pm_row["match_score"], "host_id": str(pm_row["aap_host_id"])},
                    )

                    # Create learned mapping
                    await conn.execute(
                        """
                        INSERT INTO aap_learned_mapping (
                            hostname, resource_uid, org_id, source_label, created_by
                        ) VALUES (
                            %(hostname)s, %(uid)s::uuid, %(org_id)s, %(source)s, %(admin)s
                        )
                        ON CONFLICT (hostname, org_id, source_label) DO UPDATE SET
                            resource_uid = EXCLUDED.resource_uid,
                            created_by = EXCLUDED.created_by
                        """,
                        {
                            "hostname": pm_row["h_hostname"],
                            "uid": resource_uid,
                            "org_id": pm_row["h_org_id"],
                            "source": "manual_review",
                            "admin": admin_id,
                        },
                    )

                    await conn.commit()

                    # Create graph link
                    host_data = {
                        "id": pm_row["aap_host_id"],
                        "host_id": pm_row["h_host_id"],
                        "hostname": pm_row["h_hostname"],
                        "smbios_uuid": pm_row.get("h_smbios"),
                        "org_id": pm_row["h_org_id"],
                        "inventory_id": pm_row["h_inv_id"],
                        "correlation_type": pm_row.get("h_ctype", "direct"),
                    }
                    await _create_automation_link(
                        pool, graph_name, host_data, resource_uid,
                        pm_row["match_score"], "manual_approval", now,
                    )

                    results.append({
                        "pending_match_id": pm_id,
                        "action": act,
                        "success": True,
                        "learned_mapping_created": True,
                    })

                elif act == "reject":
                    await conn.execute(
                        """
                        UPDATE aap_pending_match SET
                            status = 'rejected', reviewed_by = %(admin)s, reviewed_at = now()
                        WHERE id = %(id)s::uuid
                        """,
                        {"id": pm_id, "admin": admin_id},
                    )
                    await conn.execute(
                        """
                        UPDATE aap_host SET
                            correlation_status = 'rejected', updated_at = now()
                        WHERE id = %(host_id)s::uuid
                        """,
                        {"host_id": str(pm_row["aap_host_id"])},
                    )
                    await conn.commit()

                    results.append({
                        "pending_match_id": pm_id,
                        "action": act,
                        "success": True,
                    })

                elif act == "ignore":
                    await conn.execute(
                        """
                        UPDATE aap_pending_match SET
                            status = 'ignored', reviewed_by = %(admin)s, reviewed_at = now()
                        WHERE id = %(id)s::uuid
                        """,
                        {"id": pm_id, "admin": admin_id},
                    )
                    await conn.commit()

                    results.append({
                        "pending_match_id": pm_id,
                        "action": act,
                        "success": True,
                    })

        except Exception as e:
            logger.exception("Error processing review action for %s", pm_id)
            results.append({
                "pending_match_id": pm_id,
                "action": act,
                "success": False,
                "error": str(e),
            })

    return results
