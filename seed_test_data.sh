#!/usr/bin/env bash
# Seed realistic infrastructure inventory data for testing.
# Usage:
#   ./seed_test_data.sh --vendor=vmware          # seed VMware data
#   ./seed_test_data.sh --vendor=vmware --clean   # delete seeded data first
#   ./seed_test_data.sh --vendor=all              # seed all vendors (future)
#
# Requires a running backend at BASE_URL (default: http://localhost:8080/api/v1)

set -euo pipefail

BASE="${SEED_BASE_URL:-http://localhost:8080/api/v1}"
VENDOR=""
CLEAN=false
PASSWORD="${SEED_PASSWORD:-SuperSecretPass123}"
BODY_FILE=$(mktemp)

red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

usage() {
    echo "Usage: $0 --vendor=<vmware|aws|azure|openshift|all> [--clean]"
    echo ""
    echo "Options:"
    echo "  --vendor=VENDOR   Which vendor dataset to seed (required)"
    echo "  --clean           Delete existing seeded data for the vendor first"
    echo ""
    echo "Environment:"
    echo "  SEED_BASE_URL     API base URL (default: http://localhost:8080/api/v1)"
    echo "  SEED_PASSWORD     Admin password (default: SuperSecretPass123)"
    exit 1
}

for arg in "$@"; do
    case "$arg" in
        --vendor=*) VENDOR="${arg#*=}" ;;
        --clean)    CLEAN=true ;;
        --help|-h)  usage ;;
        *)          red "Unknown argument: $arg"; usage ;;
    esac
done

if [ -z "$VENDOR" ]; then
    red "Error: --vendor is required"
    usage
fi

# ---------- API helpers ----------

api() {
    local method="$1" path="$2"; shift 2
    STATUS=$(curl -s -o "$BODY_FILE" -w '%{http_code}' -X "$method" "${BASE}${path}" "$@")
}

json_field() {
    python3 -c "import sys,json; print(json.load(sys.stdin).get('$1',''))" < "$BODY_FILE" 2>/dev/null || true
}

# Authenticate
api POST /auth/login -H 'Content-Type: application/json' \
    -d "{\"username\":\"admin\",\"password\":\"$PASSWORD\"}"
TOKEN=$(json_field token)
if [ -z "$TOKEN" ]; then
    red "Failed to authenticate. Is the backend running?"
    red "Response: $(cat "$BODY_FILE")"
    exit 1
fi
AUTH=(-H "Authorization: Bearer $TOKEN")
green "Authenticated."

# ---------- Seed helpers ----------

CREATED=0
UPDATED=0
REL_CREATED=0
ERRORS=0

# File-based UID map (macOS bash 3.2 lacks associative arrays)
UID_MAP_FILE=$(mktemp)
trap 'rm -f "$BODY_FILE" "$UID_MAP_FILE"' EXIT

uid_put() { echo "$1=$2" >> "$UID_MAP_FILE"; }
uid_get() { grep "^$1=" "$UID_MAP_FILE" 2>/dev/null | tail -1 | cut -d= -f2; }

create_resource() {
    local json="$1"
    local vendor_id
    vendor_id=$(echo "$json" | python3 -c "import sys,json; print(json.load(sys.stdin)['vendor_id'])")

    api POST /resources "${AUTH[@]}" -H 'Content-Type: application/json' -d "$json"

    if [ "$STATUS" -eq 201 ]; then
        local uid
        uid=$(json_field uid)
        uid_put "$vendor_id" "$uid"
        dim "  + $vendor_id -> $uid"
        CREATED=$((CREATED + 1))
    elif [ "$STATUS" -eq 200 ]; then
        local uid
        uid=$(json_field uid)
        uid_put "$vendor_id" "$uid"
        dim "  ~ $vendor_id (updated)"
        UPDATED=$((UPDATED + 1))
    else
        red "  ! $vendor_id FAILED (HTTP $STATUS): $(cat "$BODY_FILE")"
        ERRORS=$((ERRORS + 1))
    fi
}

