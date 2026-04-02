#!/usr/bin/env bash
# Script to initialize AWS-deployed registry with test data
# This script:
# 1. Extracts Terraform outputs (OpenSearch endpoint, credentials endpoint)
# 2. Runs registry-loader-test-init container to load test data into AWS

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR}/../docker"

echo "=========================================="
echo "AWS Registry Initialization Script"
echo "=========================================="
echo ""

# Check if we're in the terraform directory
if [ ! -f "${SCRIPT_DIR}/main.tf" ]; then
    echo "Error: This script must be run from the terraform directory or main.tf must exist"
    exit 1
fi

# Check if terraform has been applied
if ! terraform output collection_endpoint &>/dev/null; then
    echo "Error: Terraform outputs not found. Have you run 'terraform apply'?"
    exit 1
fi

# Extract Terraform outputs
echo "📋 Extracting Terraform outputs..."
OPENSEARCH_ENDPOINT=$(terraform output -raw collection_endpoint)
CREDENTIALS_ENDPOINT=$(terraform output -raw credentials_endpoint)
echo $CREDENTIALS_ENDPOINT
#CREDENTIALS_ENDPOINT=https://c8u1zk30u5.execute-api.us-west-2.amazonaws.com/dev/credentials

# Extract AWS region from the OpenSearch endpoint
AWS_REGION=$(echo "${OPENSEARCH_ENDPOINT}" | sed -n 's/.*\.\([a-z0-9-]*\)\.aoss\.amazonaws\.com.*/\1/p')
if [ -z "${AWS_REGION}" ]; then
    echo "Error: Could not extract AWS region from OpenSearch endpoint"
    exit 1
fi

# Generate Cognito IDP URL from region
COGNITO_IDP_URL="https://cognito-idp.${AWS_REGION}.amazonaws.com"

echo "   OpenSearch Endpoint: ${OPENSEARCH_ENDPOINT}"
echo "   Credentials Endpoint: ${CREDENTIALS_ENDPOINT}"
echo "   REGISTRY Name: ${NODE_REGISTRY}"
echo "   AWS Region: ${AWS_REGION}"
echo "   Cognito IDP URL: ${COGNITO_IDP_URL}"
echo ""

# Check if credentials endpoint is accessible (optional, you might need auth)
echo "🔐 Note: Make sure you have AWS credentials configured for accessing the OpenSearch endpoint"
echo ""

# Check for required Cognito credentials
if [ -z "${COGNITO_ADMIN_USERNAME:-}" ]; then
    echo "Error: COGNITO_ADMIN_USERNAME environment variable is not set"
    echo "Please export COGNITO_ADMIN_USERNAME before running this script"
    exit 1
fi

if [ -z "${COGNITO_ADMIN_PASSWORD:-}" ]; then
    echo "Error: COGNITO_ADMIN_PASSWORD environment variable is not set"
    echo "Please export COGNITO_ADMIN_PASSWORD before running this script"
    exit 1
fi

if [ -z "${COGNITO_WRITER_USERNAME:-}" ]; then
    echo "Error: COGNITO_WRITER_USERNAME environment variable is not set"
    echo "Please export COGNITO_WRITER_USERNAME before running this script"
    exit 1
fi

if [ -z "${COGNITO_WRITER_PASSWORD:-}" ]; then
    echo "Error: COGNITO_WRITER_PASSWORD environment variable is not set"
    echo "Please export COGNITO_WRITER_PASSWORD before running this script"
    exit 1
fi

if [ -z "${COGNITO_CLIENT_ID:-}" ]; then
    echo "Error: COGNITO_CLIENT_ID environment variable is not set"
    echo "Please export COGNITO_CLIENT_ID before running this script"
    exit 1
fi

echo "   Using Cognito credentials for user: ${COGNITO_ADMIN_USERNAME}"
echo "   Cognito Client ID: ${COGNITO_CLIENT_ID}"
echo ""

# Check if Docker is running
if ! docker info &>/dev/null; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
fi

# Load environment variables from .env file
if [ -f "${DOCKER_DIR}/.env" ]; then
    echo "📄 Loading environment variables from .env file..."
    set -a
    source "${DOCKER_DIR}/.env"
    set +a
