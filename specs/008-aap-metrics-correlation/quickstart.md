# Quickstart: AAP Metrics Correlation Engine

**Feature Branch**: `008-aap-metrics-correlation`

## Integration Scenarios

### Scenario 1: Upload AAP Metrics and Monitor Correlation

```
1. POST /api/v1/automations/upload with AAP metrics archive
   → Receives 202 with correlation_job_id

2. Poll GET /api/v1/automations/correlation-jobs/{job_id}
   → Watch status progress: queued → running → completed
   → Progress shows matched/queued_for_review counts

3. GET /api/v1/automations/fleet-temperature
   → Check aggregate fleet correlation health
   → Verify weighted_average_confidence and tier_distribution
```

### Scenario 2: Hardware-Level Match (Tier 1 — Hot)

```
Precondition: Discovered vSphere VM with raw_properties containing
  serialNumber: "VMware-42-16-a8"

1. Upload AAP metrics with host facts:
   ansible_product_serial: "VMware-42-16-a8"

2. Correlation engine matches at Tier 1 (SMBIOS serial)
   → AUTOMATED_BY edge created: confidence=1.0, tier=smbios_serial

3. GET /api/v1/resources/{uid}/correlation
   → temperature: "hot", confidence: 1.0
   → No reconciliation queue entry (auto-matched)
```

### Scenario 3: Weak Match Sent to Reconciliation Queue

```
Precondition: Discovered VM named "john"

1. Upload AAP metrics with host ansible_hostname: "john.redhat.com"
   No matching serial, UUID, MAC, or IP.

2. Correlation engine matches at Tier 6 (hostname heuristic)
   → confidence=0.30, below threshold (0.50)
   → Entry created in reconciliation queue

3. GET /api/v1/automations/pending-matches?status=pending
   → Item shows tier: "hostname_heuristic", match_score: 0.30

4. POST /api/v1/automations/review
   → action: "confirm" → AUTOMATED_BY edge promoted, learned mapping saved
   OR
   → action: "reject" → exclusion rule created, pair never re-proposed
```

### Scenario 4: Multi-Tier Reinforcement Boost

```
Precondition: Discovered VM with IP 10.0.1.42 and name "webserver"

1. Upload AAP metrics with host facts:
   ansible_all_ipv4_addresses: ["10.0.1.42"]
   ansible_hostname: "webserver"

2. Correlation engine finds:
   - Tier 4 (IP) match: base confidence 0.75
   - Tier 6 (hostname) match: base confidence 0.30
   - Boosted: 0.75 + 0.15 = 0.90

3. AUTOMATED_BY edge created: confidence=0.90, tier=ip_address
   → Temperature: hot (≥0.90)
   → Auto-matched, no reconciliation needed
```

### Scenario 5: Ambiguous Match — One Host, Multiple Resources

```
Precondition: Two VMs both have BIOS UUID "abc-123-def" (cloned VMs)

1. Upload AAP metrics with host ansible_product_uuid: "abc-123-def"

2. Correlation engine detects one-to-many ambiguity
   → Both candidates placed in reconciliation queue
   → Same ambiguity_group_id links them

3. GET /api/v1/automations/pending-matches?ambiguity_group={id}
   → Returns both candidates for operator review

4. Operator confirms one, rejects the other
   → Confirmed resource gets AUTOMATED_BY edge
   → Rejected pair gets exclusion rule
```

### Scenario 6: Delta Correlation After Collection

```
Precondition: 5000 resources already correlated. New VMware collection adds 50 resources.

1. Collection completes → updates last_seen on 50 new/changed resources

2. System triggers delta correlation
   → Only processes 50 resources (where last_seen > last_correlated_at)
   → Not 5000 full re-scan

3. New matches created for any AAP hosts matching the 50 new resources
```

### Scenario 7: Re-Upload with Updated Facts

```
Precondition: Host "john.redhat.com" correlated at Tier 6 (hostname, confidence 0.30)

1. New AAP metrics uploaded with richer facts:
   ansible_product_serial: "VMware-42-16-a8"

2. Correlation engine re-evaluates:
   → Tier 1 match found (SMBIOS serial)
   → Confidence upgraded: 0.30 → 1.0
   → Tier upgraded: hostname_heuristic → smbios_serial
   → No duplicate edge created

3. Audit log records the upgrade with previous state
```

## Test Data Setup

To test the correlation engine, the seed script should create:

1. **Discovered resources** with varied raw_properties:
   - VMs with SMBIOS serial and BIOS UUID (Tier 1-2 testable)
   - VMs with MAC and IP only (Tier 3-4 testable)
   - VMs with only hostname (Tier 5-6 testable)

2. **AAP metrics** with varied ansible_facts richness:
   - Hosts with full facts (serial, UUID, MAC, IP, FQDN)
   - Hosts with partial facts (IP + hostname only)
   - Hosts with minimal facts (hostname only)
   - Localhost entries (should be excluded)

3. **Ambiguity cases**:
   - Two resources with identical BIOS UUID (cloned VMs)
   - One AAP host matching multiple resources at same tier