create_relationship() {
    local source_vid="$1" target_vid="$2" rel_type="$3"
    local source_uid
    source_uid=$(uid_get "$source_vid")
    local target_uid
    target_uid=$(uid_get "$target_vid")

    if [ -z "$source_uid" ] || [ -z "$target_uid" ]; then
        red "  ! Relationship $source_vid -> $target_vid: missing UID mapping"
        ERRORS=$((ERRORS + 1))
        return
    fi

    api POST /relationships "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d "{\"source_uid\":\"$source_uid\",\"target_uid\":\"$target_uid\",\"type\":\"$rel_type\",\"source_collector\":\"seed-script\",\"confidence\":1.0}"

    if [ "$STATUS" -eq 201 ] || [ "$STATUS" -eq 200 ] || [ "$STATUS" -eq 409 ]; then
        dim "  + $source_vid --[$rel_type]--> $target_vid"
        REL_CREATED=$((REL_CREATED + 1))
    else
        red "  ! Relationship FAILED (HTTP $STATUS): $(cat "$BODY_FILE")"
        ERRORS=$((ERRORS + 1))
    fi
}

# ---------- Clean ----------

clean_vendor() {
    local vendor="$1"
    bold "Cleaning existing $vendor resources..."

    # List all resources for this vendor and delete them
    api GET "/resources?vendor=$vendor&page_size=200" "${AUTH[@]}"
    local uids
    uids=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data.get('data', [])
for item in items:
    uid = item.get('uid', '')
    if uid:
        print(uid)
" < "$BODY_FILE" 2>/dev/null || true)

    local count=0
    while IFS= read -r uid; do
        [ -z "$uid" ] && continue
        api DELETE "/resources/$uid" "${AUTH[@]}"
        count=$((count + 1))
    done <<< "$uids"

    green "  Deleted $count resources."
}

# ---------- VMware seed data ----------
# Simulates a vCenter scan: datacenter -> clusters -> hosts -> VMs
# Plus networking (dvSwitches, port groups) and storage (datastores)

seed_vmware() {
    bold "=== Seeding VMware vSphere inventory ==="
    echo ""

    # --- vCenter ---
    bold "vCenter Server"
    create_resource '{
        "name": "vcsa-prod-01.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "vcsa-prod-01",
        "vendor_type": "vcenter_server",
        "normalised_type": "management_plane",
        "category": "management",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "build": "24322831", "api_version": "8.0.3.0"}
    }'

    # --- Datacenter ---
    bold "Datacenter"
    create_resource '{
        "name": "RDU-DC1",
        "vendor": "vmware",
        "vendor_id": "datacenter-1001",
        "vendor_type": "vim.Datacenter",
        "normalised_type": "datacenter",
        "category": "logical",
        "state": "active",
        "raw_properties": {"overall_status": "green"}
    }'

    # --- Clusters ---
    bold "Clusters"
    create_resource '{
        "name": "Prod-Cluster-01",
        "vendor": "vmware",
        "vendor_id": "domain-c2001",
        "vendor_type": "vim.ClusterComputeResource",
        "normalised_type": "cluster",
        "category": "compute",
        "state": "active",
        "raw_properties": {"drs_enabled": true, "ha_enabled": true, "total_cpu_mhz": 384000, "total_memory_mb": 1572864, "num_hosts": 4}
    }'
    create_resource '{
        "name": "Dev-Cluster-01",
        "vendor": "vmware",
        "vendor_id": "domain-c2002",
        "vendor_type": "vim.ClusterComputeResource",
        "normalised_type": "cluster",
        "category": "compute",
        "state": "active",
        "raw_properties": {"drs_enabled": true, "ha_enabled": false, "total_cpu_mhz": 192000, "total_memory_mb": 786432, "num_hosts": 2}
    }'

    # --- ESXi Hosts ---
    bold "ESXi Hosts"
    create_resource '{
        "name": "esxi-prod-01.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3001",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "cpu_model": "AMD EPYC 9654", "cpu_cores": 96, "memory_mb": 393216, "vendor": "Dell Inc.", "model": "PowerEdge R760"}
    }'
    create_resource '{
        "name": "esxi-prod-02.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3002",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "cpu_model": "AMD EPYC 9654", "cpu_cores": 96, "memory_mb": 393216, "vendor": "Dell Inc.", "model": "PowerEdge R760"}
    }'
    create_resource '{
        "name": "esxi-prod-03.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3003",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "cpu_model": "AMD EPYC 9654", "cpu_cores": 96, "memory_mb": 393216, "vendor": "Dell Inc.", "model": "PowerEdge R760"}
    }'
    create_resource '{
        "name": "esxi-prod-04.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3004",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "maintenance",
        "raw_properties": {"version": "8.0.2", "cpu_model": "AMD EPYC 9654", "cpu_cores": 96, "memory_mb": 393216, "vendor": "Dell Inc.", "model": "PowerEdge R760"}
    }'
    create_resource '{
        "name": "esxi-dev-01.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3005",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "cpu_model": "Intel Xeon Gold 6338", "cpu_cores": 64, "memory_mb": 393216, "vendor": "HPE", "model": "ProLiant DL380 Gen10 Plus"}
    }'
    create_resource '{
        "name": "esxi-dev-02.lab.rdu.redhat.com",
        "vendor": "vmware",
        "vendor_id": "host-3006",
        "vendor_type": "vim.HostSystem",
        "normalised_type": "hypervisor",
        "category": "compute",
        "state": "connected",
        "raw_properties": {"version": "8.0.3", "cpu_model": "Intel Xeon Gold 6338", "cpu_cores": 64, "memory_mb": 393216, "vendor": "HPE", "model": "ProLiant DL380 Gen10 Plus"}
    }'

    # --- Datastores ---
    bold "Datastores"
    create_resource '{
        "name": "vsanDatastore-Prod",
        "vendor": "vmware",
        "vendor_id": "datastore-4001",
        "vendor_type": "vim.Datastore",
        "normalised_type": "datastore",
        "category": "storage",
        "state": "active",
        "raw_properties": {"type": "vsan", "capacity_gb": 51200, "free_gb": 28160, "ssd": true}
    }'
    create_resource '{
        "name": "nfs-iso-share",
        "vendor": "vmware",
        "vendor_id": "datastore-4002",
        "vendor_type": "vim.Datastore",
        "normalised_type": "datastore",
        "category": "storage",
        "state": "active",
        "raw_properties": {"type": "nfs", "capacity_gb": 2048, "free_gb": 1536, "remote_host": "nas01.lab.rdu.redhat.com", "remote_path": "/exports/isos"}
    }'
    create_resource '{
        "name": "vsanDatastore-Dev",
        "vendor": "vmware",
        "vendor_id": "datastore-4003",
        "vendor_type": "vim.Datastore",
        "normalised_type": "datastore",
        "category": "storage",
        "state": "active",
        "raw_properties": {"type": "vsan", "capacity_gb": 25600, "free_gb": 18432, "ssd": true}
    }'

    # --- Distributed Virtual Switches ---
    bold "Networking"
    create_resource '{
        "name": "dvSwitch-Prod",
        "vendor": "vmware",
        "vendor_id": "dvs-5001",
        "vendor_type": "vim.DistributedVirtualSwitch",
        "normalised_type": "virtual_switch",
        "category": "network",
        "state": "active",
        "raw_properties": {"version": "8.0.0", "num_ports": 512, "mtu": 9000, "uplink_port_groups": ["dvUplink-Prod"]}
    }'
    create_resource '{
        "name": "dvSwitch-Dev",
        "vendor": "vmware",
        "vendor_id": "dvs-5002",
        "vendor_type": "vim.DistributedVirtualSwitch",
        "normalised_type": "virtual_switch",
        "category": "network",
        "state": "active",
        "raw_properties": {"version": "8.0.0", "num_ports": 256, "mtu": 1500}
    }'

    # --- Port Groups ---
    create_resource '{
        "name": "VLAN100-Production",
        "vendor": "vmware",
        "vendor_id": "dvportgroup-6001",
        "vendor_type": "vim.DistributedVirtualPortgroup",
        "normalised_type": "port_group",
        "category": "network",
        "state": "active",
        "raw_properties": {"vlan_id": 100, "type": "earlyBinding", "num_ports": 128}
    }'
    create_resource '{
        "name": "VLAN200-Database",
        "vendor": "vmware",
        "vendor_id": "dvportgroup-6002",
        "vendor_type": "vim.DistributedVirtualPortgroup",
        "normalised_type": "port_group",
        "category": "network",
        "state": "active",
        "raw_properties": {"vlan_id": 200, "type": "earlyBinding", "num_ports": 64}
    }'
    create_resource '{
        "name": "VLAN300-Management",
        "vendor": "vmware",
        "vendor_id": "dvportgroup-6003",
        "vendor_type": "vim.DistributedVirtualPortgroup",
        "normalised_type": "port_group",
        "category": "network",
        "state": "active",
        "raw_properties": {"vlan_id": 300, "type": "earlyBinding", "num_ports": 32}
    }'
    create_resource '{
        "name": "VLAN400-Dev",
        "vendor": "vmware",
        "vendor_id": "dvportgroup-6004",
        "vendor_type": "vim.DistributedVirtualPortgroup",
        "normalised_type": "port_group",
        "category": "network",
        "state": "active",
        "raw_properties": {"vlan_id": 400, "type": "earlyBinding", "num_ports": 128}
    }'

    # --- Virtual Machines ---
    bold "Virtual Machines"
    create_resource '{
        "name": "rhel9-webserver-01",
        "vendor": "vmware",
        "vendor_id": "vm-7001",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 4, "memory_mb": 8192, "disk_gb": 100, "ip_address": "10.100.1.10", "tools_status": "toolsOk", "annotation": "Production web tier"}
    }'
    create_resource '{
        "name": "rhel9-webserver-02",
        "vendor": "vmware",
        "vendor_id": "vm-7002",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 4, "memory_mb": 8192, "disk_gb": 100, "ip_address": "10.100.1.11", "tools_status": "toolsOk", "annotation": "Production web tier"}
    }'
    create_resource '{
        "name": "rhel9-db-primary",
        "vendor": "vmware",
        "vendor_id": "vm-7003",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 8, "memory_mb": 32768, "disk_gb": 500, "ip_address": "10.200.1.10", "tools_status": "toolsOk", "annotation": "PostgreSQL primary"}
    }'
    create_resource '{
        "name": "rhel9-db-replica",
        "vendor": "vmware",
        "vendor_id": "vm-7004",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 8, "memory_mb": 32768, "disk_gb": 500, "ip_address": "10.200.1.11", "tools_status": "toolsOk", "annotation": "PostgreSQL streaming replica"}
    }'
    create_resource '{
        "name": "aap-controller-01",
        "vendor": "vmware",
        "vendor_id": "vm-7005",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 4, "memory_mb": 16384, "disk_gb": 200, "ip_address": "10.100.1.50", "tools_status": "toolsOk", "annotation": "Ansible Automation Platform Controller"}
    }'
    create_resource '{
        "name": "aap-hub-01",
        "vendor": "vmware",
        "vendor_id": "vm-7006",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 4, "memory_mb": 16384, "disk_gb": 200, "ip_address": "10.100.1.51", "tools_status": "toolsOk", "annotation": "Ansible Automation Platform Private Hub"}
    }'
    create_resource '{
        "name": "satellite-01",
        "vendor": "vmware",
        "vendor_id": "vm-7007",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 4, "memory_mb": 24576, "disk_gb": 500, "ip_address": "10.300.1.10", "tools_status": "toolsOk", "annotation": "Red Hat Satellite 6.15"}
    }'
    create_resource '{
        "name": "idm-01",
        "vendor": "vmware",
        "vendor_id": "vm-7008",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 2, "memory_mb": 4096, "disk_gb": 50, "ip_address": "10.300.1.20", "tools_status": "toolsOk", "annotation": "Red Hat IdM / FreeIPA"}
    }'
    create_resource '{
        "name": "dev-rhel9-testbed",
        "vendor": "vmware",
        "vendor_id": "vm-7009",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 2, "memory_mb": 4096, "disk_gb": 80, "ip_address": "10.400.1.10", "tools_status": "toolsOk", "annotation": "Dev test VM"}
    }'
    create_resource '{
        "name": "win2022-legacy-app",
        "vendor": "vmware",
        "vendor_id": "vm-7010",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOn",
        "raw_properties": {"guest_os": "Microsoft Windows Server 2022 (64-bit)", "num_cpu": 4, "memory_mb": 16384, "disk_gb": 200, "ip_address": "10.100.1.90", "tools_status": "toolsOk", "annotation": "Legacy .NET application - migration pending"}
    }'
    create_resource '{
        "name": "template-rhel9-base",
        "vendor": "vmware",
        "vendor_id": "vm-7011",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOff",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 9 (64-bit)", "num_cpu": 2, "memory_mb": 2048, "disk_gb": 40, "tools_status": "toolsOk", "is_template": true, "annotation": "Golden image - packer built"}
    }'
    create_resource '{
        "name": "decom-oldapp-01",
        "vendor": "vmware",
        "vendor_id": "vm-7012",
        "vendor_type": "vim.VirtualMachine",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "state": "poweredOff",
        "raw_properties": {"guest_os": "Red Hat Enterprise Linux 8 (64-bit)", "num_cpu": 2, "memory_mb": 4096, "disk_gb": 60, "tools_status": "toolsNotRunning", "annotation": "DECOMMISSION - ticket INFRA-4521"}
    }'

    # --- Resource Pools ---
    bold "Resource Pools"
    create_resource '{
        "name": "Prod-RP-High",
        "vendor": "vmware",
        "vendor_id": "resgroup-8001",
        "vendor_type": "vim.ResourcePool",
        "normalised_type": "resource_pool",
        "category": "compute",
        "state": "active",
        "raw_properties": {"cpu_reservation_mhz": 96000, "memory_reservation_mb": 524288, "cpu_shares": "high", "memory_shares": "high"}
    }'
    create_resource '{
        "name": "Prod-RP-Normal",
        "vendor": "vmware",
        "vendor_id": "resgroup-8002",
        "vendor_type": "vim.ResourcePool",
        "normalised_type": "resource_pool",
        "category": "compute",
        "state": "active",
        "raw_properties": {"cpu_reservation_mhz": 0, "memory_reservation_mb": 0, "cpu_shares": "normal", "memory_shares": "normal"}
    }'

    # ========== RELATIONSHIPS ==========
    echo ""
    bold "=== Building relationships ==="
    echo ""

    # vCenter manages datacenter
    bold "Management hierarchy"
    create_relationship "vcsa-prod-01"     "datacenter-1001"  "MANAGES"

    # Datacenter contains clusters
    bold "Datacenter -> Clusters"
    create_relationship "datacenter-1001"  "domain-c2001"     "CONTAINS"
    create_relationship "datacenter-1001"  "domain-c2002"     "CONTAINS"

    # Datacenter contains networking
    bold "Datacenter -> Networking"
    create_relationship "datacenter-1001"  "dvs-5001"         "CONTAINS"
    create_relationship "datacenter-1001"  "dvs-5002"         "CONTAINS"

    # Datacenter contains datastores
    bold "Datacenter -> Datastores"
    create_relationship "datacenter-1001"  "datastore-4001"   "CONTAINS"
    create_relationship "datacenter-1001"  "datastore-4002"   "CONTAINS"
    create_relationship "datacenter-1001"  "datastore-4003"   "CONTAINS"

    # Clusters contain hosts
    bold "Clusters -> Hosts"
    create_relationship "domain-c2001"     "host-3001"        "CONTAINS"
    create_relationship "domain-c2001"     "host-3002"        "CONTAINS"
    create_relationship "domain-c2001"     "host-3003"        "CONTAINS"
    create_relationship "domain-c2001"     "host-3004"        "CONTAINS"
    create_relationship "domain-c2002"     "host-3005"        "CONTAINS"
    create_relationship "domain-c2002"     "host-3006"        "CONTAINS"

    # Clusters contain resource pools
    bold "Clusters -> Resource Pools"
    create_relationship "domain-c2001"     "resgroup-8001"    "CONTAINS"
    create_relationship "domain-c2001"     "resgroup-8002"    "CONTAINS"

    # Hosts attached to datastores
    bold "Hosts -> Datastores"
    create_relationship "host-3001"        "datastore-4001"   "ATTACHED_TO"
    create_relationship "host-3002"        "datastore-4001"   "ATTACHED_TO"
    create_relationship "host-3003"        "datastore-4001"   "ATTACHED_TO"
    create_relationship "host-3004"        "datastore-4001"   "ATTACHED_TO"
    create_relationship "host-3001"        "datastore-4002"   "ATTACHED_TO"
    create_relationship "host-3005"        "datastore-4003"   "ATTACHED_TO"
    create_relationship "host-3006"        "datastore-4003"   "ATTACHED_TO"

    # Hosts connected to dvSwitches
    bold "Hosts -> dvSwitches"
    create_relationship "host-3001"        "dvs-5001"         "CONNECTED_TO"
    create_relationship "host-3002"        "dvs-5001"         "CONNECTED_TO"
    create_relationship "host-3003"        "dvs-5001"         "CONNECTED_TO"
    create_relationship "host-3004"        "dvs-5001"         "CONNECTED_TO"
    create_relationship "host-3005"        "dvs-5002"         "CONNECTED_TO"
    create_relationship "host-3006"        "dvs-5002"         "CONNECTED_TO"

    # dvSwitches contain port groups
    bold "dvSwitches -> Port Groups"
    create_relationship "dvs-5001"         "dvportgroup-6001" "CONTAINS"
    create_relationship "dvs-5001"         "dvportgroup-6002" "CONTAINS"
    create_relationship "dvs-5001"         "dvportgroup-6003" "CONTAINS"
    create_relationship "dvs-5002"         "dvportgroup-6004" "CONTAINS"

    # VMs hosted on specific ESXi hosts
    bold "VMs -> Hosts"
    create_relationship "vm-7001"          "host-3001"        "HOSTED_ON"
    create_relationship "vm-7002"          "host-3002"        "HOSTED_ON"
    create_relationship "vm-7003"          "host-3001"        "HOSTED_ON"
    create_relationship "vm-7004"          "host-3002"        "HOSTED_ON"
    create_relationship "vm-7005"          "host-3003"        "HOSTED_ON"
    create_relationship "vm-7006"          "host-3003"        "HOSTED_ON"
    create_relationship "vm-7007"          "host-3001"        "HOSTED_ON"
    create_relationship "vm-7008"          "host-3002"        "HOSTED_ON"
    create_relationship "vm-7009"          "host-3005"        "HOSTED_ON"
    create_relationship "vm-7010"          "host-3003"        "HOSTED_ON"
    create_relationship "vm-7011"          "host-3001"        "HOSTED_ON"
    create_relationship "vm-7012"          "host-3001"        "HOSTED_ON"

    # VMs connected to port groups (network)
    bold "VMs -> Port Groups"
    create_relationship "vm-7001"          "dvportgroup-6001" "CONNECTED_TO"
    create_relationship "vm-7002"          "dvportgroup-6001" "CONNECTED_TO"
    create_relationship "vm-7003"          "dvportgroup-6002" "CONNECTED_TO"
    create_relationship "vm-7004"          "dvportgroup-6002" "CONNECTED_TO"
    create_relationship "vm-7005"          "dvportgroup-6001" "CONNECTED_TO"
    create_relationship "vm-7006"          "dvportgroup-6001" "CONNECTED_TO"
    create_relationship "vm-7007"          "dvportgroup-6003" "CONNECTED_TO"
    create_relationship "vm-7008"          "dvportgroup-6003" "CONNECTED_TO"
    create_relationship "vm-7009"          "dvportgroup-6004" "CONNECTED_TO"
    create_relationship "vm-7010"          "dvportgroup-6001" "CONNECTED_TO"

    # VMs stored on datastores
    bold "VMs -> Datastores"
    create_relationship "vm-7001"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7002"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7003"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7004"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7005"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7006"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7007"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7008"          "datastore-4001"   "ATTACHED_TO"
    create_relationship "vm-7009"          "datastore-4003"   "ATTACHED_TO"
    create_relationship "vm-7010"          "datastore-4001"   "ATTACHED_TO"

    # VMs in resource pools
    bold "VMs -> Resource Pools"
    create_relationship "vm-7003"          "resgroup-8001"    "MEMBER_OF"
    create_relationship "vm-7004"          "resgroup-8001"    "MEMBER_OF"
    create_relationship "vm-7001"          "resgroup-8002"    "MEMBER_OF"
    create_relationship "vm-7002"          "resgroup-8002"    "MEMBER_OF"

    # Application dependencies (db replica depends on primary)
    bold "Application dependencies"
    create_relationship "vm-7004"          "vm-7003"          "DEPENDS_ON"
    create_relationship "vm-7001"          "vm-7003"          "DEPENDS_ON"
    create_relationship "vm-7002"          "vm-7003"          "DEPENDS_ON"
    create_relationship "vm-7005"          "vm-7003"          "DEPENDS_ON"

    # ========== DRIFT HISTORY ==========
    echo ""
    bold "=== Seeding drift history ==="
    echo ""
    seed_drift
}

