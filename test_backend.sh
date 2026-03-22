#!/usr/bin/env bash
# End-to-end test for all InventoryView API endpoints.
# Usage: ./test_backend.sh [BASE_URL]
#   BASE_URL defaults to http://localhost:8080/api/v1

set -euo pipefail

BASE="${1:-http://localhost:8080/api/v1}"
PASS=0
FAIL=0
PASSWORD="TestPass-$(date +%s)"
BODY_FILE=$(mktemp)
trap 'rm -f "$BODY_FILE"' EXIT

red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }

assert_status() {
    local label="$1" expected="$2" actual="$3"
    if [ "$actual" -eq "$expected" ]; then
        green "  PASS  $label  (HTTP $actual)"
        PASS=$((PASS + 1))
    else
        red "  FAIL  $label  (expected $expected, got $actual)"
        red "        $(cat "$BODY_FILE")"
        FAIL=$((FAIL + 1))
    fi
}

assert_status_oneof() {
    local label="$1" actual="$2"; shift 2
    for code in "$@"; do
        if [ "$actual" -eq "$code" ]; then
            green "  PASS  $label  (HTTP $actual)"
            PASS=$((PASS + 1))
            return
        fi
    done
    red "  FAIL  $label  (HTTP $actual, expected one of: $*)"
    red "        $(cat "$BODY_FILE")"
    FAIL=$((FAIL + 1))
}

# curl wrapper — sets STATUS and writes body to BODY_FILE
api() {
    local method="$1" path="$2"; shift 2
    STATUS=$(curl -s -o "$BODY_FILE" -w '%{http_code}' -X "$method" "${BASE}${path}" "$@")
}

json_field() {
    python3 -c "import sys,json; print(json.load(sys.stdin).get('$1',''))" < "$BODY_FILE" 2>/dev/null || true
}

# ========== HEALTH ==========
bold "=== Health ==="

api GET /health
assert_status "GET /health" 200 "$STATUS"
db_status=$(json_field database)
if [ "$db_status" = "connected" ]; then
    green "  PASS  database connected"
    PASS=$((PASS + 1))
else
    red "  FAIL  database not connected ($db_status)"
    FAIL=$((FAIL + 1))
fi

# ========== SETUP ==========
bold ""
bold "=== Setup ==="

api GET /setup/status
assert_status "GET /setup/status" 200 "$STATUS"

api POST /setup/init -H 'Content-Type: application/json' -d "{\"password\":\"$PASSWORD\"}"
if [ "$STATUS" -eq 201 ] || [ "$STATUS" -eq 200 ]; then
    green "  PASS  POST /setup/init  (HTTP $STATUS - created)"
    PASS=$((PASS + 1))
elif [ "$STATUS" -eq 409 ]; then
    green "  PASS  POST /setup/init  (HTTP 409 - already set up)"
    PASS=$((PASS + 1))
    bold "  NOTE  Setup already complete. Using default password."
    PASSWORD="SuperSecretPass123"
else
    red "  FAIL  POST /setup/init  (HTTP $STATUS)"
    red "        $(cat "$BODY_FILE")"
    FAIL=$((FAIL + 1))
fi

# ========== AUTH ==========
bold ""
bold "=== Auth ==="

api POST /auth/login -H 'Content-Type: application/json' -d "{\"username\":\"admin\",\"password\":\"$PASSWORD\"}"
assert_status "POST /auth/login" 200 "$STATUS"
TOKEN=$(json_field token)

if [ -z "$TOKEN" ]; then
    red "  FATAL  Could not obtain auth token. Cannot continue."
    bold ""
    bold "=============================="
    red "ABORTED — fix auth and re-run"
    bold "=============================="
    exit 1
fi

AUTH=(-H "Authorization: Bearer $TOKEN")

# Verify auth is enforced
api GET /resources
assert_status "GET /resources without token => 401" 401 "$STATUS"

# ========== RESOURCES ==========
bold ""
bold "=== Resources ==="

