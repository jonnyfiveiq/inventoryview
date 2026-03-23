"""AAP automation coverage reporting service."""

import csv
import io
import logging
from datetime import UTC, datetime

from fastapi.responses import StreamingResponse
from psycopg_pool import AsyncConnectionPool

from inventoryview.services.graph import execute_cypher

logger = logging.getLogger(__name__)


async def get_coverage_stats(
    pool: AsyncConnectionPool,
    graph_name: str,
) -> dict:
    """Get automation coverage statistics for the dashboard."""
    async with pool.connection() as conn:
        # Total resources from graph
        total_cypher = " MATCH (r:Resource) RETURN COUNT(r) AS cnt"
        total_rows = await execute_cypher(conn, graph_name, total_cypher)
        total_resources = int(total_rows[0]) if total_rows else 0

        # Automated resources (distinct resources with AUTOMATED_BY edges)
        auto_cypher = (
            " MATCH (a:AAPHost)-[:AUTOMATED_BY]->(r:Resource) "
            "RETURN COUNT(DISTINCT r.uid) AS cnt"
        )
        auto_rows = await execute_cypher(conn, graph_name, auto_cypher)
        automated_resources = int(auto_rows[0]) if auto_rows else 0

        # Per-vendor breakdown
        vendor_cypher = (
            " MATCH (r:Resource) "
            "RETURN r.vendor AS vendor, COUNT(r) AS total"
        )
        vendor_rows = await execute_cypher(
            conn, graph_name, vendor_cypher,
            columns="(vendor agtype, total agtype)",
        )

        auto_vendor_cypher = (
            " MATCH (a:AAPHost)-[:AUTOMATED_BY]->(r:Resource) "
            "RETURN r.vendor AS vendor, COUNT(DISTINCT r.uid) AS automated"
        )
        auto_vendor_rows = await execute_cypher(
            conn, graph_name, auto_vendor_cypher,
            columns="(vendor agtype, automated agtype)",
        )

    # Build vendor map
    vendor_totals: dict[str, int] = {}
    for row in vendor_rows:
        if isinstance(row, dict):
            v = str(row.get("vendor", ""))
            vendor_totals[v] = int(row.get("total", 0))

    vendor_automated: dict[str, int] = {}
    for row in auto_vendor_rows:
        if isinstance(row, dict):
            v = str(row.get("vendor", ""))
            vendor_automated[v] = int(row.get("automated", 0))

    by_provider = []
    for vendor, total in sorted(vendor_totals.items()):
        auto = vendor_automated.get(vendor, 0)
        pct = (auto / total * 100) if total > 0 else 0.0
        by_provider.append({
            "vendor": vendor,
            "total": total,
            "automated": auto,
            "coverage_percentage": round(pct, 1),
        })

    # Top automated resources
    async with pool.connection() as conn:
        top_result = await conn.execute(
            """
            SELECT h.correlated_resource_uid, SUM(h.total_jobs) AS total_jobs,
                   MAX(h.last_seen) AS last_automated
            FROM aap_host h
            WHERE h.correlation_status IN ('auto_matched', 'manual_matched')
              AND h.correlated_resource_uid IS NOT NULL
            GROUP BY h.correlated_resource_uid
            ORDER BY total_jobs DESC
            LIMIT 10
            """
        )
        top_rows = await top_result.fetchall()

    top_automated = []
    for row in top_rows:
        uid = str(row["correlated_resource_uid"])
        # Get resource name from graph
        try:
            async with pool.connection() as conn:
                cypher = f" MATCH (r:Resource {{uid: '{uid}'}}) RETURN r.name AS name, r.vendor AS vendor"
                res = await execute_cypher(
                    conn, graph_name, cypher,
                    columns="(name agtype, vendor agtype)",
                )
                if res and isinstance(res[0], dict):
                    top_automated.append({
                        "resource_uid": uid,
                        "resource_name": str(res[0].get("name", "")),
                        "vendor": str(res[0].get("vendor", "")),
                        "total_jobs": row["total_jobs"],
                        "last_automated": row["last_automated"],
                    })
        except Exception:
            pass

    # Recent imports
    async with pool.connection() as conn:
        imports_result = await conn.execute(
            """
            SELECT import_source, MAX(created_at) AS imported_at, COUNT(*) AS hosts_count
            FROM aap_host
            GROUP BY import_source
            ORDER BY imported_at DESC
            LIMIT 5
            """
        )
        import_rows = await imports_result.fetchall()

    recent_imports = [
        {
            "source_label": row["import_source"],
            "imported_at": row["imported_at"],
            "hosts_count": row["hosts_count"],
        }
        for row in import_rows
    ]

    coverage_pct = (automated_resources / total_resources * 100) if total_resources > 0 else 0.0

    return {
        "total_resources": total_resources,
        "automated_resources": automated_resources,
        "coverage_percentage": round(coverage_pct, 1),
        "by_provider": by_provider,
        "top_automated": top_automated,
        "recent_imports": recent_imports,
    }