# ---------- Drift seed data ----------
# Inserts historical drift entries directly into the resource_drift table via
# a dedicated POST endpoint is not available, so we use raw SQL through a
# small Python helper that talks to the DB directly. Instead, we'll use
# the API — we add a simple helper that POSTs drift entries.

create_drift_entry() {
    local resource_vid="$1" field="$2" old_val="$3" new_val="$4" changed_at="$5" source="${6:-seed-script}"
    local resource_uid
    resource_uid=$(uid_get "$resource_vid")

    if [ -z "$resource_uid" ]; then
        red "  ! Drift $resource_vid: missing UID mapping"
        ERRORS=$((ERRORS + 1))
        return
    fi

    api POST "/resources/${resource_uid}/drift" "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d "{\"field\":\"$field\",\"old_value\":$old_val,\"new_value\":$new_val,\"changed_at\":\"$changed_at\",\"source\":\"$source\"}"

    if [ "$STATUS" -eq 201 ] || [ "$STATUS" -eq 200 ]; then
        dim "  + drift: $resource_vid.$field @ $changed_at"
        DRIFT_CREATED=$((DRIFT_CREATED + 1))
    else
        red "  ! Drift FAILED (HTTP $STATUS): $(cat "$BODY_FILE")"
        ERRORS=$((ERRORS + 1))
    fi
}

seed_drift() {
    DRIFT_CREATED=0

    # --- VM power state changes ---
    bold "VM power state drift"

    # rhel9-webserver-01: was powered off for maintenance, then back on
    create_drift_entry "vm-7001" "state" '"poweredOn"' '"poweredOff"' "2026-03-10T02:00:00Z"
    create_drift_entry "vm-7001" "state" '"poweredOff"' '"poweredOn"' "2026-03-10T04:30:00Z"

    # rhel9-db-primary: restarted during patching
    create_drift_entry "vm-7003" "state" '"poweredOn"' '"poweredOff"' "2026-03-14T01:00:00Z"
    create_drift_entry "vm-7003" "state" '"poweredOff"' '"poweredOn"' "2026-03-14T01:15:00Z"

    # dev-rhel9-testbed: frequent power cycles
    create_drift_entry "vm-7009" "state" '"poweredOn"' '"poweredOff"' "2026-03-08T18:00:00Z"
    create_drift_entry "vm-7009" "state" '"poweredOff"' '"poweredOn"' "2026-03-09T09:00:00Z"
    create_drift_entry "vm-7009" "state" '"poweredOn"' '"poweredOff"' "2026-03-12T17:30:00Z"
    create_drift_entry "vm-7009" "state" '"poweredOff"' '"poweredOn"' "2026-03-13T08:00:00Z"
    create_drift_entry "vm-7009" "state" '"poweredOn"' '"poweredOff"' "2026-03-18T22:00:00Z"
    create_drift_entry "vm-7009" "state" '"poweredOff"' '"poweredOn"' "2026-03-19T07:30:00Z"

    # decom-oldapp-01: powered off and stayed off
    create_drift_entry "vm-7012" "state" '"poweredOn"' '"poweredOff"' "2026-03-05T16:00:00Z"

    # --- CPU/Memory configuration changes ---
    bold "Configuration drift"

    # rhel9-db-primary: scaled up CPU and memory
    create_drift_entry "vm-7003" "num_cpu" '"4"' '"8"' "2026-03-07T03:00:00Z"
    create_drift_entry "vm-7003" "memory_mb" '"16384"' '"32768"' "2026-03-07T03:00:00Z"

    # aap-controller-01: memory increase
    create_drift_entry "vm-7005" "memory_mb" '"8192"' '"16384"' "2026-03-11T02:00:00Z"

    # rhel9-webserver-01: disk expansion
    create_drift_entry "vm-7001" "disk_gb" '"60"' '"100"' "2026-03-09T04:00:00Z"

    # rhel9-webserver-02: CPU scale-up
    create_drift_entry "vm-7002" "num_cpu" '"2"' '"4"' "2026-03-12T03:00:00Z"

    # win2022-legacy-app: memory bump for load
    create_drift_entry "vm-7010" "memory_mb" '"8192"' '"16384"' "2026-03-15T02:00:00Z"

    # --- ESXi host state changes ---
    bold "Host drift"

    # esxi-prod-04: entered maintenance mode
    create_drift_entry "host-3004" "state" '"connected"' '"maintenance"' "2026-03-16T01:00:00Z"

    # esxi-prod-04: ESXi version patched
    create_drift_entry "host-3004" "version" '"8.0.1"' '"8.0.2"' "2026-03-16T03:00:00Z"

    # esxi-prod-01: version patched
    create_drift_entry "host-3001" "version" '"8.0.2"' '"8.0.3"' "2026-03-06T02:00:00Z"

    # --- IP address changes ---
    bold "Network drift"

    # dev-rhel9-testbed: IP reassigned via DHCP
    create_drift_entry "vm-7009" "ip_address" '"10.400.1.5"' '"10.400.1.10"' "2026-03-09T09:05:00Z"

    # --- Tools status changes ---
    bold "VMware Tools drift"

    # decom-oldapp-01: tools stopped
    create_drift_entry "vm-7012" "tools_status" '"toolsOk"' '"toolsNotRunning"' "2026-03-05T16:05:00Z"

    green "  Drift entries created: $DRIFT_CREATED"
}

# ========================================================================
# AWS seed data
# Simulates an AWS account: VPCs, subnets, EC2 instances, RDS, ELB, S3, EKS
# ========================================================================

seed_aws() {
    bold "=== Seeding AWS inventory ==="
    echo ""

    # --- VPC ---
    bold "VPCs"
    create_resource '{
        "name": "prod-vpc-us-east-1",
        "vendor": "aws",
        "vendor_id": "vpc-0a1b2c3d4e5f",
        "vendor_type": "AWS::EC2::VPC",
        "normalised_type": "virtual_network",
        "category": "network",
        "region": "us-east-1",
        "state": "available",
        "raw_properties": {"cidr_block": "10.0.0.0/16", "is_default": false, "enable_dns_support": true, "enable_dns_hostnames": true}
    }'
    create_resource '{
        "name": "dev-vpc-us-east-1",
        "vendor": "aws",
        "vendor_id": "vpc-0f1e2d3c4b5a",
        "vendor_type": "AWS::EC2::VPC",
        "normalised_type": "virtual_network",
        "category": "network",
        "region": "us-east-1",
        "state": "available",
        "raw_properties": {"cidr_block": "10.1.0.0/16", "is_default": false}
    }'

    # --- Subnets ---
    bold "Subnets"
    create_resource '{
        "name": "prod-subnet-public-1a",
        "vendor": "aws",
        "vendor_id": "subnet-pub-1a",
        "vendor_type": "AWS::EC2::Subnet",
        "normalised_type": "subnet",
        "category": "network",
        "region": "us-east-1a",
        "state": "available",
        "raw_properties": {"cidr_block": "10.0.1.0/24", "map_public_ip": true, "available_ips": 248}
    }'
    create_resource '{
        "name": "prod-subnet-public-1b",
        "vendor": "aws",
        "vendor_id": "subnet-pub-1b",
        "vendor_type": "AWS::EC2::Subnet",
        "normalised_type": "subnet",
        "category": "network",
        "region": "us-east-1b",
        "state": "available",
        "raw_properties": {"cidr_block": "10.0.2.0/24", "map_public_ip": true, "available_ips": 246}
    }'
    create_resource '{
        "name": "prod-subnet-private-1a",
        "vendor": "aws",
        "vendor_id": "subnet-priv-1a",
        "vendor_type": "AWS::EC2::Subnet",
        "normalised_type": "subnet",
        "category": "network",
        "region": "us-east-1a",
        "state": "available",
        "raw_properties": {"cidr_block": "10.0.10.0/24", "map_public_ip": false, "available_ips": 250}
    }'
    create_resource '{
        "name": "prod-subnet-private-1b",
        "vendor": "aws",
        "vendor_id": "subnet-priv-1b",
        "vendor_type": "AWS::EC2::Subnet",
        "normalised_type": "subnet",
        "category": "network",
        "region": "us-east-1b",
        "state": "available",
        "raw_properties": {"cidr_block": "10.0.11.0/24", "map_public_ip": false, "available_ips": 247}
    }'

    # --- Security Groups ---
    bold "Security Groups"
    create_resource '{
        "name": "sg-web-tier",
        "vendor": "aws",
        "vendor_id": "sg-0web1234",
        "vendor_type": "AWS::EC2::SecurityGroup",
        "normalised_type": "security_group",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"description": "Web tier - HTTP/HTTPS ingress", "ingress_rules": 3, "egress_rules": 1}
    }'
    create_resource '{
        "name": "sg-app-tier",
        "vendor": "aws",
        "vendor_id": "sg-0app5678",
        "vendor_type": "AWS::EC2::SecurityGroup",
        "normalised_type": "security_group",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"description": "App tier - internal only", "ingress_rules": 2, "egress_rules": 1}
    }'
    create_resource '{
        "name": "sg-database",
        "vendor": "aws",
        "vendor_id": "sg-0db91011",
        "vendor_type": "AWS::EC2::SecurityGroup",
        "normalised_type": "security_group",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"description": "Database tier - PostgreSQL 5432", "ingress_rules": 1, "egress_rules": 1}
    }'

    # --- EC2 Instances ---
    bold "EC2 Instances"
    create_resource '{
        "name": "prod-web-01",
        "vendor": "aws",
        "vendor_id": "i-0web01aaa",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1a",
        "state": "running",
        "raw_properties": {"instance_type": "m6i.xlarge", "num_cpu": 4, "memory_mb": 16384, "ami_id": "ami-0rhel9base", "private_ip": "10.0.1.10", "public_ip": "54.210.10.10", "platform": "RHEL 9"}
    }'
    create_resource '{
        "name": "prod-web-02",
        "vendor": "aws",
        "vendor_id": "i-0web02bbb",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1b",
        "state": "running",
        "raw_properties": {"instance_type": "m6i.xlarge", "num_cpu": 4, "memory_mb": 16384, "ami_id": "ami-0rhel9base", "private_ip": "10.0.2.10", "public_ip": "54.210.10.11", "platform": "RHEL 9"}
    }'
    create_resource '{
        "name": "prod-api-01",
        "vendor": "aws",
        "vendor_id": "i-0api01ccc",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1a",
        "state": "running",
        "raw_properties": {"instance_type": "c6i.2xlarge", "num_cpu": 8, "memory_mb": 16384, "ami_id": "ami-0rhel9base", "private_ip": "10.0.10.20", "platform": "RHEL 9"}
    }'
    create_resource '{
        "name": "prod-api-02",
        "vendor": "aws",
        "vendor_id": "i-0api02ddd",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1b",
        "state": "running",
        "raw_properties": {"instance_type": "c6i.2xlarge", "num_cpu": 8, "memory_mb": 16384, "ami_id": "ami-0rhel9base", "private_ip": "10.0.11.20", "platform": "RHEL 9"}
    }'
    create_resource '{
        "name": "bastion-01",
        "vendor": "aws",
        "vendor_id": "i-0bastion01",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1a",
        "state": "running",
        "raw_properties": {"instance_type": "t3.small", "num_cpu": 2, "memory_mb": 2048, "private_ip": "10.0.1.100", "public_ip": "54.210.10.99", "platform": "Amazon Linux 2023"}
    }'
    create_resource '{
        "name": "dev-sandbox-01",
        "vendor": "aws",
        "vendor_id": "i-0devsand01",
        "vendor_type": "AWS::EC2::Instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1a",
        "state": "stopped",
        "raw_properties": {"instance_type": "t3.medium", "num_cpu": 2, "memory_mb": 4096, "private_ip": "10.1.1.10", "platform": "RHEL 9"}
    }'

    # --- RDS ---
    bold "RDS Instances"
    create_resource '{
        "name": "prod-postgres-primary",
        "vendor": "aws",
        "vendor_id": "rds-prod-pg-primary",
        "vendor_type": "AWS::RDS::DBInstance",
        "normalised_type": "database",
        "category": "storage",
        "region": "us-east-1a",
        "state": "available",
        "raw_properties": {"engine": "postgres", "engine_version": "16.4", "instance_class": "db.r6g.xlarge", "num_cpu": 4, "memory_mb": 32768, "storage_gb": 500, "multi_az": true, "storage_type": "gp3", "iops": 3000}
    }'
    create_resource '{
        "name": "prod-postgres-replica",
        "vendor": "aws",
        "vendor_id": "rds-prod-pg-replica",
        "vendor_type": "AWS::RDS::DBInstance",
        "normalised_type": "database",
        "category": "storage",
        "region": "us-east-1b",
        "state": "available",
        "raw_properties": {"engine": "postgres", "engine_version": "16.4", "instance_class": "db.r6g.xlarge", "num_cpu": 4, "memory_mb": 32768, "storage_gb": 500, "replication_source": "rds-prod-pg-primary", "storage_type": "gp3"}
    }'

    # --- ELB ---
    bold "Load Balancers"
    create_resource '{
        "name": "prod-alb-web",
        "vendor": "aws",
        "vendor_id": "alb-prod-web",
        "vendor_type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "normalised_type": "load_balancer",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"type": "application", "scheme": "internet-facing", "dns_name": "prod-alb-web-123456.us-east-1.elb.amazonaws.com", "listeners": 2}
    }'
    create_resource '{
        "name": "prod-alb-api",
        "vendor": "aws",
        "vendor_id": "alb-prod-api",
        "vendor_type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
        "normalised_type": "load_balancer",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"type": "application", "scheme": "internal", "dns_name": "prod-alb-api-789012.us-east-1.elb.amazonaws.com", "listeners": 1}
    }'

    # --- S3 Buckets ---
    bold "S3 Buckets"
    create_resource '{
        "name": "acme-prod-assets",
        "vendor": "aws",
        "vendor_id": "s3-acme-prod-assets",
        "vendor_type": "AWS::S3::Bucket",
        "normalised_type": "object_storage",
        "category": "storage",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"versioning": true, "encryption": "AES256", "public_access_blocked": true, "size_gb": 450}
    }'
    create_resource '{
        "name": "acme-prod-backups",
        "vendor": "aws",
        "vendor_id": "s3-acme-prod-backups",
        "vendor_type": "AWS::S3::Bucket",
        "normalised_type": "object_storage",
        "category": "storage",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"versioning": true, "encryption": "aws:kms", "lifecycle_rules": 2, "public_access_blocked": true, "size_gb": 1200}
    }'
    create_resource '{
        "name": "acme-prod-logs",
        "vendor": "aws",
        "vendor_id": "s3-acme-prod-logs",
        "vendor_type": "AWS::S3::Bucket",
        "normalised_type": "object_storage",
        "category": "storage",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"versioning": false, "encryption": "AES256", "lifecycle_rules": 1, "public_access_blocked": true, "size_gb": 80}
    }'

    # --- EKS ---
    bold "EKS Cluster"
    create_resource '{
        "name": "prod-eks-cluster",
        "vendor": "aws",
        "vendor_id": "eks-prod-cluster",
        "vendor_type": "AWS::EKS::Cluster",
        "normalised_type": "kubernetes_cluster",
        "category": "compute",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"version": "1.29", "platform_version": "eks.8", "endpoint": "https://ABCDEF.gr7.us-east-1.eks.amazonaws.com", "node_groups": 2, "total_nodes": 6}
    }'

    # ========== RELATIONSHIPS ==========
    echo ""
    bold "=== Building AWS relationships ==="
    echo ""

    # VPC contains subnets
    bold "VPC -> Subnets"
    create_relationship "vpc-0a1b2c3d4e5f" "subnet-pub-1a"   "CONTAINS"
    create_relationship "vpc-0a1b2c3d4e5f" "subnet-pub-1b"   "CONTAINS"
    create_relationship "vpc-0a1b2c3d4e5f" "subnet-priv-1a"  "CONTAINS"
    create_relationship "vpc-0a1b2c3d4e5f" "subnet-priv-1b"  "CONTAINS"

    # Security groups in VPC
    bold "VPC -> Security Groups"
    create_relationship "vpc-0a1b2c3d4e5f" "sg-0web1234"     "CONTAINS"
    create_relationship "vpc-0a1b2c3d4e5f" "sg-0app5678"     "CONTAINS"
    create_relationship "vpc-0a1b2c3d4e5f" "sg-0db91011"     "CONTAINS"

    # EC2 hosted on subnets
    bold "EC2 -> Subnets"
    create_relationship "i-0web01aaa"    "subnet-pub-1a"     "HOSTED_ON"
    create_relationship "i-0web02bbb"    "subnet-pub-1b"     "HOSTED_ON"
    create_relationship "i-0api01ccc"    "subnet-priv-1a"    "HOSTED_ON"
    create_relationship "i-0api02ddd"    "subnet-priv-1b"    "HOSTED_ON"
    create_relationship "i-0bastion01"   "subnet-pub-1a"     "HOSTED_ON"

    # EC2 connected to security groups
    bold "EC2 -> Security Groups"
    create_relationship "i-0web01aaa"    "sg-0web1234"       "MEMBER_OF"
    create_relationship "i-0web02bbb"    "sg-0web1234"       "MEMBER_OF"
    create_relationship "i-0api01ccc"    "sg-0app5678"       "MEMBER_OF"
    create_relationship "i-0api02ddd"    "sg-0app5678"       "MEMBER_OF"
    create_relationship "i-0bastion01"   "sg-0web1234"       "MEMBER_OF"

    # ALB routes to EC2
    bold "ALB -> EC2"
    create_relationship "alb-prod-web"   "i-0web01aaa"       "ROUTES_TO"
    create_relationship "alb-prod-web"   "i-0web02bbb"       "ROUTES_TO"
    create_relationship "alb-prod-api"   "i-0api01ccc"       "ROUTES_TO"
    create_relationship "alb-prod-api"   "i-0api02ddd"       "ROUTES_TO"

    # ALB in subnets
    bold "ALB -> Subnets"
    create_relationship "alb-prod-web"   "subnet-pub-1a"     "HOSTED_ON"
    create_relationship "alb-prod-web"   "subnet-pub-1b"     "HOSTED_ON"
    create_relationship "alb-prod-api"   "subnet-priv-1a"    "HOSTED_ON"
    create_relationship "alb-prod-api"   "subnet-priv-1b"    "HOSTED_ON"

    # RDS in subnets
    bold "RDS -> Subnets"
    create_relationship "rds-prod-pg-primary" "subnet-priv-1a" "HOSTED_ON"
    create_relationship "rds-prod-pg-replica" "subnet-priv-1b" "HOSTED_ON"

    # RDS security group
    bold "RDS -> Security Groups"
    create_relationship "rds-prod-pg-primary" "sg-0db91011"   "MEMBER_OF"
    create_relationship "rds-prod-pg-replica" "sg-0db91011"   "MEMBER_OF"

    # Replica depends on primary
    bold "RDS dependencies"
    create_relationship "rds-prod-pg-replica" "rds-prod-pg-primary" "DEPENDS_ON"

    # App depends on DB
    bold "App dependencies"
    create_relationship "i-0api01ccc"    "rds-prod-pg-primary" "DEPENDS_ON"
    create_relationship "i-0api02ddd"    "rds-prod-pg-primary" "DEPENDS_ON"
    create_relationship "i-0web01aaa"    "i-0api01ccc"         "DEPENDS_ON"
    create_relationship "i-0web02bbb"    "i-0api02ddd"         "DEPENDS_ON"

    # EKS in subnets
    bold "EKS -> Subnets"
    create_relationship "eks-prod-cluster" "subnet-priv-1a"   "HOSTED_ON"
    create_relationship "eks-prod-cluster" "subnet-priv-1b"   "HOSTED_ON"

    # ========== DRIFT ==========
    echo ""
    bold "=== Seeding AWS drift history ==="
    echo ""
    DRIFT_CREATED=0

    # prod-web-01: instance type change (scale-up)
    create_drift_entry "i-0web01aaa" "instance_type" '"m6i.large"' '"m6i.xlarge"' "2026-03-08T04:00:00Z"
    create_drift_entry "i-0web01aaa" "num_cpu" '"2"' '"4"' "2026-03-08T04:00:00Z"
    create_drift_entry "i-0web01aaa" "memory_mb" '"8192"' '"16384"' "2026-03-08T04:00:00Z"

    # dev-sandbox-01: stopped after hours
    create_drift_entry "i-0devsand01" "state" '"running"' '"stopped"' "2026-03-15T18:00:00Z"

    # RDS engine version upgrade
    create_drift_entry "rds-prod-pg-primary" "engine_version" '"16.2"' '"16.4"' "2026-03-12T03:00:00Z"
    create_drift_entry "rds-prod-pg-replica" "engine_version" '"16.2"' '"16.4"' "2026-03-12T03:30:00Z"

    # RDS storage expansion
    create_drift_entry "rds-prod-pg-primary" "storage_gb" '"250"' '"500"' "2026-03-10T02:00:00Z"

    green "  Drift entries created: $DRIFT_CREATED"
}