# Create resource 1: EC2 instance
api POST /resources "${AUTH[@]}" -H 'Content-Type: application/json' \
    -d '{
        "name": "web-server-01",
        "vendor": "aws",
        "vendor_id": "i-0abc123def456",
        "vendor_type": "aws_instance",
        "normalised_type": "virtual_machine",
        "category": "compute",
        "region": "us-east-1",
        "state": "running",
        "raw_properties": {"instance_type": "t3.medium"}
    }'
assert_status_oneof "POST /resources (ec2)" "$STATUS" 200 201 409
EC2_UID=$(json_field uid)

# Create resource 2: VPC
api POST /resources "${AUTH[@]}" -H 'Content-Type: application/json' \
    -d '{
        "name": "main-vpc",
        "vendor": "aws",
        "vendor_id": "vpc-0abc123",
        "vendor_type": "aws_vpc",
        "normalised_type": "virtual_network",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"cidr": "10.0.0.0/16"}
    }'
assert_status_oneof "POST /resources (vpc)" "$STATUS" 200 201 409
VPC_UID=$(json_field uid)

# Create resource 3: Subnet (for graph depth test)
api POST /resources "${AUTH[@]}" -H 'Content-Type: application/json' \
    -d '{
        "name": "private-subnet-01",
        "vendor": "aws",
        "vendor_id": "subnet-0abc123",
        "vendor_type": "aws_subnet",
        "normalised_type": "subnet",
        "category": "network",
        "region": "us-east-1",
        "state": "active",
        "raw_properties": {"cidr": "10.0.1.0/24"}
    }'
assert_status_oneof "POST /resources (subnet)" "$STATUS" 200 201 409
SUBNET_UID=$(json_field uid)

# List resources
api GET '/resources?vendor=aws' "${AUTH[@]}"
assert_status "GET /resources?vendor=aws" 200 "$STATUS"

# Get single resource
if [ -n "$EC2_UID" ]; then
    api GET "/resources/$EC2_UID" "${AUTH[@]}"
    assert_status "GET /resources/$EC2_UID" 200 "$STATUS"

    # Update resource
    api PATCH "/resources/$EC2_UID" "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d '{"state":"stopped"}'
    assert_status "PATCH /resources/$EC2_UID" 200 "$STATUS"

    updated_state=$(json_field state)
    if [ "$updated_state" = "stopped" ]; then
        green "  PASS  state updated to 'stopped'"
        PASS=$((PASS + 1))
    else
        red "  FAIL  state expected 'stopped', got '$updated_state'"
        FAIL=$((FAIL + 1))
    fi
fi

# Get non-existent resource
api GET /resources/does-not-exist-00000000 "${AUTH[@]}"
assert_status "GET non-existent resource => 404" 404 "$STATUS"

# ========== RELATIONSHIPS ==========
bold ""
bold "=== Relationships ==="

if [ -n "$EC2_UID" ] && [ -n "$VPC_UID" ]; then
    # Create relationship: ec2 -> vpc
    api POST /relationships "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d "{\"source_uid\":\"$EC2_UID\",\"target_uid\":\"$VPC_UID\",\"type\":\"MEMBER_OF\"}"
    assert_status_oneof "POST /relationships (ec2->vpc)" "$STATUS" 200 201 409
fi

if [ -n "$SUBNET_UID" ] && [ -n "$VPC_UID" ]; then
    # Create relationship: subnet -> vpc
    api POST /relationships "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d "{\"source_uid\":\"$SUBNET_UID\",\"target_uid\":\"$VPC_UID\",\"type\":\"MEMBER_OF\"}"
    assert_status_oneof "POST /relationships (subnet->vpc)" "$STATUS" 200 201 409
fi

if [ -n "$EC2_UID" ]; then
    # List relationships for a resource
    api GET "/resources/$EC2_UID/relationships" "${AUTH[@]}"
    assert_status "GET /resources/$EC2_UID/relationships" 200 "$STATUS"

    # Graph traversal
    api GET "/resources/$EC2_UID/graph?depth=2" "${AUTH[@]}"
    assert_status "GET /resources/$EC2_UID/graph?depth=2" 200 "$STATUS"
fi

# ========== CREDENTIALS ==========
bold ""
bold "=== Credentials ==="

api POST /credentials "${AUTH[@]}" -H 'Content-Type: application/json' \
    -d '{"name":"Test AWS Cred","credential_type":"aws_key_pair","secret":{"access_key":"AKIAIOSFODNN7EXAMPLE","secret_key":"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"},"metadata":{"account_id":"123456789"}}'
assert_status_oneof "POST /credentials" "$STATUS" 200 201
CRED_ID=$(json_field id)

api GET /credentials "${AUTH[@]}"
assert_status "GET /credentials" 200 "$STATUS"

# Verify secrets are never returned
has_secret=$(python3 -c "
import sys, json
data = json.load(sys.stdin)
items = data if isinstance(data, list) else data.get('data', data.get('items', []))
for item in (items if isinstance(items, list) else []):
    if 'secret' in item or 'encrypted_secret' in item:
        print('LEAKED'); sys.exit(0)
print('SAFE')
" < "$BODY_FILE" 2>/dev/null || echo "UNKNOWN")
if [ "$has_secret" = "SAFE" ]; then
    green "  PASS  credentials list does not leak secrets"
    PASS=$((PASS + 1))
else
    red "  FAIL  credentials list may contain secrets ($has_secret)"
    FAIL=$((FAIL + 1))
fi

if [ -n "$CRED_ID" ]; then
    api GET "/credentials/$CRED_ID" "${AUTH[@]}"
    assert_status "GET /credentials/$CRED_ID" 200 "$STATUS"

    api PATCH "/credentials/$CRED_ID" "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d '{"metadata":{"account_id":"123456789","env":"test"}}'
    assert_status "PATCH /credentials/$CRED_ID" 200 "$STATUS"

    api POST "/credentials/$CRED_ID/test" "${AUTH[@]}"
    assert_status_oneof "POST /credentials/$CRED_ID/test" "$STATUS" 200 400 422 501

    api DELETE "/credentials/$CRED_ID" "${AUTH[@]}"
    assert_status_oneof "DELETE /credentials/$CRED_ID" "$STATUS" 200 204

    api GET "/credentials/$CRED_ID" "${AUTH[@]}"
    assert_status "GET deleted credential => 404" 404 "$STATUS"
fi

# ========== CLEANUP ==========
bold ""
bold "=== Cleanup ==="

if [ -n "$EC2_UID" ] && [ -n "$VPC_UID" ]; then
    api DELETE /relationships "${AUTH[@]}" -H 'Content-Type: application/json' \
        -d "{\"source_uid\":\"$EC2_UID\",\"target_uid\":\"$VPC_UID\",\"type\":\"MEMBER_OF\"}"
    assert_status_oneof "DELETE /relationships (ec2->vpc)" "$STATUS" 200 204 404
fi

for uid in "$EC2_UID" "$VPC_UID" "$SUBNET_UID"; do
    if [ -n "$uid" ]; then
        api DELETE "/resources/$uid" "${AUTH[@]}"
        assert_status_oneof "DELETE /resources/$uid" "$STATUS" 200 204
    fi
done

# ========== TOKEN REVOCATION ==========
bold ""
bold "=== Token Revocation ==="

api POST /auth/revoke "${AUTH[@]}" -H 'Content-Type: application/json' \
    -d "{\"token\":\"$TOKEN\"}"
assert_status_oneof "POST /auth/revoke" "$STATUS" 200 204

api GET /resources "${AUTH[@]}"
assert_status "GET /resources with revoked token => 401" 401 "$STATUS"

# ========== SUMMARY ==========
bold ""
bold "=============================="
TOTAL=$((PASS + FAIL))
if [ "$FAIL" -eq 0 ]; then
    green "ALL $TOTAL TESTS PASSED"
else
    red "$FAIL/$TOTAL TESTS FAILED"
    green "$PASS/$TOTAL tests passed"
fi
bold "=============================="

exit "$FAIL"
