
# 🪐 NASA PDS Registry repository

[![DOI](https://zenodo.org/badge/419869439.svg)](https://zenodo.org/doi/10.5281/zenodo.6724814) [![🤪 Unstable integration & delivery](https://github.com/NASA-PDS/registry/actions/workflows/unstable-cicd.yaml/badge.svg)](https://github.com/NASA-PDS/registry/actions/workflows/unstable-cicd.yaml) [![😌 Stable integration & delivery](https://github.com/NASA-PDS/registry/actions/workflows/stable-cicd.yaml/badge.svg)](https://github.com/NASA-PDS/registry/actions/workflows/stable-cicd.yaml)

This repository is an umbrella for the PDS registry application. The application is composed of multiple sub-components, each of them managed in their own repository and integrated here:

- registry-loader: tools to load PDD4 producs to the registry
- opensearch: the famoua data store and search engine which performaces we praise.s
- registry-sweepers: suite of script consolidating the PDS4 product descriptions in OpenSearch.
- registry-api: the PDS Search API service.
- registry-ref-data: some reference datsets that we use for our application integration tests.


Users and administrator should use the documentation published on http://nasa-pds.github.io/registry

This repository specifically contains these PDS registry application resources:

- the source for the user/administrator documentation, see `docs` folder
- docker compose script to start/test the full application with its required components, see https://github.com/NASA-PDS/registry/blob/main/docker/README.md for details. This also includes integration tests (in `docker/postman`). The integration test datasets are maintained in NASA-PDS/registry-ref-data repository.
- **For developers:** See [Integration Testing Guide](https://nasa-pds.github.io/registry/developer/integration-testing.html) for instructions on adding and running integration tests.
- utility scripts for registry management and reporting, see `scripts` folder


## Code of Conduct

All users and developers of the NASA-PDS software are expected to abide by our [Code of Conduct](https://github.com/NASA-PDS/.github/blob/main/CODE_OF_CONDUCT.md). Please read this to ensure you understand the expectations of our community.


## Scripts

### Missing Products Report Generator

Generate CSV reports for missing bundles and collections in the PDS Registry:

```bash
# Generate reports and commit/push to GitHub (default)
./scripts/generate_missing_products_report.py

# Generate reports only, without committing
./scripts/generate_missing_products_report.py --no-commit
```

**Purpose:** Identifies Product_Bundle and Product_Collection records marked as missing in the registry.

**Output:** Creates CSV files in `docs/status/`:
- `missing_bundles_in_registry.csv`
- `missing_collections_in_registry.csv`

By default, the script commits and pushes these files to GitHub. Use `--no-commit` to disable this.

**Requirements:**
- Python 3.12 or higher
- `pds-registry-client` and PDS Registry credentials
- See `scripts/README.md` for full configuration details

## Utilities
* Treks
    * To deploy the package run one of these commands from the root directory:
        ```pip install .``` for users
        ```pip install -e '.[dev]'``` for developers
        * This package is also hosted on the "cheeseshop" and can be installed with
            ```pip install pds.registry```
    * The Treks utilities can be used to create pds4 labels for the layers given in the Treks API
    * Run the command:
        ```create-treks-pds4```

* GeoSTAC - Lola
    * To deploy the package run one of these commands from the root directory:
        ```pip install .``` for users
        ```pip install -e '.[dev]'``` for developers
        * This package is also hosted on the "cheeseshop" and can be installed with
            ```pip install pds.registry```
    * The GeoSTAC utilities can be used to create pds4 labels for the Lola point clouds they host
    * This command needs LOLA GDR data to be loaded in the registry in order to connect the lid references
        * This data can be found here: [https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/float_img/](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/float_img/)
    * Run the command:
        ```create-lola-pds4```


## Development

To develop this project, use your favorite text editor, or an integrated development environment with Python support, such as [PyCharm](https://www.jetbrains.com/pycharm/).


### Contributing

For information on how to contribute to NASA-PDS codebases please take a look at our [Contributing guidelines](https://github.com/NASA-PDS/.github/blob/main/CONTRIBUTING.md).


### Installation

Install in editable mode and with extra developer dependencies into your virtual environment of choice:

    pip install --editable '.[dev]'

Make a baseline for any secrets (email addresses, passwords, API keys, etc.) in the repository:

    detect-secrets scan . \
        --all-files \
        --disable-plugin AbsolutePathDetectorExperimental \
        --exclude-files '\.secrets..*' \
        --exclude-files '\.git.*' \
        --exclude-files '\.mypy_cache' \
        --exclude-files '\.pytest_cache' \
        --exclude-files '\.tox' \
        --exclude-files '\.venv' \
        --exclude-files 'venv' \
        --exclude-files 'dist' \
        --exclude-files 'build' \
        --exclude-files '.*\.egg-info' > .secrets.baseline

Review the secrets to determine which should be allowed and which are false positives:

    detect-secrets audit .secrets.baseline

Please remove any secrets that should not be seen by the public. You can then add the baseline file to the commit:

    git add .secrets.baseline

Then, configure the `pre-commit` hooks:

    pre-commit install
    pre-commit install -t pre-push
    pre-commit install -t prepare-commit-msg
    pre-commit install -t commit-msg

These hooks then will check for any future commits that might contain secrets. They also check code formatting, PEP8 compliance, type hints, etc.

👉 **Note:** A one time setup is required both to support `detect-secrets` and in your global Git configuration. See [the wiki entry on Secrets](https://github.com/NASA-PDS/nasa-pds.github.io/wiki/Git-and-Github-Guide#detect-secrets) to learn how.


### Documentation

The project uses [Sphinx](https://www.sphinx-doc.org/en/master/) to build its documentation. PDS' documentation template is already configured as part of the default build. You can build your projects docs with:


    cd docs
    make html

The generated documnentation can be found in directory docs/build/html


## CI/CD

The template repository comes with our two "standard" CI/CD workflows, `stable-cicd` and `unstable-cicd`. The unstable build runs on any push to `main` (± ignoring changes to specific files) and the stable build runs on push of a release branch of the form `release/<release version>`. Both of these make use of our GitHub actions build step, [Roundup](https://github.com/NASA-PDS/roundup-action). The `unstable-cicd` will generate (and constantly update) a SNAPSHOT release. If you haven't done a formal software release you will end up with a `v0.0.0-SNAPSHOT` release (see NASA-PDS/roundup-action#56 for specifics).
