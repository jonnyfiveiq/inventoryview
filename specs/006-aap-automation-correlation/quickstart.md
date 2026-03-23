# Quickstart: AAP Automation Correlation

**Feature**: 006-aap-automation-correlation
**Date**: 2026-03-22

## Scenario 1: First-time AAP Data Upload

**Steps**:
1. Navigate to sidebar → "Automations" section
2. Click "Upload Metrics Data"
3. Drag & drop (or browse) a metrics utility ZIP/tar.gz file (max 200MB)
4. Wait for parsing and auto-correlation to complete (≤30s for 10k hosts)
5. Review import summary: hosts imported, jobs processed, auto-matched count, pending review count

**Expected outcome**: Import summary shows breakdown. High-confidence matches (SMBIOS UUID, exact hostname) are auto-linked. Lower-confidence matches appear in the review queue.

## Scenario 2: Review and Approve Pending Matches

**Steps**:
1. Navigate to sidebar → "Automations" → "Review Queue"
2. See paginated list of pending matches sorted by confidence score
3. Filter by score range (e.g., 60-79) to focus on near-threshold matches
4. Select multiple matches using checkboxes
5. Click "Approve Selected" to bulk-approve, or click individual rows for override
6. For incorrect suggestions: click row → search/pick a different resource → approve with override

**Expected outcome**: Approved matches create `AUTOMATED_BY` graph edges and learned mappings. On next import, these hostnames auto-match at score 100.

## Scenario 3: View Automation History on Resource Detail

**Steps**:
1. Navigate to any resource detail page (e.g., via search or graph click)
2. Scroll to "Automation History" section
3. See: first automated date, last automated date, total job count
4. Browse paginated job execution timeline with status breakdowns (ok/changed/failures/dark/skipped)

**Expected outcome**: Complete automation trail visible per resource. Direct and indirect automations labelled separately.

## Scenario 4: Automation Coverage Dashboard

**Steps**:
1. Navigate to landing page — see automation coverage summary in the metrics strip
2. Click through to "Automations" → "Coverage" for detailed dashboard
3. View provider-level donut charts showing automated vs. total per vendor
4. See top automated resources and unautomated resources lists

**Expected outcome**: Accurate deduplicated coverage percentages. 3 AAP hostnames resolving to 1 machine = 1 automated resource, not 3.

## Scenario 5: Graph Visualisation with Automation Edges

**Steps**:
1. Navigate to a resource with AAP correlations
2. Open the graph overlay (existing Cytoscape.js canvas)
3. See `AAPHost` nodes connected to the `Resource` node via `AUTOMATED_BY` edges
4. For deduplicated hosts: see all hostname variants (john, john.redhat, john.redhat.com) as separate `AAPHost` nodes pointing to the same `Resource`

**Expected outcome**: Automation relationships visible alongside infrastructure topology. Direct edges styled differently from indirect edges.

## Scenario 6: Export Coverage Report

**Steps**:
1. Navigate to "Automations" → "Reports"
2. Click "Generate Coverage Report"
3. Optionally filter by vendor
4. View in-page or click "Export CSV"

**Expected outcome**: CSV download with columns: resource_uid, resource_name, vendor, type, first_automated, last_automated, total_jobs, aap_hostnames. Deduplicated counts in summary row.

## Scenario 7: Re-import with Learned Mappings

**Steps**:
1. Upload the same (or updated) metrics utility file from the same AAP source
2. Wait for parsing and auto-correlation

**Expected outcome**: Previously-approved hostnames auto-match at score 100 via learned mappings. Review queue is ≥50% smaller than first import. Existing job execution data is merged (no duplicates).