else
    echo "⚠️  Warning: .env file not found, using default values"
    REG_LOADER_IMAGE=${REG_LOADER_IMAGE:-nasapds/registry-loader:latest}
    TEST_DATA_URL=${TEST_DATA_URL:-https://github.com/NASA-PDS/registry-ref-data/releases/download/Latest/custom-datasets.tar.gz}
    TEST_DATA_LIDVID=${TEST_DATA_LIDVID:-"urn:nasa:pds:mars2020.spice::1.0 urn:nasa:pds:mars2020.spice::2.0 urn:nasa:pds:mars2020.spice::3.0"}
    CONTAINER_HARVEST_DATA_DIR=${CONTAINER_HARVEST_DATA_DIR:-/data}
    REG_DATA_VOLUME=${REG_DATA_VOLUME:-data-volume}
fi

echo ""

# Generate registry connection XML configuration
mkdir -p "${SCRIPT_DIR}/.registry-loader"
REGISTRY_CONFIG_FILE="${SCRIPT_DIR}/.registry-loader/registry-connection.xml"
echo "📝 Generating registry connection configuration..."
cat > "${REGISTRY_CONFIG_FILE}" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<registry_connection index="${NODE_REGISTRY}">
  <cognitoClientId endpoint="${OPENSEARCH_ENDPOINT}"
                   gateway="${CREDENTIALS_ENDPOINT}"
                   IDP="${COGNITO_IDP_URL}">${COGNITO_CLIENT_ID}</cognitoClientId>
</registry_connection>
EOF

echo "   Created: ${REGISTRY_CONFIG_FILE}"
echo ""

# Generate es-auth.cfg with Cognito credentials
TEMP_ES_COGNITO_ADMIN_AUTH_CFG="${SCRIPT_DIR}/.registry-loader/es-admin-auth.cfg"
echo "📝 Generating temporary es-auth.cfg with Cognito credentials..."
cat > "${TEMP_ES_COGNITO_ADMIN_AUTH_CFG}" << EOF
# Generated es-auth.cfg for AWS Cognito authentication
# Generated at: $(date)
user = ${COGNITO_ADMIN_USERNAME}
password = ${COGNITO_ADMIN_PASSWORD}
EOF

echo "   Created temporary auth config: ${TEMP_ES_COGNITO_ADMIN_AUTH_CFG}"
echo ""

# Generate es-auth.cfg with Cognito credentials
TEMP_ES_COGNITO_WRITER_AUTH_CFG="${SCRIPT_DIR}/.registry-loader/es-writer-auth.cfg"
echo "📝 Generating temporary es-auth.cfg with Cognito credentials..."
cat > "${TEMP_ES_COGNITO_WRITER_AUTH_CFG}" << EOF
# Generated es-auth.cfg for AWS Cognito authentication
# Generated at: $(date)
user = ${COGNITO_WRITER_USERNAME}
password = ${COGNITO_WRITER_PASSWORD}
EOF

echo "   Created temporary auth config: ${TEMP_ES_COGNITO_ADMIN_AUTH_CFG}"
echo ""

# Run registry-loader-test-init
echo "🚀 Running registry-manager create-registry..."
echo "   This will download test data and load it into AWS OpenSearch"
echo "   Image: ${REG_LOADER_IMAGE}"
echo "   Test Data: ${TEST_DATA_URL}"
echo ""
echo "📋 Container logs:"
echo "----------------------------------------"

docker run --rm -it \
    -v "${SCRIPT_DIR}/.registry-loader:/config" \
    -e "REGISTRY_CONFIG=registry-connection.xml" \
    -e "AUTH_CONFIG=es-auth.cfg" \
    "${REG_LOADER_IMAGE}" \
    registry-manager create-registry


echo "----------------------------------------"

# Run harvest job to load test data
echo "🚀 Running harvest..."
echo "   This will download test data and load it into AWS OpenSearch"
echo "   Image: ${REG_LOADER_IMAGE}"
echo "   Test Data: ${TEST_DATA_URL}"
echo ""
echo "📋 Container logs:"
echo "----------------------------------------"

docker run --rm -it \
    -v "${SCRIPT_DIR}/.registry-loader:/config" \
    -e "REGISTRY_CONFIG=registry-connection.xml" \
    -e "AUTH_CONFIG=es-auth.cfg" \
    "${REG_LOADER_IMAGE}" \
    harvest -c /config/harvest-job-config.xml


echo "----------------------------------------"

# Clean up temporary file
rm -f "${TEMP_ES_COGNITO_ADMIN_AUTH_CFG}"
rm -f "${TEMP_ES_COGNITO_WRITER_AUTH_CFG}"
echo "   Cleaned up temporary auth config"

echo ""
echo "=========================================="
echo "✅ Initialization complete!"
echo "=========================================="
echo ""
echo "Your AWS OpenSearch collection should now be populated with test data."
echo ""
echo "Configuration files:"
echo "   Registry connection: ${REGISTRY_CONFIG_FILE}"
echo ""
echo "Connection details:"
echo "   OpenSearch Endpoint: ${OPENSEARCH_ENDPOINT}"
echo "   Credentials Endpoint: ${CREDENTIALS_ENDPOINT}"
echo "   Collection/Index: ${COLLECTION_NAME}"
echo ""
