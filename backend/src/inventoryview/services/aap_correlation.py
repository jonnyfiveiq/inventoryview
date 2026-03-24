"""AAP host-to-resource correlation service.

Implements a 6-tier cascading matching strategy with confidence scoring
(0.0-1.0), multi-tier reinforcement boost, exclusion rules, ambiguity
detection, audit logging, and background job progress tracking.

Tiers (ordered by confidence):
  1. SMBIOS Serial  → 1.00
  2. BIOS UUID       → 0.95
  3. MAC Address      → 0.85
  4. IP Address       → 0.75
  5. FQDN             → 0.50
  6. Hostname Heuristic → 0.30
  0. Learned Mapping  → 1.00 (checked first)
"""

import json
import logging
import uuid
from datetime import UTC, datetime

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from inventoryview.models.automation import CorrelationTier
from inventoryview.services.asset_correlation import _extract_hw_ids
from inventoryview.services.graph import execute_cypher

logger = logging.getLogger(__name__)

# Matches at or above this threshold are auto-matched; below go to reconciliation.
AUTO_MATCH_THRESHOLD = 0.50

# Multi-tier reinforcement boost: max(confidences) + BOOST_PER_ADDITIONAL * extra_tiers
BOOST_PER_ADDITIONAL = 0.15


# ── Fact extraction ─────────────────────────────────────────────────────

def extract_ansible_facts(host_row: dict) -> dict:
    """Extract structured identifiers from a host's ansible_facts JSONB."""
    facts = host_row.get("ansible_facts") or {}
    if isinstance(facts, str):
        try:
            facts = json.loads(facts)
        except (json.JSONDecodeError, ValueError):
            facts = {}

    serial = str(facts.get("ansible_product_serial", "") or "").strip().lower()
    product_uuid = str(facts.get("ansible_product_uuid", "") or "").strip().lower()

    # MAC addresses
    macs: list[str] = []
    default_ipv4 = facts.get("ansible_default_ipv4") or {}
    if isinstance(default_ipv4, dict):
        mac = default_ipv4.get("macaddress", "")
        if mac:
            macs.append(_normalise_mac(mac))
    for iface_name, iface_data in (facts.get("ansible_interfaces_details") or {}).items():
        if isinstance(iface_data, dict):
            mac = iface_data.get("macaddress", "")
            if mac:
                macs.append(_normalise_mac(mac))

    # IP addresses
    ips: list[str] = []
    for ip in (facts.get("ansible_all_ipv4_addresses") or []):
        if isinstance(ip, str) and ip.strip():
            ips.append(ip.strip())
    if isinstance(default_ipv4, dict):
        addr = default_ipv4.get("address", "")
        if addr and addr not in ips:
            ips.append(addr.strip())

    fqdn = str(facts.get("ansible_fqdn", "") or "").strip().lower()
    hostname = str(facts.get("ansible_hostname", "") or "").strip().lower()

    return {
        "serial": serial,
        "product_uuid": product_uuid,
        "macs": [m for m in macs if m],
        "ips": [ip for ip in ips if ip],
        "fqdn": fqdn,
        "hostname": hostname,
    }


def extract_resource_identifiers(resource: dict) -> dict:
    """Extract all matchable identifiers from a resource node.

    Searches raw_properties across vSphere, AWS, Azure naming conventions.
    """
    hw_ids = resource.get("hw_ids") or {}
    raw = resource.get("raw_props_parsed") or {}

    serials: list[str] = []
    for key in ("serial_number", "system_serial", "baseboard_serial", "serialNumber"):
        val = raw.get(key) or hw_ids.get(key, "")
        if val:
            serials.append(str(val).strip().lower())

    uuids: list[str] = []
    for key in ("smbios_uuid", "system_uuid", "bios_uuid", "dmi_uuid",
                "config.uuid", "instanceId"):
        val = raw.get(key) or hw_ids.get(key, "")
        if val:
            uuids.append(str(val).strip().lower())

    macs: list[str] = []
    for key in ("macAddress", "mac_address", "primaryMac"):
        val = raw.get(key, "")
        if val:
            macs.append(_normalise_mac(str(val)))
    # vSphere nested NICs
    for nic in (raw.get("guest", {}) or {}).get("net", []) or []:
        if isinstance(nic, dict):
            mac = nic.get("macAddress", "")
            if mac:
                macs.append(_normalise_mac(mac))

    ips: list[str] = []
    for key in ("ipAddress", "ip_address", "privateIpAddress", "publicIpAddress"):
        val = raw.get(key, "")
        if val and isinstance(val, str):
            ips.append(val.strip())
    # vSphere guest IPs
    for nic in (raw.get("guest", {}) or {}).get("net", []) or []:
        if isinstance(nic, dict):
            for ip_entry in nic.get("ipAddress", []) or []:
                if isinstance(ip_entry, str) and "." in ip_entry:
                    ips.append(ip_entry.strip())

    fqdn = str(raw.get("fqdn", "") or raw.get("dnsName", "") or "").strip().lower()

    return {
        "serials": [s for s in serials if s],
        "uuids": [u for u in uuids if u],
        "macs": [m for m in macs if m],
        "ips": [ip for ip in ips if ip],
        "fqdn": fqdn,
        "name": resource.get("name", "").strip().lower(),
    }


