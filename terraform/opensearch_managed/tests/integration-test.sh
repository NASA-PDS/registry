#!/usr/bin/env bash
#
# Integration tests for OpenSearch Managed deployment
#
# Runs against a real AWS deployment to verify the Terraform-provisioned
# infrastructure works correctly. Assumes Terraform has already been applied.
#
# Usage:
#   ./tests/integration-test.sh --domain-name <name> [options]
#
# Options:
#   --domain-name NAME     Required. The OpenSearch domain name to test.
#   --region REGION        AWS region (default: us-west-2)
#   --component-name NAME  Component name for SSM paths (default: registry)
#   --skip-smoke           Skip endpoint reachability test
#   --verbose              Show full AWS CLI output
#   --help                 Show this help message
#
# Exit codes:
#   0 - All tests passed
#   1 - One or more tests failed
#   2 - Invalid arguments or missing dependencies

set -o pipefail

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DOMAIN_NAME=""
REGION="us-west-2"
COMPONENT_NAME="registry"
SKIP_SMOKE=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

usage() {
    cat <<'EOF'
Usage:
  ./tests/integration-test.sh --domain-name <name> [options]

Options:
  --domain-name NAME     Required. The OpenSearch domain name to test.
  --region REGION        AWS region (default: us-west-2)
  --component-name NAME  Component name for SSM paths (default: registry)
  --skip-smoke           Skip endpoint reachability test
  --verbose              Show full AWS CLI output
  --help                 Show this help message

Examples:
  ./tests/integration-test.sh --domain-name pds-mcp-registry-dev-mos
  ./tests/integration-test.sh --domain-name pds-mcp-registry-dev-mos --verbose
EOF
    exit 2
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
}

log_verbose() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

check_dependencies() {
    local missing=()

    for cmd in aws jq curl; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ "${#missing[@]}" -ne 0 ]; then
        echo -e "${RED}[ERROR]${NC} Missing required commands: ${missing[*]}"
        echo "Please install them and try again."
        exit 2
    fi
}

# -----------------------------------------------------------------------------
# Parse arguments
# -----------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case $1 in
        --domain-name)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo -e "${RED}[ERROR]${NC} --domain-name requires a value"
                exit 2
            fi
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --region)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo -e "${RED}[ERROR]${NC} --region requires a value"
                exit 2
            fi
            REGION="$2"
            shift 2
            ;;
        --component-name)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo -e "${RED}[ERROR]${NC} --component-name requires a value"
                exit 2
            fi
            COMPONENT_NAME="$2"
            shift 2
            ;;
        --skip-smoke)
            SKIP_SMOKE=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            usage
            ;;
        *)
            echo -e "${RED}[ERROR]${NC} Unknown option: $1"
            usage
            ;;
    esac
done

if [ -z "$DOMAIN_NAME" ]; then
    echo -e "${RED}[ERROR]${NC} --domain-name is required"
    usage
fi

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

check_dependencies

echo ""
echo "=============================================="
echo " OpenSearch Managed Integration Tests"
echo "=============================================="
echo ""
echo "Domain:    $DOMAIN_NAME"
echo "Region:    $REGION"
echo "Component: $COMPONENT_NAME"
echo ""

# -----------------------------------------------------------------------------
# Test 1: Domain exists
# -----------------------------------------------------------------------------

log_info "Test: Domain exists"

if DOMAIN_INFO=$(aws opensearch describe-domain \
    --domain-name "$DOMAIN_NAME" \
    --region "$REGION" \
    --output json 2>&1); then
    log_pass "Domain '$DOMAIN_NAME' exists"
    log_verbose "$DOMAIN_INFO"
else
    log_fail "Domain '$DOMAIN_NAME' not found: $DOMAIN_INFO"
    echo ""
    echo -e "${RED}Cannot continue - domain does not exist.${NC}"
    echo "Ensure Terraform has been applied before running integration tests."
    exit 1
fi

# -----------------------------------------------------------------------------
# Test 2: Domain endpoint is available
# -----------------------------------------------------------------------------

log_info "Test: Domain endpoint is available"

ENDPOINT=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.Endpoint // empty')