# ========================================================================
# Azure seed data
# Simulates: Resource Groups, VNets, VMs, AKS, SQL DB, Storage, App Gateway
# ========================================================================

seed_azure() {
    bold "=== Seeding Azure inventory ==="
    echo ""

    # --- Resource Groups ---
    bold "Resource Groups"
    create_resource '{
        "name": "rg-prod-eastus",
        "vendor": "azure",
        "vendor_id": "rg-prod-eastus",
        "vendor_type": "Microsoft.Resources/resourceGroups",
        "normalised_type": "resource_group",
        "category": "logical",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"subscription": "acme-production", "tags": {"environment": "production", "cost_center": "eng-001"}}
    }'
    create_resource '{
        "name": "rg-dev-eastus",
        "vendor": "azure",
        "vendor_id": "rg-dev-eastus",
        "vendor_type": "Microsoft.Resources/resourceGroups",
        "normalised_type": "resource_group",
        "category": "logical",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"subscription": "acme-development", "tags": {"environment": "development"}}
    }'

    # --- VNets ---
    bold "Virtual Networks"
    create_resource '{
        "name": "vnet-prod-eastus",
        "vendor": "azure",
        "vendor_id": "vnet-prod-eastus",
        "vendor_type": "Microsoft.Network/virtualNetworks",
        "normalised_type": "virtual_network",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"address_space": "10.10.0.0/16", "subnets": 4, "dns_servers": ["10.10.0.4"]}
    }'

    # --- Subnets ---
    bold "Subnets"
    create_resource '{
        "name": "snet-web",
        "vendor": "azure",
        "vendor_id": "snet-web-prod",
        "vendor_type": "Microsoft.Network/virtualNetworks/subnets",
        "normalised_type": "subnet",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"address_prefix": "10.10.1.0/24", "nsg": "nsg-web"}
    }'
    create_resource '{
        "name": "snet-app",
        "vendor": "azure",
        "vendor_id": "snet-app-prod",
        "vendor_type": "Microsoft.Network/virtualNetworks/subnets",
        "normalised_type": "subnet",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"address_prefix": "10.10.2.0/24", "nsg": "nsg-app"}
    }'
    create_resource '{
        "name": "snet-data",
        "vendor": "azure",
        "vendor_id": "snet-data-prod",
        "vendor_type": "Microsoft.Network/virtualNetworks/subnets",
        "normalised_type": "subnet",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"address_prefix": "10.10.3.0/24", "nsg": "nsg-data", "service_endpoints": ["Microsoft.Sql", "Microsoft.Storage"]}
    }'

    # --- NSGs ---
    bold "Network Security Groups"
    create_resource '{
        "name": "nsg-web",
        "vendor": "azure",
        "vendor_id": "nsg-web-prod",
        "vendor_type": "Microsoft.Network/networkSecurityGroups",
        "normalised_type": "security_group",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"rules_count": 5, "default_action": "Deny"}
    }'
    create_resource '{
        "name": "nsg-app",
        "vendor": "azure",
        "vendor_id": "nsg-app-prod",
        "vendor_type": "Microsoft.Network/networkSecurityGroups",
        "normalised_type": "security_group",
        "category": "network",
        "region": "eastus",
        "state": "active",
        "raw_properties": {"rules_count": 3, "default_action": "Deny"}
    }'

    # --- Virtual Machines ---
    bold "Virtual Machines"
    create_resource '{
        "name": "vm-web-prod-01",
        "vendor": "azure",
        "vendor_id": "az-vm-web-01",
        "vendor_type": "Microsoft.Compute/virtualMachines",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "eastus",
        "state": "running",
        "raw_properties": {"vm_size": "Standard_D4s_v5", "num_cpu": 4, "memory_mb": 16384, "os_type": "Linux", "os_offer": "RHEL", "os_sku": "9-lvm-gen2", "disk_gb": 128, "private_ip": "10.10.1.10"}
    }'
    create_resource '{
        "name": "vm-web-prod-02",
        "vendor": "azure",
        "vendor_id": "az-vm-web-02",
        "vendor_type": "Microsoft.Compute/virtualMachines",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "eastus",
        "state": "running",
        "raw_properties": {"vm_size": "Standard_D4s_v5", "num_cpu": 4, "memory_mb": 16384, "os_type": "Linux", "os_offer": "RHEL", "os_sku": "9-lvm-gen2", "disk_gb": 128, "private_ip": "10.10.1.11"}
    }'
    create_resource '{
        "name": "vm-jumpbox-prod",
        "vendor": "azure",
        "vendor_id": "az-vm-jumpbox",
        "vendor_type": "Microsoft.Compute/virtualMachines",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "eastus",
        "state": "running",
        "raw_properties": {"vm_size": "Standard_B2s", "num_cpu": 2, "memory_mb": 4096, "os_type": "Linux", "os_offer": "RHEL", "os_sku": "9-lvm-gen2", "disk_gb": 64, "private_ip": "10.10.1.100"}
    }'
    create_resource '{
        "name": "vm-dev-test-01",
        "vendor": "azure",
        "vendor_id": "az-vm-dev-01",
        "vendor_type": "Microsoft.Compute/virtualMachines",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "eastus",
        "state": "deallocated",
        "raw_properties": {"vm_size": "Standard_D2s_v5", "num_cpu": 2, "memory_mb": 8192, "os_type": "Linux", "os_offer": "RHEL", "os_sku": "9-lvm-gen2", "disk_gb": 64, "private_ip": "10.10.1.200"}
    }'

    # --- Azure SQL ---
    bold "Azure SQL"
    create_resource '{
        "name": "sql-prod-eastus",
        "vendor": "azure",
        "vendor_id": "az-sql-prod",
        "vendor_type": "Microsoft.Sql/servers",
        "normalised_type": "database_server",
        "category": "storage",
        "region": "eastus",
        "state": "ready",
        "raw_properties": {"version": "12.0", "admin_login": "sqladmin", "fqdn": "sql-prod-eastus.database.windows.net"}
    }'
    create_resource '{
        "name": "sqldb-acme-prod",
        "vendor": "azure",
        "vendor_id": "az-sqldb-acme",
        "vendor_type": "Microsoft.Sql/servers/databases",
        "normalised_type": "database",
        "category": "storage",
        "region": "eastus",
        "state": "online",
        "raw_properties": {"sku": "GP_Gen5_4", "num_cpu": 4, "max_size_gb": 256, "collation": "SQL_Latin1_General_CP1_CI_AS", "zone_redundant": true}
    }'

    # --- Storage Account ---
    bold "Storage"
    create_resource '{
        "name": "stacmeprod001",
        "vendor": "azure",
        "vendor_id": "az-st-acmeprod",
        "vendor_type": "Microsoft.Storage/storageAccounts",
        "normalised_type": "object_storage",
        "category": "storage",
        "region": "eastus",
        "state": "available",
        "raw_properties": {"sku": "Standard_GRS", "kind": "StorageV2", "access_tier": "Hot", "https_only": true, "blob_containers": 5, "size_gb": 320}
    }'

    # --- AKS Cluster ---
    bold "AKS Cluster"
    create_resource '{
        "name": "aks-prod-eastus",
        "vendor": "azure",
        "vendor_id": "az-aks-prod",
        "vendor_type": "Microsoft.ContainerService/managedClusters",
        "normalised_type": "kubernetes_cluster",
        "category": "compute",
        "region": "eastus",
        "state": "running",
        "raw_properties": {"kubernetes_version": "1.29.2", "node_pools": 2, "total_nodes": 5, "network_plugin": "azure", "tier": "Standard"}
    }'

    # --- App Gateway ---
    bold "Application Gateway"
    create_resource '{
        "name": "appgw-prod-eastus",
        "vendor": "azure",
        "vendor_id": "az-appgw-prod",
        "vendor_type": "Microsoft.Network/applicationGateways",
        "normalised_type": "load_balancer",
        "category": "network",
        "region": "eastus",
        "state": "running",
        "raw_properties": {"sku": "WAF_v2", "capacity": 2, "waf_enabled": true, "backend_pools": 2, "listeners": 2}
    }'

    # ========== RELATIONSHIPS ==========
    echo ""
    bold "=== Building Azure relationships ==="
    echo ""

    # Resource group contains resources
    bold "Resource Group hierarchy"
    create_relationship "rg-prod-eastus" "vnet-prod-eastus"   "CONTAINS"
    create_relationship "rg-prod-eastus" "az-vm-web-01"       "CONTAINS"
    create_relationship "rg-prod-eastus" "az-vm-web-02"       "CONTAINS"
    create_relationship "rg-prod-eastus" "az-vm-jumpbox"      "CONTAINS"
    create_relationship "rg-prod-eastus" "az-sql-prod"        "CONTAINS"
    create_relationship "rg-prod-eastus" "az-st-acmeprod"     "CONTAINS"
    create_relationship "rg-prod-eastus" "az-aks-prod"        "CONTAINS"
    create_relationship "rg-prod-eastus" "az-appgw-prod"      "CONTAINS"
    create_relationship "rg-dev-eastus"  "az-vm-dev-01"       "CONTAINS"

    # VNet contains subnets
    bold "VNet -> Subnets"
    create_relationship "vnet-prod-eastus" "snet-web-prod"    "CONTAINS"
    create_relationship "vnet-prod-eastus" "snet-app-prod"    "CONTAINS"
    create_relationship "vnet-prod-eastus" "snet-data-prod"   "CONTAINS"

    # NSGs attached to subnets
    bold "NSGs -> Subnets"
    create_relationship "nsg-web-prod"  "snet-web-prod"       "ATTACHED_TO"
    create_relationship "nsg-app-prod"  "snet-app-prod"       "ATTACHED_TO"

    # VMs hosted on subnets
    bold "VMs -> Subnets"
    create_relationship "az-vm-web-01"  "snet-web-prod"       "HOSTED_ON"
    create_relationship "az-vm-web-02"  "snet-web-prod"       "HOSTED_ON"
    create_relationship "az-vm-jumpbox" "snet-web-prod"       "HOSTED_ON"

    # SQL in data subnet
    bold "SQL -> Subnets"
    create_relationship "az-sql-prod"   "snet-data-prod"      "HOSTED_ON"
    create_relationship "az-sqldb-acme" "az-sql-prod"         "HOSTED_ON"

    # AKS in app subnet
    bold "AKS -> Subnet"
    create_relationship "az-aks-prod"   "snet-app-prod"       "HOSTED_ON"

    # App Gateway routes to VMs
    bold "AppGW -> VMs"
    create_relationship "az-appgw-prod" "az-vm-web-01"        "ROUTES_TO"
    create_relationship "az-appgw-prod" "az-vm-web-02"        "ROUTES_TO"

    # App dependencies
    bold "App dependencies"
    create_relationship "az-vm-web-01"  "az-sqldb-acme"       "DEPENDS_ON"
    create_relationship "az-vm-web-02"  "az-sqldb-acme"       "DEPENDS_ON"

    # ========== DRIFT ==========
    echo ""
    bold "=== Seeding Azure drift history ==="
    echo ""
    DRIFT_CREATED=0

    # VM scale-up
    create_drift_entry "az-vm-web-01" "vm_size" '"Standard_D2s_v5"' '"Standard_D4s_v5"' "2026-03-09T02:00:00Z"
    create_drift_entry "az-vm-web-01" "num_cpu" '"2"' '"4"' "2026-03-09T02:00:00Z"
    create_drift_entry "az-vm-web-01" "memory_mb" '"8192"' '"16384"' "2026-03-09T02:00:00Z"

    # Dev VM deallocated
    create_drift_entry "az-vm-dev-01" "state" '"running"' '"deallocated"' "2026-03-14T19:00:00Z"

    # AKS version upgrade
    create_drift_entry "az-aks-prod" "kubernetes_version" '"1.28.5"' '"1.29.2"' "2026-03-11T03:00:00Z"

    # SQL database scaled
    create_drift_entry "az-sqldb-acme" "max_size_gb" '"128"' '"256"' "2026-03-13T02:00:00Z"

    green "  Drift entries created: $DRIFT_CREATED"
}