def _normalise_mac(mac: str) -> str:
    """Normalise MAC address to lowercase colon-separated."""
    mac = mac.strip().lower().replace("-", ":").replace(".", ":")
    # Handle Cisco-style xxxx.xxxx.xxxx
    parts = mac.split(":")
    if len(parts) == 3 and all(len(p) == 4 for p in parts):
        hex_str = "".join(parts)
        return ":".join(hex_str[i : i + 2] for i in range(0, 12, 2))
    return mac


# ── Tier matchers ────────────────────────────────────────────────────────

def _match_smbios_serial(host_facts: dict, res_ids: dict) -> dict | None:
    """Tier 1: SMBIOS serial number match."""
    serial = host_facts.get("serial", "")
    if not serial:
        return None
    for rs in res_ids.get("serials", []):
        if rs == serial:
            return {
                "confidence": 1.0,
                "tier": CorrelationTier.SMBIOS_SERIAL,
                "matched_fields": [{
                    "ansible_field": "ansible_product_serial",
                    "resource_field": "raw_properties.serialNumber",
                    "values": [serial, rs],
                }],
            }
    return None


def _match_bios_uuid(host_facts: dict, res_ids: dict) -> dict | None:
    """Tier 2: BIOS UUID match."""
    puuid = host_facts.get("product_uuid", "")
    if not puuid:
        return None
    for ru in res_ids.get("uuids", []):
        if ru == puuid:
            return {
                "confidence": 0.95,
                "tier": CorrelationTier.BIOS_UUID,
                "matched_fields": [{
                    "ansible_field": "ansible_product_uuid",
                    "resource_field": "raw_properties.bios_uuid",
                    "values": [puuid, ru],
                }],
            }
    return None


def _match_mac_address(host_facts: dict, res_ids: dict) -> dict | None:
    """Tier 3: MAC address match."""
    for hmac in host_facts.get("macs", []):
        for rmac in res_ids.get("macs", []):
            if hmac == rmac:
                return {
                    "confidence": 0.85,
                    "tier": CorrelationTier.MAC_ADDRESS,
                    "matched_fields": [{
                        "ansible_field": "ansible_default_ipv4.macaddress",
                        "resource_field": "raw_properties.macAddress",
                        "values": [hmac, rmac],
                    }],
                }
    return None


def _match_ip_address(host_facts: dict, res_ids: dict) -> dict | None:
    """Tier 4: IP address match."""
    for hip in host_facts.get("ips", []):
        for rip in res_ids.get("ips", []):
            if hip == rip:
                return {
                    "confidence": 0.75,
                    "tier": CorrelationTier.IP_ADDRESS,
                    "matched_fields": [{
                        "ansible_field": "ansible_all_ipv4_addresses",
                        "resource_field": "raw_properties.ipAddress",
                        "values": [hip, rip],
                    }],
                }
    return None


def _match_fqdn(host_facts: dict, res_ids: dict) -> dict | None:
    """Tier 5: FQDN match."""
    fqdn = host_facts.get("fqdn", "")
    if not fqdn:
        return None
    res_fqdn = res_ids.get("fqdn", "")
    if res_fqdn and res_fqdn == fqdn:
        return {
            "confidence": 0.50,
            "tier": CorrelationTier.FQDN,
            "matched_fields": [{
                "ansible_field": "ansible_fqdn",
                "resource_field": "fqdn",
                "values": [fqdn, res_fqdn],
            }],
        }
    return None