async def generate_coverage_report(
    pool: AsyncConnectionPool,
    graph_name: str,
    format: str = "json",
    vendor_filter: str | None = None,
):
    """Generate a full coverage report. Returns JSON or CSV."""
    now = datetime.now(UTC)

    # Get all resources
    async with pool.connection() as conn:
        vendor_clause = ""
        if vendor_filter:
            vendor_clause = f"WHERE r.vendor = '{vendor_filter}'"
        all_cypher = (
            f" MATCH (r:Resource) {vendor_clause} "
            f"RETURN r.uid AS uid, r.name AS name, r.vendor AS vendor, r.normalised_type AS ntype"
        )
        all_rows = await execute_cypher(
            conn, graph_name, all_cypher,
            columns="(uid agtype, name agtype, vendor agtype, ntype agtype)",
        )

    all_resources = {}
    for row in all_rows:
        if isinstance(row, dict):
            uid = str(row.get("uid", ""))
            all_resources[uid] = {
                "uid": uid,
                "name": str(row.get("name", "")),
                "vendor": str(row.get("vendor", "")),
                "normalised_type": str(row.get("ntype", "")),
            }

    # Get automated resources (deduplicated by resource uid)
    async with pool.connection() as conn:
        result = await conn.execute(
            """
            SELECT h.correlated_resource_uid,
                   MIN(h.first_seen) AS first_automated,
                   MAX(h.last_seen) AS last_automated,
                   SUM(h.total_jobs) AS total_jobs,
                   ARRAY_AGG(DISTINCT h.hostname) AS hostnames
            FROM aap_host h
            WHERE h.correlation_status IN ('auto_matched', 'manual_matched')
              AND h.correlated_resource_uid IS NOT NULL
            GROUP BY h.correlated_resource_uid
            """
        )
        auto_rows = await result.fetchall()

    automated_uids = set()
    automated_list = []
    for row in auto_rows:
        uid = str(row["correlated_resource_uid"])
        res_info = all_resources.get(uid)
        if not res_info:
            continue
        if vendor_filter and res_info["vendor"] != vendor_filter:
            continue
        automated_uids.add(uid)
        automated_list.append({
            "resource_uid": uid,
            "resource_name": res_info["name"],
            "vendor": res_info["vendor"],
            "normalised_type": res_info["normalised_type"],
            "first_automated": row["first_automated"],
            "last_automated": row["last_automated"],
            "total_jobs": row["total_jobs"],
            "aap_hostnames": row["hostnames"] or [],
        })

    unautomated_list = [
        {
            "resource_uid": info["uid"],
            "resource_name": info["name"],
            "vendor": info["vendor"],
            "normalised_type": info["normalised_type"],
        }
        for uid, info in all_resources.items()
        if uid not in automated_uids
    ]

    total = len(all_resources)
    auto_count = len(automated_uids)
    pct = (auto_count / total * 100) if total > 0 else 0.0

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "resource_uid", "resource_name", "vendor", "normalised_type",
            "first_automated", "last_automated", "total_jobs", "aap_hostnames", "status",
        ])
        for item in automated_list:
            writer.writerow([
                item["resource_uid"], item["resource_name"], item["vendor"],
                item["normalised_type"], item["first_automated"], item["last_automated"],
                item["total_jobs"], "; ".join(item["aap_hostnames"]), "automated",
            ])
        for item in unautomated_list:
            writer.writerow([
                item["resource_uid"], item["resource_name"], item["vendor"],
                item["normalised_type"], "", "", 0, "", "unautomated",
            ])

        date_str = now.strftime("%Y-%m-%d")
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=automation-coverage-{date_str}.csv"},
        )

    return {
        "generated_at": now,
        "summary": {
            "total_resources": total,
            "automated_resources": auto_count,
            "coverage_percentage": round(pct, 1),
            "deduplicated_note": "Multiple AAP hostnames resolving to the same resource are counted once",
        },
        "automated": automated_list,
        "unautomated": unautomated_list,
    }
