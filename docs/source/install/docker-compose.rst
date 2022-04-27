=================================
Docker Container Based Deployment
=================================

Overview
********

All the PDS Registry components are containerized as docker images and published in https://hub.docker.com/u/nasapds.

The container based deployment of the PDS Registry components is orchestrated by Docker Compose, a tool for defining and running multi-container Docker applications.

Therefore, the deployment procedures described here can be used to deploy server-side and/or client-side registry components, without having to install the individual components manually.

.. warning::
 these deployment are not intended for production given that 1. docker compose works on a single host and 2. permanent storage is left to docker to manage.

.. note::
    To learn more about docker compose, please visit https://docs.docker.com/compose/.

Prerequisites
*************

It is required to install the following tools.

    * **docker** Can be downloaded installed as explained in https://docs.docker.com/get-docker/

    * **docker compose** Can be downloaded and installed as explained in https://docs.docker.com/compose/install/

.. note::
    At the time of writing this, all registry components were successfully tested with the docker compose version v2.2.3.
    The registry components should work with later versions of docker compose too.

Download and Configure the PDS Registry Application
****************************************************

The latest release of the Registry can be downloaded and configured as follows.

1. Download the sourcecode `.zip` file or `.tar.gz` file from the https://github.com/NASA-PDS/registry/releases.

2. Extract the **tar** (Linux, Mac) or **zip** (Windows) to a directory without spaces, such as */home/pds*.
On Linux you can use the following command::

    % tar -xzvf registry-x.y.z.tar.gz

.. Note::
    The path of the extracted directory, is referred to as the `<REGISTRY_ROOT>` in the following instructions.

3. Open a terminal and change the working directory to `<REGISTRY_ROOT>/docker` directory.

4. Open the `<REGISTRY_ROOT>/docker/.env` file using a text editor

5. Edit the `.env` file and set the following environment variables. ::

    # Absolute path of the Harvest data directory in the host machine (E.g.: `./test-data/registry-harvest-data`).
    # If the Registry Harvest CLI is executed with the option to download test data, then this directory will be
    # cleaned-up and populated with test data.
    # Also, this `HARVEST_DATA_DIR` location should be accessible from the docker containers of the Registry Harvest Service
    # and Registry Crawler Service.
    HARVEST_DATA_DIR=./test-data/registry-harvest-data

    # Absolute path of the Harvest job file in the host machine (E.g.: ./default-config/harvest-job-config.xml)
    HARVEST_JOB_CONFIG_FILE=./default-config/harvest-job-config.xml

.. note::
    The `HARVEST_DATA_DIR` specified above should have the directories of the data to be harvested.

    An example of a `harvest-job-config.xml` file (to set as `HARVEST_JOB_CONFIG_FILE` in the above configurations)
    can be obtained from the `<REGISTRY_ROOT>/docker/default-config` directory.

5. Generate the self-signed certificates as follows.


.. note::
    Certificates are required for OpenSearch to enable https.
..

    a) Change the current working directory to `<REGISTRY_ROOT>/docker/certs` directory. ::

        cd certs

    b) Generate self-signed certificates by executing the following script. ::

        ./generate-certs.sh

    c) Change the current working directory to `<REGISTRY_ROOT>/docker` directory. ::

        cd ..

Deployment profiles
****************************

Deployment profiles are defined to parameterize your deployment, either you only want to run the server side core components of the registry (OpenSearch and web API) or run an harvest standalone job, or run the scalable harvest services.

Using a profile name, you can start only the required components of the Registry as follows. ::

    docker compose --profile=<DOCKER_COMPOSE_PROFILE_NAME> up --detach

.. note::
    The next section explains the possible profile names that can be used for the `<DOCKER_COMPOSE_PROFILE_NAME>` in the
    docker compose command above.

The docker containers deployed using a docker compose profile can be easily uninstalled and cleaned-up using the following
command::

    docker compose --profile=<DOCKER_COMPOSE_PROFILE_NAME> down


The following table contains commonly used and production ready server-side profiles and descriptions.

====================== ==================================================== ==============================================
 Profile Name           Description                                          Prerequisites

                                                                             (profiles to start before this)

====================== ==================================================== ==============================================
 pds-core-registry      Starts only the OpenSearch and Registry API          None
 pds-loader-services    Starts the Scalable Harvest server-side components   The `pds-core-registry` profile
                                                                             must be up and running
====================== ==================================================== ==============================================


Client-side operations
****************************


To ingest data in the registry, you need to run client side command (which use docker compose as well internally)

================================================ ==================================================== ==============================================
 Command prototype                                 Description                                          Prerequisites

                                                                                                        (profiles to start before this)