if [ -n "$ENDPOINT" ]; then
    log_pass "Domain endpoint: $ENDPOINT"
else
    log_fail "Domain endpoint not available (domain may still be provisioning)"
fi

# -----------------------------------------------------------------------------
# Test 3: Cluster configuration
# -----------------------------------------------------------------------------

log_info "Test: Cluster configuration"

INSTANCE_TYPE=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.ClusterConfig.InstanceType')
INSTANCE_COUNT=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.ClusterConfig.InstanceCount')
MASTER_ENABLED=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.ClusterConfig.DedicatedMasterEnabled')
ZONE_AWARENESS=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.ClusterConfig.ZoneAwarenessEnabled')

echo "  Instance type:     $INSTANCE_TYPE"
echo "  Instance count:    $INSTANCE_COUNT"
echo "  Master enabled:    $MASTER_ENABLED"
echo "  Zone awareness:    $ZONE_AWARENESS"

if [ "$MASTER_ENABLED" = "true" ]; then
    log_pass "Dedicated master nodes enabled"
else
    log_fail "Dedicated master nodes not enabled"
fi

if [ "$ZONE_AWARENESS" = "true" ]; then
    log_pass "Zone awareness enabled"
else
    log_fail "Zone awareness not enabled"
fi

# -----------------------------------------------------------------------------
# Test 4: EBS configuration
# -----------------------------------------------------------------------------

log_info "Test: EBS configuration"

EBS_ENABLED=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.EBSOptions.EBSEnabled')
EBS_TYPE=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.EBSOptions.VolumeType')
EBS_SIZE=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.EBSOptions.VolumeSize')

echo "  EBS enabled:   $EBS_ENABLED"
echo "  Volume type:   $EBS_TYPE"
echo "  Volume size:   ${EBS_SIZE}GB"

if [ "$EBS_ENABLED" = "true" ]; then
    log_pass "EBS storage enabled"
else
    log_fail "EBS storage not enabled"
fi

# -----------------------------------------------------------------------------
# Test 5: Encryption settings
# -----------------------------------------------------------------------------

log_info "Test: Encryption settings"

ENCRYPT_AT_REST=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.EncryptionAtRestOptions.Enabled')
N2N_ENCRYPTION=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.NodeToNodeEncryptionOptions.Enabled')
ENFORCE_HTTPS=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.DomainEndpointOptions.EnforceHTTPS')
TLS_POLICY=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.DomainEndpointOptions.TLSSecurityPolicy')

echo "  Encrypt at rest:   $ENCRYPT_AT_REST"
echo "  N2N encryption:    $N2N_ENCRYPTION"
echo "  Enforce HTTPS:     $ENFORCE_HTTPS"
echo "  TLS policy:        $TLS_POLICY"

if [ "$ENFORCE_HTTPS" = "true" ]; then
    log_pass "HTTPS enforced"
else
    log_fail "HTTPS not enforced"
fi

if [ "$TLS_POLICY" = "Policy-Min-TLS-1-2-2019-07" ] || [ "$TLS_POLICY" = "Policy-Min-TLS-1-2-PFS-2023-10" ]; then
    log_pass "TLS 1.2+ policy configured"
else
    log_fail "TLS policy is not TLS 1.2+: $TLS_POLICY"
fi

# -----------------------------------------------------------------------------
# Test 6: Access policy exists
# -----------------------------------------------------------------------------

log_info "Test: Access policy structure"

ACCESS_POLICY_RAW=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.AccessPolicies // empty')

if [ -z "$ACCESS_POLICY_RAW" ]; then
    log_fail "No access policy attached to domain"
    ACCESS_POLICY=""
elif ! ACCESS_POLICY=$(echo "$ACCESS_POLICY_RAW" | jq '.' 2>/dev/null); then
    log_fail "Access policy is not valid JSON"
    ACCESS_POLICY=""
