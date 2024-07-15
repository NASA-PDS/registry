
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


## Code of Conduct

All users and developers of the NASA-PDS software are expected to abide by our [Code of Conduct](https://github.com/NASA-PDS/.github/blob/main/CODE_OF_CONDUCT.md). Please read this to ensure you understand the expectations of our community.


## Utilities
* Titan Treks
    * To deploy the package run one of these commands from the root directory:
        ```pip install .``` for users
        ```pip install -e '.[dev]'``` for developers
        * This package is also hosted on the "cheeseshop" and can be installed with
            ```pip install pds.registry```
    * The Titan Treks utilities can be used to create pds4 labels for the layers given in the Titan Treks API
    * Run the command:

        ```create-titan-treks-pds4```

    * `create-titan-treks-pds4` has 3 paramaters to customize the script
    `-d DEST, --destination-directory DEST` Destination to save the pds4 xml labels, default `xml_files/product_service`
    `-s, --save-xml` Save the xml files to the destination folder, deafult `True`
    `-v, --verbose` Verbose, default `False`
    * These can also be seen with the command:
        ```create-titan-treks-pds4 --help```


## Development

To develop this project, use your favorite text editor, or an integrated development environment with Python support, such as [PyCharm](https://www.jetbrains.com/pycharm/).


### Contributing

For information on how to contribute to NASA-PDS codebases please take a look at our [Contributing guidelines](https://github.com/NASA-PDS/.github/blob/main/CONTRIBUTING.md).


### Documentation

The project uses [Sphinx](https://www.sphinx-doc.org/en/master/) to build its documentation. PDS' documentation template is already configured as part of the default build. You can build your projects docs with:


    cd docs
    make html

The generated documnentation can be found in directory docs/build/html


## CI/CD

The template repository comes with our two "standard" CI/CD workflows, `stable-cicd` and `unstable-cicd`. The unstable build runs on any push to `main` (± ignoring changes to specific files) and the stable build runs on push of a release branch of the form `release/<release version>`. Both of these make use of our GitHub actions build step, [Roundup](https://github.com/NASA-PDS/roundup-action). The `unstable-cicd` will generate (and constantly update) a SNAPSHOT release. If you haven't done a formal software release you will end up with a `v0.0.0-SNAPSHOT` release (see NASA-PDS/roundup-action#56 for specifics).