# ========================================================================
# OpenShift seed data
# Simulates: Cluster, nodes (master/worker/infra), projects, deployments,
# routes, PVCs, services
# ========================================================================

seed_openshift() {
    bold "=== Seeding OpenShift inventory ==="
    echo ""

    # --- Cluster ---
    bold "OpenShift Cluster"
    create_resource '{
        "name": "ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-prod-rdu",
        "vendor_type": "cluster",
        "normalised_type": "kubernetes_cluster",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"version": "4.15.8", "platform": "vsphere", "channel": "stable-4.15", "cluster_id": "d1e2f3a4-b5c6-7890-abcd-ef0123456789", "api_url": "https://api.ocp-prod-rdu.lab.rdu.redhat.com:6443"}
    }'

    # --- Master Nodes ---
    bold "Master Nodes"
    create_resource '{
        "name": "master-0.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-master-0",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "master", "num_cpu": 8, "memory_mb": 32768, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8", "container_runtime": "cri-o://1.28.4"}
    }'
    create_resource '{
        "name": "master-1.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-master-1",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "master", "num_cpu": 8, "memory_mb": 32768, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8"}
    }'
    create_resource '{
        "name": "master-2.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-master-2",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "master", "num_cpu": 8, "memory_mb": 32768, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8"}
    }'

    # --- Worker Nodes ---
    bold "Worker Nodes"
    create_resource '{
        "name": "worker-0.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-worker-0",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "worker", "num_cpu": 16, "memory_mb": 65536, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8", "pods_running": 42}
    }'
    create_resource '{
        "name": "worker-1.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-worker-1",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "worker", "num_cpu": 16, "memory_mb": 65536, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8", "pods_running": 38}
    }'
    create_resource '{
        "name": "worker-2.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-worker-2",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "worker", "num_cpu": 16, "memory_mb": 65536, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8", "pods_running": 35}
    }'
    create_resource '{
        "name": "worker-3.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-worker-3",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "not_ready",
        "raw_properties": {"role": "worker", "num_cpu": 16, "memory_mb": 65536, "os": "RHCOS 4.15", "kubelet_version": "v1.28.8+073f9f8", "pods_running": 0, "condition": "DiskPressure"}
    }'

    # --- Infra Nodes ---
    bold "Infra Nodes"
    create_resource '{
        "name": "infra-0.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-infra-0",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "infra", "num_cpu": 8, "memory_mb": 32768, "os": "RHCOS 4.15", "taint": "node-role.kubernetes.io/infra:NoSchedule"}
    }'
    create_resource '{
        "name": "infra-1.ocp-prod-rdu",
        "vendor": "openshift",
        "vendor_id": "ocp-infra-1",
        "vendor_type": "node",
        "normalised_type": "kubernetes_node",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "ready",
        "raw_properties": {"role": "infra", "num_cpu": 8, "memory_mb": 32768, "os": "RHCOS 4.15", "taint": "node-role.kubernetes.io/infra:NoSchedule"}
    }'

    # --- Projects (Namespaces) ---
    bold "Projects"
    create_resource '{
        "name": "acme-frontend",
        "vendor": "openshift",
        "vendor_id": "ocp-ns-acme-fe",
        "vendor_type": "namespace",
        "normalised_type": "namespace",
        "category": "logical",
        "region": "rdu-dc1",
        "state": "active",
        "raw_properties": {"display_name": "ACME Frontend", "requester": "dev-team", "quota_cpu": "8", "quota_memory": "16Gi"}
    }'
    create_resource '{
        "name": "acme-backend",
        "vendor": "openshift",
        "vendor_id": "ocp-ns-acme-be",
        "vendor_type": "namespace",
        "normalised_type": "namespace",
        "category": "logical",
        "region": "rdu-dc1",
        "state": "active",
        "raw_properties": {"display_name": "ACME Backend", "requester": "dev-team", "quota_cpu": "16", "quota_memory": "32Gi"}
    }'
    create_resource '{
        "name": "monitoring",
        "vendor": "openshift",
        "vendor_id": "ocp-ns-monitoring",
        "vendor_type": "namespace",
        "normalised_type": "namespace",
        "category": "logical",
        "region": "rdu-dc1",
        "state": "active",
        "raw_properties": {"display_name": "Cluster Monitoring", "managed_by": "cluster-admin"}
    }'

    # --- Deployments ---
    bold "Deployments"
    create_resource '{
        "name": "frontend-web",
        "vendor": "openshift",
        "vendor_id": "ocp-deploy-fe-web",
        "vendor_type": "apps/deployment",
        "normalised_type": "deployment",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "available",
        "raw_properties": {"replicas": 3, "ready_replicas": 3, "image": "registry.acme.com/frontend:v2.4.1", "strategy": "RollingUpdate", "cpu_request": "500m", "memory_request": "512Mi"}
    }'
    create_resource '{
        "name": "backend-api",
        "vendor": "openshift",
        "vendor_id": "ocp-deploy-be-api",
        "vendor_type": "apps/deployment",
        "normalised_type": "deployment",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "available",
        "raw_properties": {"replicas": 4, "ready_replicas": 4, "image": "registry.acme.com/backend:v3.1.0", "strategy": "RollingUpdate", "cpu_request": "1000m", "memory_request": "1Gi"}
    }'
    create_resource '{
        "name": "backend-worker",
        "vendor": "openshift",
        "vendor_id": "ocp-deploy-be-worker",
        "vendor_type": "apps/deployment",
        "normalised_type": "deployment",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "available",
        "raw_properties": {"replicas": 2, "ready_replicas": 2, "image": "registry.acme.com/worker:v3.1.0", "strategy": "RollingUpdate", "cpu_request": "2000m", "memory_request": "2Gi"}
    }'
    create_resource '{
        "name": "prometheus",
        "vendor": "openshift",
        "vendor_id": "ocp-deploy-prometheus",
        "vendor_type": "apps/statefulset",
        "normalised_type": "statefulset",
        "category": "compute",
        "region": "rdu-dc1",
        "state": "available",
        "raw_properties": {"replicas": 2, "ready_replicas": 2, "image": "quay.io/prometheus/prometheus:v2.51.0", "storage_class": "thin-csi", "storage_size": "100Gi"}
    }'

    # --- Routes ---
    bold "Routes"
    create_resource '{
        "name": "frontend-route",
        "vendor": "openshift",
        "vendor_id": "ocp-route-fe",
        "vendor_type": "route.openshift.io/route",
        "normalised_type": "ingress",
        "category": "network",
        "region": "rdu-dc1",
        "state": "admitted",
        "raw_properties": {"host": "app.acme.com", "tls_termination": "edge", "insecure_policy": "Redirect", "target_port": "8080-tcp"}
    }'
    create_resource '{
        "name": "api-route",
        "vendor": "openshift",
        "vendor_id": "ocp-route-api",
        "vendor_type": "route.openshift.io/route",
        "normalised_type": "ingress",
        "category": "network",
        "region": "rdu-dc1",
        "state": "admitted",
        "raw_properties": {"host": "api.acme.com", "tls_termination": "reencrypt", "target_port": "8443-tcp"}
    }'

    # --- PVCs ---
    bold "Persistent Volume Claims"
    create_resource '{
        "name": "prometheus-data-0",
        "vendor": "openshift",
        "vendor_id": "ocp-pvc-prom-0",
        "vendor_type": "v1/persistentvolumeclaim",
        "normalised_type": "persistent_volume",
        "category": "storage",
        "region": "rdu-dc1",
        "state": "bound",
        "raw_properties": {"storage_class": "thin-csi", "capacity": "100Gi", "access_mode": "ReadWriteOnce", "volume_name": "pv-vsphere-abcde"}
    }'
    create_resource '{
        "name": "prometheus-data-1",
        "vendor": "openshift",
        "vendor_id": "ocp-pvc-prom-1",
        "vendor_type": "v1/persistentvolumeclaim",
        "normalised_type": "persistent_volume",
        "category": "storage",
        "region": "rdu-dc1",
        "state": "bound",
        "raw_properties": {"storage_class": "thin-csi", "capacity": "100Gi", "access_mode": "ReadWriteOnce", "volume_name": "pv-vsphere-fghij"}
    }'

    # --- Services ---
    bold "Services"
    create_resource '{
        "name": "frontend-svc",
        "vendor": "openshift",
        "vendor_id": "ocp-svc-fe",
        "vendor_type": "v1/service",
        "normalised_type": "service",
        "category": "network",
        "region": "rdu-dc1",
        "state": "active",
        "raw_properties": {"type": "ClusterIP", "cluster_ip": "172.30.10.50", "ports": [{"port": 8080, "protocol": "TCP"}], "selector": "app=frontend-web"}
    }'
    create_resource '{
        "name": "backend-svc",
        "vendor": "openshift",
        "vendor_id": "ocp-svc-be",
        "vendor_type": "v1/service",
        "normalised_type": "service",
        "category": "network",
        "region": "rdu-dc1",
        "state": "active",
        "raw_properties": {"type": "ClusterIP", "cluster_ip": "172.30.10.60", "ports": [{"port": 8443, "protocol": "TCP"}], "selector": "app=backend-api"}
    }'

    # ========== RELATIONSHIPS ==========
    echo ""
    bold "=== Building OpenShift relationships ==="
    echo ""

    # Cluster contains nodes
    bold "Cluster -> Nodes"
    create_relationship "ocp-prod-rdu"  "ocp-master-0"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-master-1"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-master-2"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-worker-0"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-worker-1"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-worker-2"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-worker-3"        "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-infra-0"         "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-infra-1"         "CONTAINS"

    # Cluster contains projects
    bold "Cluster -> Projects"
    create_relationship "ocp-prod-rdu"  "ocp-ns-acme-fe"      "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-ns-acme-be"      "CONTAINS"
    create_relationship "ocp-prod-rdu"  "ocp-ns-monitoring"   "CONTAINS"

    # Deployments in projects
    bold "Projects -> Deployments"
    create_relationship "ocp-ns-acme-fe"    "ocp-deploy-fe-web"     "CONTAINS"
    create_relationship "ocp-ns-acme-be"    "ocp-deploy-be-api"     "CONTAINS"
    create_relationship "ocp-ns-acme-be"    "ocp-deploy-be-worker"  "CONTAINS"
    create_relationship "ocp-ns-monitoring" "ocp-deploy-prometheus" "CONTAINS"

    # Routes in projects
    bold "Projects -> Routes"
    create_relationship "ocp-ns-acme-fe"   "ocp-route-fe"          "CONTAINS"
    create_relationship "ocp-ns-acme-be"   "ocp-route-api"         "CONTAINS"

    # Services in projects
    bold "Projects -> Services"
    create_relationship "ocp-ns-acme-fe"   "ocp-svc-fe"            "CONTAINS"
    create_relationship "ocp-ns-acme-be"   "ocp-svc-be"            "CONTAINS"

    # PVCs in projects
    bold "Projects -> PVCs"
    create_relationship "ocp-ns-monitoring" "ocp-pvc-prom-0"       "CONTAINS"
    create_relationship "ocp-ns-monitoring" "ocp-pvc-prom-1"       "CONTAINS"

    # Routes route to services
    bold "Routes -> Services"
    create_relationship "ocp-route-fe"  "ocp-svc-fe"               "ROUTES_TO"
    create_relationship "ocp-route-api" "ocp-svc-be"               "ROUTES_TO"

    # Services route to deployments
    bold "Services -> Deployments"
    create_relationship "ocp-svc-fe"    "ocp-deploy-fe-web"        "ROUTES_TO"
    create_relationship "ocp-svc-be"    "ocp-deploy-be-api"        "ROUTES_TO"

    # Deployments hosted on worker nodes
    bold "Deployments -> Nodes"
    create_relationship "ocp-deploy-fe-web"     "ocp-worker-0"     "HOSTED_ON"
    create_relationship "ocp-deploy-fe-web"     "ocp-worker-1"     "HOSTED_ON"
    create_relationship "ocp-deploy-be-api"     "ocp-worker-0"     "HOSTED_ON"
    create_relationship "ocp-deploy-be-api"     "ocp-worker-2"     "HOSTED_ON"
    create_relationship "ocp-deploy-be-worker"  "ocp-worker-1"     "HOSTED_ON"
    create_relationship "ocp-deploy-prometheus" "ocp-infra-0"      "HOSTED_ON"
    create_relationship "ocp-deploy-prometheus" "ocp-infra-1"      "HOSTED_ON"

    # PVCs attached to statefulsets
    bold "PVCs -> StatefulSets"
    create_relationship "ocp-pvc-prom-0" "ocp-deploy-prometheus"   "ATTACHED_TO"
    create_relationship "ocp-pvc-prom-1" "ocp-deploy-prometheus"   "ATTACHED_TO"

    # App dependencies
    bold "App dependencies"
    create_relationship "ocp-deploy-fe-web"    "ocp-deploy-be-api"    "DEPENDS_ON"
    create_relationship "ocp-deploy-be-api"    "ocp-deploy-be-worker" "DEPENDS_ON"

    # ========== DRIFT ==========
    echo ""
    bold "=== Seeding OpenShift drift history ==="
    echo ""
    DRIFT_CREATED=0

    # Cluster version upgrade
    create_drift_entry "ocp-prod-rdu" "version" '"4.14.12"' '"4.15.8"' "2026-03-06T02:00:00Z"

    # Worker-3 went not_ready
    create_drift_entry "ocp-worker-3" "state" '"ready"' '"not_ready"' "2026-03-18T14:30:00Z"

    # Frontend deployment image update (rolling release)
    create_drift_entry "ocp-deploy-fe-web" "image" '"registry.acme.com/frontend:v2.3.0"' '"registry.acme.com/frontend:v2.4.1"' "2026-03-17T10:00:00Z"
    create_drift_entry "ocp-deploy-fe-web" "replicas" '"2"' '"3"' "2026-03-15T09:00:00Z"

    # Backend API deployment image update
    create_drift_entry "ocp-deploy-be-api" "image" '"registry.acme.com/backend:v3.0.2"' '"registry.acme.com/backend:v3.1.0"' "2026-03-17T10:15:00Z"
    create_drift_entry "ocp-deploy-be-api" "replicas" '"2"' '"4"' "2026-03-13T11:00:00Z"

    # Worker node kubelet version during upgrade
    create_drift_entry "ocp-worker-0" "kubelet_version" '"v1.27.10+28fee89"' '"v1.28.8+073f9f8"' "2026-03-06T03:00:00Z"
    create_drift_entry "ocp-worker-1" "kubelet_version" '"v1.27.10+28fee89"' '"v1.28.8+073f9f8"' "2026-03-06T03:15:00Z"
    create_drift_entry "ocp-worker-2" "kubelet_version" '"v1.27.10+28fee89"' '"v1.28.8+073f9f8"' "2026-03-06T03:30:00Z"

    green "  Drift entries created: $DRIFT_CREATED"
}

# ---------- Dispatch ----------

case "$VENDOR" in
    vmware)
        if $CLEAN; then clean_vendor vmware; fi
        seed_vmware
        ;;
    aws)
        if $CLEAN; then clean_vendor aws; fi
        seed_aws
        ;;
    azure)
        if $CLEAN; then clean_vendor azure; fi
        seed_azure
        ;;
    openshift)
        if $CLEAN; then clean_vendor openshift; fi
        seed_openshift
        ;;
    all)
        if $CLEAN; then
            for v in vmware aws azure openshift; do clean_vendor "$v"; done
        fi
        seed_vmware
        seed_aws
        seed_azure
        seed_openshift
        ;;
    *)
        red "Unknown vendor: $VENDOR"
        red "Supported: vmware, aws, azure, openshift, all"
        exit 1
        ;;
esac

# ---------- Summary ----------
echo ""
bold "=============================="
green "Resources created: $CREATED"
if [ "$UPDATED" -gt 0 ]; then
    green "Resources updated: $UPDATED  (already existed)"
fi
green "Relationships:     $REL_CREATED"
if [ "$ERRORS" -gt 0 ]; then
    red "Errors:            $ERRORS"
fi
bold "=============================="