else
    POLICY_STATEMENTS=$(echo "$ACCESS_POLICY" | jq '.Statement | length' 2>/dev/null)
    # Ensure POLICY_STATEMENTS is a valid non-negative integer
    if ! [[ "$POLICY_STATEMENTS" =~ ^[0-9]+$ ]]; then
        POLICY_STATEMENTS=0
    fi
    echo "  Policy statements: $POLICY_STATEMENTS"

    if [ "$POLICY_STATEMENTS" -gt 0 ]; then
        log_pass "Access policy has $POLICY_STATEMENTS statement(s)"

        # List statement SIDs (subshell is fine here, just printing)
        echo "$ACCESS_POLICY" | jq -r '.Statement[].Sid // "unnamed"' | while read -r sid; do
            echo "    - $sid"
        done
    else
        log_fail "Access policy has no statements"
    fi
fi

# -----------------------------------------------------------------------------
# Test 7: AdminAccess policy statement
# -----------------------------------------------------------------------------

log_info "Test: AdminAccess policy statement"

if [ -z "$ACCESS_POLICY" ]; then
    log_skip "AdminAccess statement (no valid policy)"
else
    ADMIN_STMT=$(echo "$ACCESS_POLICY" | jq -c '[.Statement[] | select(.Sid == "AdminAccess")][0] // empty' 2>/dev/null)

    if [ -n "$ADMIN_STMT" ] && [ "$ADMIN_STMT" != "null" ]; then
        ADMIN_ACTIONS=$(echo "$ADMIN_STMT" | jq -r '.Action | if type == "array" then .[] else . end')
        echo "  Actions: $ADMIN_ACTIONS"

        if echo "$ADMIN_ACTIONS" | grep -Fq "es:*"; then
            log_pass "AdminAccess has full es:* permissions"
        else
            log_fail "AdminAccess missing es:* permissions"
        fi
    else
        log_skip "AdminAccess statement not found (may not be configured)"
    fi
fi

# -----------------------------------------------------------------------------
# Test 8: ReadOnlyAccess policy statement
# -----------------------------------------------------------------------------

log_info "Test: ReadOnlyAccess policy statement"

if [ -z "$ACCESS_POLICY" ]; then
    log_skip "ReadOnlyAccess statement (no valid policy)"
else
    READONLY_STMT=$(echo "$ACCESS_POLICY" | jq -c '[.Statement[] | select(.Sid == "ReadOnlyAccess")][0] // empty' 2>/dev/null)

    if [ -n "$READONLY_STMT" ] && [ "$READONLY_STMT" != "null" ]; then
        READONLY_ACTIONS=$(echo "$READONLY_STMT" | jq -r '.Action | if type == "array" then .[] else . end')
        echo "  Actions: $READONLY_ACTIONS"

        # Check it has GET but not POST/DELETE (actions include es: prefix)
        if echo "$READONLY_ACTIONS" | grep -Fq "es:ESHttpGet"; then
            if echo "$READONLY_ACTIONS" | grep -Fq "es:ESHttpPost" || echo "$READONLY_ACTIONS" | grep -Fq "es:ESHttpDelete"; then
                log_fail "ReadOnlyAccess has write permissions (should be read-only)"
            else
                log_pass "ReadOnlyAccess has read-only permissions"
            fi
        else
            log_fail "ReadOnlyAccess missing es:ESHttpGet permission"
        fi
    else
        log_skip "ReadOnlyAccess statement not found (may not be configured)"
    fi
fi

# -----------------------------------------------------------------------------
# Test 9: Policy resource ARN format
# -----------------------------------------------------------------------------

log_info "Test: Policy resource ARN format"

if [ -z "$ACCESS_POLICY" ]; then
    log_skip "Policy resource ARN format (no valid policy)"
else
    RESOURCES=$(echo "$ACCESS_POLICY" | jq -r '.Statement[].Resource | if type == "array" then .[] else . end' 2>/dev/null)

    # Check for unsubstituted placeholders
    PLACEHOLDER_FOUND=false
    while IFS= read -r resource; do
        # Skip empty lines
        [ -z "$resource" ] && continue
        if [[ "$resource" == *"{account_id}"* ]] || [[ "$resource" == *"{region}"* ]] || [[ "$resource" == *"{domain_name}"* ]]; then
            echo "  Bad resource: $resource"
            PLACEHOLDER_FOUND=true
        fi
    done <<< "$RESOURCES"

    if [ "$PLACEHOLDER_FOUND" = true ]; then
        log_fail "Policy contains unsubstituted placeholders"
    else
        log_pass "Policy resource ARNs are fully resolved"
    fi