================================================ ==================================================== ==============================================
 pds-batch-loader.sh  <harvest job confg file>     Executes the Standalone Harvest client-side tool.    The `pds-core-registry` server-side profile
                                                   This tool is recommended for small data sets of      must be up and running
                                                   up to 10,000 PDS4 labels.
 pds-service-loader.sh <harvest job confg file>    Executes the Scalable Harvest client-side tool.      The `pds-service-loader` server-side profile
                                                   This tool is   recommended for larger data sets of   must be up and running
                                                   over 10,000 PDS4 labels.
================================================ ==================================================== ==============================================


Common deployment scenarii
****************************


Core Registry with Standalone Harvest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As explained above, the Standalone Harvest is a simplified deployment, which is suitable to process smaller data sets of
up to 10,000 PDS4 labels.

You can execute the following instructions to deploy the server-side and client-side components of Standalone Harvest.

Deploying the Sever-side Components of Standalone Harvest
----------------------------------------------------------

1) Open a new terminal and change the current working directory to the `<REGISTRY_ROOT>/docker` directory.

2) Start the `pds-core-registry` components as follows. ::

    docker compose --profile=pds-core-registry  up

3) Wait for the following log messages in the terminal. ::

    docker-registry-api-1        |   .   ____          _            __ _ _
    docker-registry-api-1        |  /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
    docker-registry-api-1        | ( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
    docker-registry-api-1        |  \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
    docker-registry-api-1        |   '  |____| .__|_| |_|_| |_\__, | / / / /
    docker-registry-api-1        |  =========|_|==============|___/=/_/_/_/
    docker-registry-api-1        |  :: Spring Boot ::        (v2.3.1.RELEASE)
    docker-registry-api-1        |

Deploying the Client-side Components of Standalone Harvest
-----------------------------------------------------------

1) Open a new terminal and change the current working directory to the `<REGISTRY_ROOT>/docker` directory.

2) Start the `pds-core-registry` components as follows. ::

    docker compose --profile=pds-batch-loader  up

3) Wait for the following log messages in the terminal. ::

    docker-registry-loader-1 exited with code 0

4) Visit the http://localhost:8080/swagger-ui.html#!/collections/getCollection of the Registry API.

5) Click on the **Try it out!** button to see the Response Body.


Clean-up the Deployment
------------------------

The docker containers deployed above can be easily uninstalled and cleaned-up using the following
commands::

    docker compose --profile=pds-core-registry down

    docker compose --profile=pds-batch-loader down


Core registry with Scalable Harvest
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As explained above, the Scalable Harvest is suitable to process larger data sets of more than 10,000 PDS4 labels.

You can execute the following instructions to deploy the server-side and client-side components of Scalable Harvest.

Deploying the Sever-side Components of Scalable Harvest
--------------------------------------------------------

1) Open a new terminal and change the current working directory to the `<REGISTRY_ROOT>/docker` directory.

2) Start the `pds-core-registry` components as follows. ::

    docker compose --profile=pds-core-registry  up

3) Wait for the following log messages in the terminal. ::

    docker-registry-api-1        |   .   ____          _            __ _ _
    docker-registry-api-1        |  /\\ / ___'_ __ _ _(_)_ __  __ _ \ \ \ \
    docker-registry-api-1        | ( ( )\___ | '_ | '_| | '_ \/ _` | \ \ \ \
    docker-registry-api-1        |  \\/  ___)| |_)| | | | | || (_| |  ) ) ) )
    docker-registry-api-1        |   '  |____| .__|_| |_|_| |_\__, | / / / /
    docker-registry-api-1        |  =========|_|==============|___/=/_/_/_/
    docker-registry-api-1        |  :: Spring Boot ::        (v2.3.1.RELEASE)
    docker-registry-api-1        |

4) Start the `pds-loader-services` components as follows to start Scalable Harvest components. ::

    docker compose --profile=pds-loader-services up


Deploying the Client-side Components of Standalone Harvest
-----------------------------------------------------------

1) Open a new terminal and change the current working directory to the `<REGISTRY_ROOT>/docker` directory.

2) Start the `pds-service-loader` components as follows. ::

    docker compose --profile=pds-service-loader up

3) Wait for the following log messages in the terminal. ::

    docker-registry-harvest-cli-1 exited with code 0

4) Visit the http://localhost:8080/swagger-ui.html#!/collections/getCollection of the Registry API.

5) Click on the **Try it out!** button to see the Response Body.

Clean-up the Deployment
------------------------

The docker containers deployed above can be easily uninstalled and cleaned-up using the following
commands::

    docker compose --profile=pds-core-registry down

    docker compose --profile=pds-loader-services down

    docker compose --profile=pds-service-loader down



.. note::
    In addition to the commonly used and production ready docker compose profiles explained above, there are several other
    docker compose profile that are used to setup the development environment and execute integration tests.

    More information about all currently available docker compose profiles are available at
    https://github.com/NASA-PDS/registry/tree/main/docker#-docker-compose-for-registry-components.
