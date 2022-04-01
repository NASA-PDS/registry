=================================
Docker Container Based Deployment
=================================

Overview
********

Docker Compose is a tool for defining and running multi-container Docker applications. All registry components are
containerized as docker images and published in https://hub.docker.com/u/nasapds. Therefore, the docker compose tool
can be used to deploy the required registry components.

To learn more about docker compose, please refer to https://docs.docker.com/compose/.

Prerequisites
*************

Before using the docker compose, it is required to install the docker compose as explained in the following link.
https://docs.docker.com/compose/install/

At the time of writing this, all registry components were successfully tested with the docker compose version v2.2.3. The
registry components should work with later versions of docker compose too.

Download
********

The latest release of the registry can be downloaded from https://github.com/NASA-PDS/registry/releases.

1) Download the sourcecode `.zip` file or `.tar.gz` file from the https://github.com/NASA-PDS/registry/releases.

2) Extract the `.zip` file or `.tar.gz` into a local directory.

3) Open a terminal and change the working directory to `<REGISTRY_ROOT>/docker` directory.

4) Execute the docker compose command as follows.::

    docker compose --profile=<DOCKER_COMPOSE_PROFILE_NAME> up --detach

The following section explains the possible profile names that can be used for <DOCKER_COMPOSE_PROFILE_NAME> above.

Docker Compose Profile Names
****************************

All the required registry components (such as OpenSearch, RabbitMQ, Registry API) are defined as services in
the file `docker/docker-compose.yml`. In this file, each and every service (components) is tagged with a profile name.
There are multiple services associated with single profile.

Using a profile name, we can start only the required components of the registry.

Server-side Profiles
~~~~~~~~~~~~~~~~~~~~

The following table contains commonly used server-side profiles and descriptions.

====================== ==================================================== ===============================
 Profile Name           Description                                          Prerequisites
====================== ==================================================== ===============================
 pds-core-registry      Starts only the OpenSearch and Registry API          None
 pds-loader-services    Starts the Scalable Harvest server-side components   The `pds-core-registry` profile
                                                                             should be up and running
====================== ==================================================== ===============================

The `pds-core-registry` profile can be started as follows::
    docker compose --profile=pds-core-registry  up --detach

The `pds-loader-services` profile can be started as follows (make sure to start the
profile `pds-core-registry` before starting this)::
    docker compose --profile=pds-core-registry  up --detach

Client-side Profiles
~~~~~~~~~~~~~~~~~~~~

The following table contains commonly used client-side profiles and descriptions.

====================== ==================================================== ==============================================
 Profile Name           Description                                          Prerequisites
====================== ==================================================== ==============================================
 pds-batch-loader       Executes the Standalone Harvest client-side tool.    The `pds-core-registry` server-side profile
                        This tool is   recommended for small data sets of    should be up and running
                        up to 10,000 PDS4 labels.
 pds-service-loader     Executes the Scalable Harvest client-side tool.      The `pds-service-loader` server-side profile
                        This tool is   recommended for larger data sets of   should be up and running
                        over 10,000 PDS4 labels.
====================== ==================================================== ==============================================

The `pds-batch-loader` profile can be started as follows (make sure to start the
profile `pds-core-registry` before starting this)::
    docker compose --profile=pds-batch-loader up --detach

The `pds-service-loader` profile can be started as follows (make sure to start the
profile `pds-service-loader` before starting this)::
    docker compose --profile=pds-service-loader up --detach


Cleaning-up the Deployment
**************************

The docker containers deployed using a docker compose profile can be easily uninstalled and cleaned-up using the following
command::

    docker compose --profile=<DOCKER_COMPOSE_PROFILE_NAME> down

Examples::
    docker compose --profile=pds-core-registry down
    docker compose --profile=pds-core-registry down
    docker compose --profile=pds-batch-loader down
    docker compose --profile=pds-service-loader down