fi

# -----------------------------------------------------------------------------
# Test 10: SSM parameter - domain_name
# -----------------------------------------------------------------------------

log_info "Test: SSM parameter - domain_name"

SSM_DOMAIN_NAME_PATH="/pds/${COMPONENT_NAME}/opensearch_managed/domain_name"
if SSM_DOMAIN_NAME=$(aws ssm get-parameter \
    --name "$SSM_DOMAIN_NAME_PATH" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text 2>&1); then
    echo "  Path:  $SSM_DOMAIN_NAME_PATH"
    echo "  Value: $SSM_DOMAIN_NAME"

    if [ "$SSM_DOMAIN_NAME" = "$DOMAIN_NAME" ]; then
        log_pass "SSM domain_name matches actual domain"
    else
        log_fail "SSM domain_name ($SSM_DOMAIN_NAME) != actual domain ($DOMAIN_NAME)"
    fi
else
    SSM_DOMAIN_NAME=""
    log_skip "SSM parameter not found: $SSM_DOMAIN_NAME_PATH"
fi

# -----------------------------------------------------------------------------
# Test 11: SSM parameter - domain_arn
# -----------------------------------------------------------------------------

log_info "Test: SSM parameter - domain_arn"

SSM_DOMAIN_ARN_PATH="/pds/${COMPONENT_NAME}/opensearch_managed/domain_arn"
if SSM_DOMAIN_ARN=$(aws ssm get-parameter \
    --name "$SSM_DOMAIN_ARN_PATH" \
    --region "$REGION" \
    --query 'Parameter.Value' \
    --output text 2>&1); then
    echo "  Path:  $SSM_DOMAIN_ARN_PATH"
    echo "  Value: $SSM_DOMAIN_ARN"

    ACTUAL_ARN=$(echo "$DOMAIN_INFO" | jq -r '.DomainStatus.ARN')

    if [ "$SSM_DOMAIN_ARN" = "$ACTUAL_ARN" ]; then
        log_pass "SSM domain_arn matches actual domain ARN"
    else
        log_fail "SSM domain_arn ($SSM_DOMAIN_ARN) != actual ARN ($ACTUAL_ARN)"
    fi
else
    SSM_DOMAIN_ARN=""
    log_skip "SSM parameter not found: $SSM_DOMAIN_ARN_PATH"
fi

# -----------------------------------------------------------------------------
# Test 12: Cross-reference - SSM -> Domain lookup
# -----------------------------------------------------------------------------

log_info "Test: Cross-reference - SSM domain name resolves to real domain"

if [ -z "$SSM_DOMAIN_NAME" ]; then
    log_skip "SSM domain_name not available for cross-reference test"
elif CROSS_REF_INFO=$(aws opensearch describe-domain \
    --domain-name "$SSM_DOMAIN_NAME" \
    --region "$REGION" \
    --output json 2>&1); then
    CROSS_REF_ARN=$(echo "$CROSS_REF_INFO" | jq -r '.DomainStatus.ARN')
    echo "  SSM domain_name -> describe-domain -> ARN: $CROSS_REF_ARN"

    if [ -n "$SSM_DOMAIN_ARN" ] && [ "$CROSS_REF_ARN" = "$SSM_DOMAIN_ARN" ]; then
        log_pass "SSM -> Domain -> ARN chain is consistent"
    elif [ -z "$SSM_DOMAIN_ARN" ]; then
        log_pass "SSM domain_name resolves to valid domain (ARN param not available for cross-check)"
    else
        log_fail "SSM ARN ($SSM_DOMAIN_ARN) != looked-up ARN ($CROSS_REF_ARN)"
    fi
else
    log_fail "Could not describe domain from SSM-stored name: $CROSS_REF_INFO"
fi

# -----------------------------------------------------------------------------
# Test 13: IAM role SSM parameters - node-limited-writer
# -----------------------------------------------------------------------------

