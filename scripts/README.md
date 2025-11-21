# Registry Utility Scripts

This directory contains utility scripts for managing and reporting on the PDS Registry.

## Available Scripts

### Missing Products Report Generator

Generate CSV reports identifying missing bundles and collections in the PDS Registry.

**Script:** `generate_missing_products_report.py`

#### Purpose

This script queries the PDS Registry OpenSearch instance to identify Product_Bundle and Product_Collection records that are marked as missing (`found_in_registry: false`). This helps track data gaps and identify products that need to be ingested into the registry.

#### Requirements

- Python 3.12 or higher
- `pds-registry-client` - Install with: `pip install pds-registry-client`
- Access credentials to the PDS Registry OpenSearch instance

#### Configuration

The script requires these environment variables for authentication:

- `REQUEST_SIGNER_AWS_ACCOUNT`
- `REQUEST_SIGNER_AWS_REGION`
- `REQUEST_SIGNER_CLIENT_ID`
- `REQUEST_SIGNER_USER_POOL_ID`
- `REQUEST_SIGNER_IDENTITY_POOL_ID`
- `REQUEST_SIGNER_AOSS_ENDPOINT`
- `REQUEST_SIGNER_COGNITO_USER`
- `REQUEST_SIGNER_COGNITO_PASSWORD`

**Environment File Locations (checked in order):**
1. `$HOME/.pds/.registry-client` (recommended for personal credentials)
2. `./.env` (repository root)

**Example `.env` file:**
```bash
export REQUEST_SIGNER_AWS_ACCOUNT='your_aws_account_id'
export REQUEST_SIGNER_AWS_REGION='us-west-2'
export REQUEST_SIGNER_CLIENT_ID='your_cognito_client_id'
export REQUEST_SIGNER_USER_POOL_ID='your_user_pool_id'
export REQUEST_SIGNER_IDENTITY_POOL_ID='your_identity_pool_id'
export REQUEST_SIGNER_AOSS_ENDPOINT='https://your-opensearch-endpoint.amazonaws.com'
export REQUEST_SIGNER_COGNITO_USER='your_username'
export REQUEST_SIGNER_COGNITO_PASSWORD='your_password'
```

⚠️ **Security:** Never commit your `.env` file with real credentials to version control!

#### Usage

Run from the repository root:

```bash
# Generate reports and commit/push to GitHub (default behavior)
./scripts/generate_missing_products_report.py

# Generate reports only, without committing to git
./scripts/generate_missing_products_report.py --no-commit

# Show help
./scripts/generate_missing_products_report.py --help
```

**Note:** By default, the script will commit and push the generated CSV files to GitHub. Use the `--no-commit` flag to disable this behavior.

#### Output

Generates two CSV files in `docs/status/`:

1. **`missing_bundles_in_registry.csv`** - Missing Product_Bundle records
2. **`missing_collections_in_registry.csv`** - Missing Product_Collection records

**CSV Format:**
```
"NODE_ID","LIDVID","PRODUCT_CLASS"
```

**Example:**
```
"PDS_PPI","urn:nasa:pds:maven.rose.raw::1.21","Product_Bundle"
"PDS_ENG","urn:nasa:pds:context::1.2","Product_Bundle"
```

#### How It Works

1. Loads environment variables from `.env` file (if present)
2. Verifies all required authentication variables are set
3. Executes OpenSearch DSL queries using `pds-registry-client` from:
   - `conf/missing_bundles_per_node.json`
   - `conf/missing_collections_per_node.json`
4. Queries the `/en-legacy-registry/_search` endpoint
5. Transforms JSON responses into CSV format
6. Saves results to `docs/status/`
7. Commits and pushes changes to GitHub (unless `--no-commit` is specified)

#### Query Details

Both queries:
- Return up to 2000 results per query
- Filter by `product_class` (Product_Bundle or Product_Collection)
- Filter by `found_in_registry: false`
- Return only `node`, `lidvid`, and `product_class` fields

#### Troubleshooting

**"pds-registry-client command not found"**
```bash
pip install pds-registry-client
```

**"Missing required environment variables"**

Ensure you have a `.env` file with all required variables at either:
- `$HOME/.pds/.registry-client` (recommended), or
- Repository root `./.env`

**Authentication errors**

Verify your credentials are correct in the `.env` file. Contact PDS operations if you need access credentials.