def _match_hostname_heuristic(host_facts: dict, res_ids: dict, host_hostname: str) -> dict | None:
    """Tier 6: Hostname heuristic (stripped short name comparison)."""
    # Use ansible_hostname if available, otherwise strip domain from host hostname
    ansible_hn = host_facts.get("hostname", "") or host_hostname.lower().split(".")[0]
    if not ansible_hn:
        return None

    res_name = res_ids.get("name", "")
    if not res_name:
        return None

    res_short = res_name.split(".")[0]
    ansible_short = ansible_hn.split(".")[0]

    if res_short and ansible_short and res_short == ansible_short:
        return {
            "confidence": 0.30,
            "tier": CorrelationTier.HOSTNAME_HEURISTIC,
            "matched_fields": [{
                "ansible_field": "ansible_hostname",
                "resource_field": "name",
                "values": [ansible_hn, res_name],
            }],
        }
    return None


# ── Boost formula ────────────────────────────────────────────────────────

# Tier base confidences for capping
_TIER_BASES = [1.0, 0.95, 0.85, 0.75, 0.50, 0.30]


def _calculate_boosted_confidence(matches: list[dict]) -> dict:
    """Apply multi-tier reinforcement boost.

    Formula: max(confidences) + 0.15 * count(additional_matches)
    Capped at next-higher tier base confidence.
    """
    if not matches:
        raise ValueError("No matches to boost")
    if len(matches) == 1:
        return matches[0]

    # Sort by confidence descending
    sorted_matches = sorted(matches, key=lambda m: m["confidence"], reverse=True)
    best = sorted_matches[0]
    additional = len(sorted_matches) - 1

    boosted = best["confidence"] + BOOST_PER_ADDITIONAL * additional

    # Cap at next higher tier
    base = best["confidence"]
    higher_bases = [b for b in _TIER_BASES if b > base]
    if higher_bases:
        cap = min(higher_bases)
        boosted = min(boosted, cap)
    else:
        boosted = min(boosted, 1.0)

    # Merge matched_fields from all tiers
    all_fields = []
    for m in sorted_matches:
        all_fields.extend(m.get("matched_fields", []))

    return {
        "confidence": round(boosted, 4),
        "tier": best["tier"],
        "matched_fields": all_fields,
    }


# ── Localhost filter ─────────────────────────────────────────────────────

_LOCALHOST_NAMES = {"localhost", "127.0.0.1", "::1", "localhost.localdomain"}


def _is_localhost(host_row: dict) -> bool:
    """Check if a host is localhost (should be excluded from correlation)."""
    hostname = str(host_row.get("hostname", "")).lower().strip()
    if hostname in _LOCALHOST_NAMES:
        return True
    facts = host_row.get("ansible_facts") or {}
    if isinstance(facts, str):
        try:
            facts = json.loads(facts)
        except Exception:
            facts = {}
    if isinstance(facts, dict):
        conn_type = str(facts.get("ansible_connection", "")).lower()
        if conn_type == "local":
            return True
    return False


# ── Exclusion check ──────────────────────────────────────────────────────

async def _check_exclusions(
    pool: AsyncConnectionPool,
    aap_host_id: str,
    candidate_uids: list[str],
) -> set[str]:
    """Return resource UIDs that are excluded for this host."""
    if not candidate_uids:
        return set()
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        placeholders = ", ".join(f"'{uid}'::uuid" for uid in candidate_uids)
        result = await conn.execute(
            f"""
            SELECT resource_uid FROM correlation_exclusion
            WHERE aap_host_id = %(host_id)s::uuid
              AND resource_uid IN ({placeholders})
            """,
            {"host_id": aap_host_id},
        )
        rows = await result.fetchall()
    return {str(row["resource_uid"]) for row in rows}


# ── Audit logging ────────────────────────────────────────────────────────

async def _log_audit(
    pool: AsyncConnectionPool,
    action: str,
    aap_host_id: str | None,
    resource_uid: str | None,
    tier: str | None = None,
    confidence: float | None = None,
    matched_fields: list | None = None,
    previous_state: dict | None = None,
    actor: str = "system",
) -> None:
    """Insert an audit log entry."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO correlation_audit (
                action, aap_host_id, resource_uid, tier, confidence,
                matched_fields, previous_state, actor
            ) VALUES (
                %(action)s,
                %(host_id)s::uuid,
                %(resource_uid)s::uuid,
                %(tier)s,
                %(confidence)s,
                %(matched_fields)s,
                %(previous_state)s,
                %(actor)s
            )
            """,
            {
                "action": action,
                "host_id": aap_host_id,
                "resource_uid": resource_uid,
                "tier": tier,
                "confidence": confidence,
                "matched_fields": json.dumps(matched_fields) if matched_fields else None,
                "previous_state": json.dumps(previous_state) if previous_state else None,
                "actor": actor,
            },
        )
        await conn.commit()


# ── Graph edge creation ──────────────────────────────────────────────────

def _esc(s) -> str:
    """Escape a string for Cypher embedding."""
    return str(s).replace("\\", "\\\\").replace("'", "\\'")


async def _upsert_automated_by_edge(
    pool: AsyncConnectionPool,
    graph_name: str,
    host: dict,
    resource_uid: str,
    confidence: float,
    tier: str,
    matched_fields: list,
    status: str = "proposed",
    confirmed_by: str | None = None,
) -> None:
    """Create or update an AUTOMATED_BY edge in the graph."""
    host_id = host["host_id"]
    hostname = host["hostname"]
    org_id = host["org_id"]
    now = datetime.now(UTC).isoformat()
    mf_json = json.dumps(matched_fields)

    async with pool.connection() as conn:
        # Ensure AAPHost node exists
        check_node = (
            f" MATCH (a:AAPHost {{host_id: '{_esc(host_id)}', org_id: '{_esc(org_id)}'}}) "
            f"RETURN a"
        )
        existing_node = await execute_cypher(conn, graph_name, check_node)

        if existing_node:
            update_node = (
                f" MATCH (a:AAPHost {{host_id: '{_esc(host_id)}', org_id: '{_esc(org_id)}'}}) "
                f"SET a.hostname = '{_esc(hostname)}', a.last_seen = '{now}' "
                f"RETURN a"
            )
            await execute_cypher(conn, graph_name, update_node)
        else:
            smbios_uuid = host.get("smbios_uuid") or ""
            inventory_id = host.get("inventory_id", "")
            ctype = host.get("correlation_type", "direct")
            create_node = (
                f" CREATE (a:AAPHost {{"
                f"host_id: '{_esc(host_id)}', "
                f"org_id: '{_esc(org_id)}', "
                f"hostname: '{_esc(hostname)}', "
                f"smbios_uuid: '{_esc(smbios_uuid)}', "
                f"inventory_id: '{_esc(inventory_id)}', "
                f"correlation_type: '{_esc(ctype)}', "
                f"total_jobs: 0, total_events: 0, "
                f"first_seen: '{now}', last_seen: '{now}', "
                f"import_source: 'aap_metrics_import'"
                f"}}) RETURN a"
            )
            await execute_cypher(conn, graph_name, create_node)

        # Check existing edge
        check_edge = (
            f" MATCH (a:AAPHost {{host_id: '{_esc(host_id)}', org_id: '{_esc(org_id)}'}})"
            f"-[r:AUTOMATED_BY]->"
            f"(res:Resource {{uid: '{_esc(resource_uid)}'}}) "
            f"RETURN r.confidence AS conf, r.tier AS tier, r.status AS st"
        )
        existing = await execute_cypher(
            conn, graph_name, check_edge,
            columns="(conf agtype, tier agtype, st agtype)",
        )

        cb_part = f", confirmed_by: '{_esc(confirmed_by)}'" if confirmed_by else ""

        if existing and isinstance(existing[0], dict):
            # Update existing edge
            update_edge = (
                f" MATCH (a:AAPHost {{host_id: '{_esc(host_id)}', org_id: '{_esc(org_id)}'}})"
                f"-[r:AUTOMATED_BY]->"
                f"(res:Resource {{uid: '{_esc(resource_uid)}'}}) "
                f"SET r.confidence = {confidence}, "
                f"r.tier = '{_esc(tier)}', "
                f"r.matched_fields = '{_esc(mf_json)}', "
                f"r.status = '{_esc(status)}', "
                f"r.updated_at = '{now}'"
                f"{(', r.confirmed_by = ' + chr(39) + _esc(confirmed_by) + chr(39)) if confirmed_by else ''} "
                f"RETURN r"
            )
            await execute_cypher(conn, graph_name, update_edge)
        else:
            # Create new edge
            create_edge = (
                f" MATCH (a:AAPHost {{host_id: '{_esc(host_id)}', org_id: '{_esc(org_id)}'}}), "
                f"(res:Resource {{uid: '{_esc(resource_uid)}'}}) "
                f"CREATE (a)-[r:AUTOMATED_BY {{"
                f"confidence: {confidence}, "
                f"tier: '{_esc(tier)}', "
                f"matched_fields: '{_esc(mf_json)}', "
                f"status: '{_esc(status)}', "
                f"correlation_key: '{_esc(tier)}:{_esc(host_id)}', "
                f"inference_method: '{_esc(tier)}', "
                f"source_collector: 'aap_metrics_import', "
                f"established_at: '{now}', "
                f"last_confirmed: '{now}', "
                f"created_at: '{now}', "
                f"updated_at: '{now}'"
                f"{cb_part}"
                f"}}]->(res) RETURN r"
            )
            await execute_cypher(conn, graph_name, create_edge)


# ── Core orchestrator ────────────────────────────────────────────────────

async def correlate_hosts(
    pool: AsyncConnectionPool,
    graph_name: str,
    source_label: str,
    *,
    job_id: str | None = None,
) -> dict:
    """Run correlation for all pending AAP hosts.

    Returns summary: {auto_matched, pending_review, unmatched}.
    """
    from inventoryview.services.correlation_jobs import (
        start_job,
        update_progress,
        complete_job,
        fail_job,
    )

    summary = {"auto_matched": 0, "pending_review": 0, "unmatched": 0}

    # Fetch uncorrelated hosts
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        result = await conn.execute(
            """
            SELECT id, host_id, hostname, smbios_uuid, org_id, inventory_id,
                   correlation_type, canonical_facts, ansible_facts
            FROM aap_host
            WHERE correlation_status = 'pending'
            """
        )
        hosts = await result.fetchall()

    if not hosts:
        if job_id:
            complete_job(job_id)
        return summary

    if job_id:
        start_job(job_id, total=len(hosts))

    # Pre-fetch resources
    async with pool.connection() as conn:
        resources = await _fetch_resources_for_matching(conn, graph_name)

    # Pre-fetch learned mappings
    learned = await _fetch_learned_mappings(pool)

    # Prepare resource identifiers once
    res_id_cache: list[tuple[dict, dict]] = []
    for res in resources:
        ids = extract_resource_identifiers(res)
        res_id_cache.append((res, ids))

    for idx, host in enumerate(hosts):
        # Normalise bytes/memoryview to str
        host = {
            k: (v.decode("utf-8") if isinstance(v, (bytes, memoryview)) else v)
            for k, v in host.items()
        }

        # Skip localhost
        if _is_localhost(host):
            if job_id:
                update_progress(job_id, progress=idx + 1)
            continue

        host_id_str = str(host["id"])
        hostname = str(host["hostname"]).lower().strip()

        # Check learned mapping first (Tier 0)
        if hostname in learned:
            resource_uid = learned[hostname]
            await _upsert_automated_by_edge(
                pool, graph_name, host, resource_uid,
                confidence=1.0,
                tier=CorrelationTier.LEARNED_MAPPING,
                matched_fields=[{
                    "ansible_field": "hostname",
                    "resource_field": "learned_mapping",
                    "values": [hostname, resource_uid],
                }],
                status="confirmed",
            )
            await _update_host_correlation(
                pool, host_id_str, resource_uid,
                1.0, CorrelationTier.LEARNED_MAPPING, "auto_matched",
            )
            await _log_audit(
                pool, "auto_match", host_id_str, resource_uid,
                tier=CorrelationTier.LEARNED_MAPPING, confidence=1.0,
            )
            summary["auto_matched"] += 1
            if job_id:
                update_progress(job_id, progress=idx + 1, matched_delta=1)
            continue

        # Extract ansible_facts
        host_facts = extract_ansible_facts(host)

        # Check exclusions for all candidate resources
        all_uids = [res["uid"] for res, _ in res_id_cache]
        excluded_uids = await _check_exclusions(pool, host_id_str, all_uids)

        # Run tier cascade across all resources
        tier_matchers = [
            _match_smbios_serial,
            _match_bios_uuid,
            _match_mac_address,
            _match_ip_address,
            _match_fqdn,
        ]

        # Collect best match per resource
        resource_matches: dict[str, list[dict]] = {}  # uid -> list of tier matches

        for res, res_ids in res_id_cache:
            uid = res["uid"]
            if uid in excluded_uids:
                continue

            matches_for_res: list[dict] = []
            for matcher in tier_matchers:
                m = matcher(host_facts, res_ids)
                if m:
                    matches_for_res.append(m)

            # Tier 6: hostname heuristic (needs host hostname)
            m = _match_hostname_heuristic(host_facts, res_ids, hostname)
            if m:
                matches_for_res.append(m)

            if matches_for_res:
                resource_matches[uid] = matches_for_res

        if not resource_matches:
            # No match found
            await _create_pending_match(pool, host, None, 0.0, "no_match")
            summary["unmatched"] += 1
            if job_id:
                update_progress(job_id, progress=idx + 1)
            continue

        # Apply boost per resource and find the best
        best_uid: str | None = None
        best_result: dict | None = None

        for uid, matches in resource_matches.items():
            boosted = _calculate_boosted_confidence(matches)
            if best_result is None or boosted["confidence"] > best_result["confidence"]:
                best_uid = uid
                best_result = boosted

        # Check for ambiguity: multiple resources at same tier
        if best_result:
            same_tier_uids = [
                uid for uid, matches in resource_matches.items()
                if _calculate_boosted_confidence(matches)["confidence"] == best_result["confidence"]
            ]
            if len(same_tier_uids) > 1:
                # Ambiguity — send all to reconciliation
                ambiguity_group = str(uuid.uuid4())
                for uid in same_tier_uids:
                    m = _calculate_boosted_confidence(resource_matches[uid])
                    await _create_pending_match(
                        pool, host, uid, m["confidence"],
                        f"Ambiguous: {m['tier']} match",
                        tier=m["tier"],
                        matched_fields=m["matched_fields"],
                        ambiguity_group_id=ambiguity_group,
                    )
                summary["pending_review"] += len(same_tier_uids)
                if job_id:
                    update_progress(job_id, progress=idx + 1, review_delta=len(same_tier_uids))
                continue

        # Single best match
        if best_uid and best_result:
            confidence = best_result["confidence"]
            tier = best_result["tier"]
            matched_fields = best_result["matched_fields"]

            if confidence >= AUTO_MATCH_THRESHOLD:
                # Auto-match
                status = "confirmed" if confidence >= 0.90 else "proposed"
                await _upsert_automated_by_edge(
                    pool, graph_name, host, best_uid,
                    confidence=confidence, tier=tier,
                    matched_fields=matched_fields, status=status,
                )
                await _update_host_correlation(
                    pool, host_id_str, best_uid, confidence, tier, "auto_matched",
                )
                await _log_audit(
                    pool, "auto_match", host_id_str, best_uid,
                    tier=tier, confidence=confidence, matched_fields=matched_fields,
                )
                summary["auto_matched"] += 1
                if job_id:
                    update_progress(job_id, progress=idx + 1, matched_delta=1)
            else:
                # Below threshold — reconciliation
                await _create_pending_match(
                    pool, host, best_uid, confidence,
                    f"{tier} match (confidence {confidence:.0%})",
                    tier=tier, matched_fields=matched_fields,
                )
                summary["pending_review"] += 1
                if job_id:
                    update_progress(job_id, progress=idx + 1, review_delta=1)

    if job_id:
        complete_job(job_id)

    return summary


# ── Re-correlate single resource ─────────────────────────────────────────

async def re_correlate_resource(
    pool: AsyncConnectionPool,
    graph_name: str,
    resource_uid: str,
    *,
    job_id: str | None = None,
) -> None:
    """Clear confirmed status and re-run correlation for one resource."""
    from inventoryview.services.correlation_jobs import start_job, complete_job, fail_job

    if job_id:
        start_job(job_id, total=1)

    # Clear confirmed status on existing edge
    async with pool.connection() as conn:
        cypher = (
            f" MATCH (a:AAPHost)-[r:AUTOMATED_BY]->(res:Resource {{uid: '{_esc(resource_uid)}'}}) "
            f"SET r.status = 'proposed', r.confirmed_by = '' "
            f"RETURN a.host_id AS host_id"
        )
        await execute_cypher(conn, graph_name, cypher)

    # Reset host correlation status
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE aap_host SET correlation_status = 'pending', updated_at = now()
            WHERE correlated_resource_uid = %(uid)s::uuid
            """,
            {"uid": resource_uid},
        )
        await conn.commit()

    # Run correlation for affected hosts
    await correlate_hosts(pool, graph_name, "re-correlate", job_id=job_id)


# ── Delta correlation ────────────────────────────────────────────────────

async def correlate_delta(
    pool: AsyncConnectionPool,
    graph_name: str,
    *,
    job_id: str | None = None,
) -> dict:
    """Run correlation only for resources with last_seen > last_correlated_at."""
    from inventoryview.services.correlation_jobs import start_job, complete_job

    # Find hosts that need re-correlation
    async with pool.connection() as conn:
        conn.row_factory = dict_row
        result = await conn.execute(
            """
            SELECT id FROM aap_host
            WHERE last_correlated_at IS NULL
               OR last_seen > last_correlated_at
            """
        )
        rows = await result.fetchall()

    if not rows:
        if job_id:
            start_job(job_id, total=0)
            complete_job(job_id)
        return {"auto_matched": 0, "pending_review": 0, "unmatched": 0}

    # Reset status to pending for delta hosts
    host_ids = [str(r["id"]) for r in rows]
    async with pool.connection() as conn:
        placeholders = ", ".join(f"'{hid}'::uuid" for hid in host_ids)
        await conn.execute(
            f"""
            UPDATE aap_host SET correlation_status = 'pending'
            WHERE id IN ({placeholders})
              AND correlation_status != 'pending'
            """
        )
        await conn.commit()

    return await correlate_hosts(pool, graph_name, "delta-correlation", job_id=job_id)


# ── Helper functions ─────────────────────────────────────────────────────

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

            # Parse raw_properties for resource identifier extraction
            raw_parsed = {}
            if raw:
                if isinstance(raw, str):
                    try:
                        raw_parsed = json.loads(raw.strip('"').replace('\\"', '"'))
                    except Exception:
                        raw_parsed = {}
                elif isinstance(raw, dict):
                    raw_parsed = raw

            name_val = str(row.get("name", "")).strip('"')
            uid_val = str(row.get("uid", "")).strip('"')
            resources.append({
                "uid": uid_val,
                "name": name_val,
                "vendor": str(row.get("vendor", "")).strip('"'),
                "normalised_type": str(row.get("ntype", "")).strip('"'),
                "hw_ids": hw_ids,
                "name_lower": name_val.lower(),
                "raw_props_parsed": raw_parsed,
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


async def _update_host_correlation(
    pool: AsyncConnectionPool,
    host_id: str,
    resource_uid: str,
    confidence: float,
    tier: str,
    status: str,
) -> None:
    """Update the relational host record after a match."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            UPDATE aap_host SET
                correlated_resource_uid = %(uid)s::uuid,
                correlation_status = %(status)s,
                correlation_type = %(tier)s,
                match_score = %(confidence)s,
                match_reason = %(tier)s,
                last_correlated_at = now(),
                updated_at = now()
            WHERE id = %(id)s::uuid
            """,
            {
                "uid": resource_uid,
                "status": status,
                "tier": tier,
                "confidence": confidence,
                "id": host_id,
            },
        )
        await conn.commit()


async def _create_pending_match(
    pool: AsyncConnectionPool,
    host: dict,
    resource_uid: str | None,
    score: float,
    reason: str,
    *,
    tier: str | None = None,
    matched_fields: list | None = None,
    ambiguity_group_id: str | None = None,
) -> None:
    """Create a pending match record for admin review."""
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO aap_pending_match (
                aap_host_id, suggested_resource_uid, match_score, match_reason,
                tier, matched_fields, ambiguity_group_id
            ) VALUES (
                %(host_id)s::uuid, %(resource_uid)s, %(score)s, %(reason)s,
                %(tier)s, %(matched_fields)s, %(ambiguity_group_id)s
            )
            ON CONFLICT DO NOTHING
            """,
            {
                "host_id": str(host["id"]),
                "resource_uid": resource_uid,
                "score": score,
                "reason": reason,
                "tier": tier,
                "matched_fields": json.dumps(matched_fields) if matched_fields else None,
                "ambiguity_group_id": ambiguity_group_id,
            },
        )
        await conn.commit()


# ── Review actions ───────────────────────────────────────────────────────

async def process_review_actions(
    pool: AsyncConnectionPool,
    graph_name: str,
    actions: list,
    admin_id: str | None,
) -> list[dict]:
    """Process bulk review actions (approve/confirm/reject/ignore/dismiss)."""
    now = datetime.now(UTC).isoformat()
    results = []

    for action in actions:
        pm_id = str(action.pending_match_id)
        act = action.action
        override_uid = str(action.override_resource_uid) if action.override_resource_uid else None
        reason = getattr(action, "reason", None)

        try:
            async with pool.connection() as conn:
                conn.row_factory = dict_row
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

                if act in ("approve", "confirm"):
                    resource_uid = override_uid or str(pm_row["suggested_resource_uid"] or "")
                    if not resource_uid:
                        results.append({
                            "pending_match_id": pm_id,
                            "action": act,
                            "success": False,
                            "error": "No resource UID to approve",
                        })
                        continue

                    await conn.execute(
                        """
                        UPDATE aap_pending_match SET
                            status = 'confirmed', reviewed_by = %(admin)s,
                            reviewed_at = now(), override_resource_uid = %(override)s
                        WHERE id = %(id)s::uuid
                        """,
                        {"id": pm_id, "admin": admin_id, "override": override_uid},
                    )

                    await conn.execute(
                        """
                        UPDATE aap_host SET
                            correlated_resource_uid = %(uid)s::uuid,
                            correlation_status = 'confirmed',
                            match_score = %(score)s,
                            match_reason = 'manual_approval',
                            updated_at = now()
                        WHERE id = %(host_id)s::uuid
                        """,
                        {
                            "uid": resource_uid,
                            "score": pm_row["match_score"],
                            "host_id": str(pm_row["aap_host_id"]),
                        },
                    )

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

                    host_data = {
                        "id": pm_row["aap_host_id"],
                        "host_id": pm_row["h_host_id"],
                        "hostname": pm_row["h_hostname"],
                        "smbios_uuid": pm_row.get("h_smbios"),
                        "org_id": pm_row["h_org_id"],
                        "inventory_id": pm_row["h_inv_id"],
                        "correlation_type": pm_row.get("h_ctype", "direct"),
                    }
                    await _upsert_automated_by_edge(
                        pool, graph_name, host_data, resource_uid,
                        confidence=pm_row["match_score"],
                        tier=pm_row.get("tier") or "manual",
                        matched_fields=pm_row.get("matched_fields") or [],
                        status="confirmed",
                        confirmed_by=str(admin_id) if admin_id else None,
                    )

                    await _log_audit(
                        pool, "confirm", str(pm_row["aap_host_id"]), resource_uid,
                        tier=pm_row.get("tier"), confidence=pm_row["match_score"],
                        actor=str(admin_id) if admin_id else "system",
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

                    # Create exclusion rule
                    resource_uid = str(pm_row["suggested_resource_uid"] or "")
                    if resource_uid:
                        await conn.execute(
                            """
                            INSERT INTO correlation_exclusion (
                                aap_host_id, resource_uid, created_by, reason
                            ) VALUES (
                                %(host_id)s::uuid, %(uid)s::uuid, %(admin)s, %(reason)s
                            )
                            ON CONFLICT (aap_host_id, resource_uid) DO NOTHING
                            """,
                            {
                                "host_id": str(pm_row["aap_host_id"]),
                                "uid": resource_uid,
                                "admin": str(admin_id) if admin_id else None,
                                "reason": reason,
                            },
                        )

                    await conn.commit()

                    await _log_audit(
                        pool, "reject", str(pm_row["aap_host_id"]), resource_uid,
                        actor=str(admin_id) if admin_id else "system",
                    )

                    results.append({
                        "pending_match_id": pm_id,
                        "action": act,
                        "success": True,
                    })

                elif act == "dismiss":
                    await conn.execute(
                        """
                        UPDATE aap_pending_match SET
                            status = 'dismissed', reviewed_by = %(admin)s, reviewed_at = now()
                        WHERE id = %(id)s::uuid
                        """,
                        {"id": pm_id, "admin": admin_id},
                    )
                    await conn.commit()

                    await _log_audit(
                        pool, "dismiss", str(pm_row["aap_host_id"]),
                        str(pm_row.get("suggested_resource_uid") or ""),
                        actor=str(admin_id) if admin_id else "system",
                    )

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