log_info "Test: IAM role SSM parameters - node-limited-writer"

NODE_WRITER_PATH="/pds/cds-infra/iam/roles/pds-node-limited-writer"
NODE_WRITER_PARAMS=$(aws ssm get-parameters-by-path \
    --path "$NODE_WRITER_PATH" \
    --region "$REGION" \
    --query 'Parameters[].Name' \
    --output text 2>&1) || NODE_WRITER_PARAMS=""

if [ -n "$NODE_WRITER_PARAMS" ]; then
    NODE_WRITER_COUNT=$(echo "$NODE_WRITER_PARAMS" | wc -w | tr -d ' ')
    log_pass "node-limited-writer SSM params exist ($NODE_WRITER_COUNT nodes)"
    echo "  Path: $NODE_WRITER_PATH"
    for param in $NODE_WRITER_PARAMS; do
        node_name=$(basename "$param")
        echo "    - $node_name"
    done
else
    log_fail "No node-limited-writer SSM params found at $NODE_WRITER_PATH"
    echo "  These are required for per-node access policies"
fi

# -----------------------------------------------------------------------------
# Test 14: IAM role SSM parameters - core-cloudops
# -----------------------------------------------------------------------------

log_info "Test: IAM role SSM parameters - core-cloudops"

CLOUDOPS_PATH="/pds/cds-infra/iam/roles/pds-core-cloudops"
CLOUDOPS_PARAMS=$(aws ssm get-parameters-by-path \
    --path "$CLOUDOPS_PATH" \
    --region "$REGION" \
    --query 'Parameters[].Name' \
    --output text 2>&1) || CLOUDOPS_PARAMS=""

if [ -n "$CLOUDOPS_PARAMS" ]; then
    CLOUDOPS_COUNT=$(echo "$CLOUDOPS_PARAMS" | wc -w | tr -d ' ')
    log_pass "core-cloudops SSM params exist ($CLOUDOPS_COUNT nodes)"
    echo "  Path: $CLOUDOPS_PATH"
    for param in $CLOUDOPS_PARAMS; do
        node_name=$(basename "$param")
        echo "    - $node_name"
    done
else
    log_fail "No core-cloudops SSM params found at $CLOUDOPS_PATH"
    echo "  These roles are not yet provisioned in pds-cds-infra/iam/roles"
    echo "  When created, they will automatically be included in the access policy"
fi

# -----------------------------------------------------------------------------
# Test 15: Endpoint reachability (optional)
# -----------------------------------------------------------------------------

if [ "$SKIP_SMOKE" = true ]; then
    log_skip "Endpoint reachability (--skip-smoke)"
elif [ -z "$ENDPOINT" ]; then
    log_skip "Endpoint reachability (no endpoint available)"
else
    log_info "Test: Endpoint reachability"

    # Try to reach the endpoint (may fail due to VPC/auth restrictions)
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 5 \
        "https://${ENDPOINT}/" 2>/dev/null || echo "000")

    if [ "$HEALTH_CHECK" = "200" ] || [ "$HEALTH_CHECK" = "401" ] || [ "$HEALTH_CHECK" = "403" ]; then
        # 401/403 means endpoint is reachable but needs auth (expected)
        log_pass "Domain endpoint is reachable (HTTP $HEALTH_CHECK)"

        if [ "$HEALTH_CHECK" = "401" ] || [ "$HEALTH_CHECK" = "403" ]; then
            echo "  Note: Auth required - full data test would need IAM credentials"
        fi
    elif [ "$HEALTH_CHECK" = "000" ]; then
        log_skip "Domain endpoint not reachable (VPC-only or network issue)"
    else
        log_fail "Unexpected response from endpoint: HTTP $HEALTH_CHECK"
    fi
fi

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------

echo ""
echo "=============================================="
echo " Test Summary"
echo "=============================================="
echo ""
echo -e "  ${GREEN}Passed:${NC}  $TESTS_PASSED"
echo -e "  ${RED}Failed:${NC}  $TESTS_FAILED"
echo -e "  ${YELLOW}Skipped:${NC} $TESTS_SKIPPED"
echo ""

if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi
