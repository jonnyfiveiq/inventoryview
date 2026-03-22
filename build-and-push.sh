#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# Build and push InventoryView container image to quay.io
# Usage: ./build-and-push.sh [--no-push] [--tag <tag>]
# ============================================================

REGISTRY="quay.io/jhardy"
IMAGE="inventoryview"
TAG="latest"
PUSH=true
if [ -n "${CONTAINER_ENGINE:-}" ]; then
    BUILDER="$CONTAINER_ENGINE"
elif command -v podman &>/dev/null; then
    BUILDER="podman"
else
    BUILDER="docker"
fi

red()   { printf '\033[1;31m%s\033[0m\n' "$*"; }
green() { printf '\033[1;32m%s\033[0m\n' "$*"; }
bold()  { printf '\033[1m%s\033[0m\n' "$*"; }
dim()   { printf '\033[2m%s\033[0m\n' "$*"; }

while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-push)  PUSH=false; shift ;;
        --tag)      TAG="$2"; shift 2 ;;
        --tag=*)    TAG="${1#*=}"; shift ;;
        --docker)   BUILDER="docker"; shift ;;
        --podman)   BUILDER="podman"; shift ;;
        *)          red "Unknown option: $1"; exit 1 ;;
    esac
done

FULL_TAG="${REGISTRY}/${IMAGE}:${TAG}"

bold "=== InventoryView Container Build ==="
dim "Engine:  ${BUILDER}"
dim "Image:   ${FULL_TAG}"
dim "Push:    ${PUSH}"
echo ""

# ----------------------------------------------------------
# Ensure we're at the repo root
# ----------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f backend/Dockerfile ] || [ ! -f frontend/package.json ]; then
    red "Error: Run this script from the repository root."
    exit 1
fi

# ----------------------------------------------------------
# Build the all-in-one image
# ----------------------------------------------------------
bold "[1/3] Building container image..."
$BUILDER build \
    -t "${IMAGE}:${TAG}" \
    -t "${FULL_TAG}" \
    -f backend/Dockerfile \
    .

green "Build complete: ${FULL_TAG}"

# ----------------------------------------------------------
# Push to quay.io
# ----------------------------------------------------------
if [ "$PUSH" = true ]; then
    bold "[2/3] Logging in to quay.io..."
    if ! $BUILDER login --get-login quay.io > /dev/null 2>&1; then
        $BUILDER login quay.io
    else
        dim "Already logged in to quay.io"
    fi

    bold "[3/3] Pushing to ${FULL_TAG}..."
    $BUILDER push "${FULL_TAG}"
    green "Pushed: ${FULL_TAG}"

    echo ""
    bold "=== Done ==="
    echo ""
    echo "Users can now run:"
    echo ""
    echo "  ${BUILDER} pull ${FULL_TAG}"
    echo "  ${BUILDER} run -d --name inventoryview -p 8080:8080 ${FULL_TAG}"
    echo ""
    echo "Then open http://localhost:8080"
    echo "Login: admin / SuperSecretPass123"
else
    dim "[2/3] Skipping login (--no-push)"
    dim "[3/3] Skipping push (--no-push)"
    echo ""
    bold "=== Build only — not pushed ==="
    echo ""
    echo "Run locally:"
    echo ""
    echo "  ${BUILDER} run -d --name inventoryview -p 8080:8080 ${IMAGE}:${TAG}"
fi
