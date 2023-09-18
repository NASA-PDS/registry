# 🪐 Docker Compose for Registry Components

This directory contains the files related with docker compose for Registry Container. To learn more about docker compose,
please refer to [https://docs.docker.com/compose/](https://docs.docker.com/compose/).

The docker-compose.yml file contains following profiles and each profile will start the components as shown in the table below.

| Components\\Profiles                                 | dev-api | pds-core-registry | int-registry-batch-loader | int-registry-service-loader | pds-loader-services | pds-batch-loader | pds-service-loader | int-test |
|:-----------------------------------------------------|:-------:|:-----------------:|:-------------------------:|:---------------------------:|:-------------------:|:----------------:|:------------------:|:--------:|
| Elasticsearch                                        | ✓       | ✓                 | ✓                         | ✓                           |                     |                  |                    |          |
| Elasticsearch init                                   | ✓       | ✓                 | ✓                         | ✓                           |                     |                  |                    |          |
| Registry API                                         |         | ✓                 | ✓                         | ✓                           |                     |                  |                    |          |
| Registry loader test init                            | ✓       |                   | ✓                         |                             |                     |                  |                    |          |
| Registry loader                                      |         |                   |                           |                             |                     | ✓                |                    |          |
| Registry API integration tests (postman collection?) |         |                   | ✓                         | ✓                           |                     |                  |                    | ✓        |
| Rabbitmq                                             |         |                   |                           | ✓                           | ✓                   |                  |                    |          |
| Registry harvest service                             |         |                   |                           | ✓                           | ✓                   |                  |                    |          |
| Registry crawler service                             |         |                   |                           | ✓                           | ✓                   |                  |                    |          |
| Registry harvest cli test init                       |         |                   |                           | ✓                           |                     |                  |                    |          |
| Registry harvest cli                                 |         |                   |                           |                             |                     |                  | ✓                  |          |
| TLS termination                                      |         | ✓                 | ✓                         | ✓                           |                     |                  |                    |          |

With the use of above profiles the docker compose can start components individually
or as a group of components as follows. The `-d` option at the end of the commands is used to
run containers in detached mode (Run containers in the background).

```
docker compose --profile=pds-core-registry up -d

docker compose --profile=dev-api up
```

For test, start the registry with some test data loaded:

    docker compose --profile=int-registry-batch-loader up


For API dev, start the registry with some test data, without the API:

    docker compose --profile=dev-api up

In addition, the following wrapper scripts available in the `registry/docker` directory can be used to easily execute
some docker compose services.

| Script Usage | Description |
| ------------ | ----------- |
| `./int-test.sh` | This script is a wrapper to execute Postman integration tests with docker compose. Please note that the test data should be already available in Elasticsearch. If it is required to load test data before executing the integration test, then use the `int-registry-batch-loader` docker compose profile or `int-registry-service-loader` docker compose profile, as explained in this README file. |
| `./pds-batch-loader.sh <harvest_job_config_file_path>` | This script is a wrapper to run the registry loader with docker compose, while passing a Harvest job configuration file as an argument. |
| `./pds-service-loader.sh <harvest_job_config_file_path>` | This script is a wrapper to run the registry-harvest-cli with docker compose, while passing a Harvest job configuration file as an argument. |

## 🏃 Quick start guide - with default configurations

This quick start guide is a quick way to start all Registry Components, load test data and run tests with a Postman
collection. This quick start steps use default configurations such as default username and password.

PLEASE DO NOT use the quick start with default configurations in any environment other than your local machine. Make sure
to replace the default passwords with your own passwords as explained in the following section:
**Steps to configure registry components to be executed with docker compose** to ensure security.

**Steps to quick start all Registry Components, load test data and run tests with a Postman collection**

1) Get the latest copy of the Registry from https://github.com/NASA-PDS/registry.
```
git clone https://github.com/NASA-PDS/registry.git
```
2) Open a terminal and change the current working directory to `registry/docker/certs`.
```
cd docker/certs
```

3) Generate certificates required for OpenSearch by executing the following shell script.
```
./generate-certs.sh
```

4) Change the current working directory to `registry/docker`.
```
cd ..
```

5) Deploy and execute integration tests with the following single command.
```
docker compose --profile=int-registry-service-loader up
```
Note: This may take several minutes, including data loading  delays between components.

6) To clean the deployment, execute the following command.
```
docker compose --profile=int-registry-service-loader down
```


## 🏃 Steps to configure registry components to be executed with docker compose

#### 1. Open the `.env` file (located in the same directory with the `docker.compose.yml` file).

#### 2. Check and update (if necessary) the following environment variables related with Elasticsearch.

| Environment Variable  | Description |
| --------------------- | ----------- |
| ES_IMAGE              | Docker image of Elasticsearch. Make sure this docker image is available. |
| ES_DISCOVERY_TYPE     | Elasticsearch discovery mode |

```
# --------------------------------------------------------------------
# Elasticsearch
# --------------------------------------------------------------------

# Docker image of Elasticsearch
ES_IMAGE=docker.elastic.co/elasticsearch/elasticsearch:7.8.1

# Elasticsearch discovery mode
ES_DISCOVERY_TYPE=single-node
```

#### 3. Check and update (if necessary) the `elasticSearch.host` property in the `config/application.properties` file.

Make sure this `application.properties` file is up-to-date with the latest changes in the Registry API service. It is recommended to
get a copy of `application.properties` from the latest code of the Registry API service
([registry-api-service/tree/main/src/main/resources](https://github.com/NASA-PDS/registry-api-service/blob/main/src/main/resources/application.properties))
and replace the `config/application.properties` file with it.

The `elasticSearch.host` should be set as follows. The host name used below should match with the Elasticsearch service
name used in the `docker-compose.yml`.

```
elasticSearch.host=elasticsearch:9200
```

#### 4. Check and update (if necessary) the following environment variables related with the Registry API.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| REG_API_IMAGE                 | Docker image of the Registry API. Make sure this docker image is available. |
| REG_API_APP_PROPERTIES_FILE   | Absolute path of the `application.properties` file to be used for the Registry API |

```
# Docker image of Registry API
REG_API_IMAGE=pds/registry-api-service:0.4.0-SNAPSHOT

# Absolute path of the application.properties file to be used for the Registry API
REG_API_APP_PROPERTIES_FILE=./default-config/application.properties
```

#### 5. Make sure that the Harvest configuration file has the directory path configured as `/data`, as shown in the following example.

```
<?xml version="1.0" encoding="UTF-8"?>
<harvest nodeName="PDS_ENG">
  <directories>
    <path>/data</path>
  </directories>
  <registry url="http://elasticsearch:9200" index="registry" />
  <autogenFields/>
</harvest>

```

#### 6. Check and update (if necessary) the following environment variables related with the Registry Loader.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| REG_LOADER_IMAGE              | Docker image of the Registry Loader. Make sure this docker image is available. |
| ES_URL                        | Elasticsearch URL (the host name is the Elasticsearch service name specified in the docker compose) |
| TEST_DATA_URL                 | URL to download the test data to Harvest (only required, if executing with test data) |
| TEST_DATA_LIDVID              | The lidvid of the test data, which is used to set the archive status |
| HARVEST_DATA_DIR              | Absolute path of the Harvest data directory in the host machine (E.g.: `/tmp/registry-harvest-data`). If the Registry Harvest CLI is executed with the option to download test data, then this directory will be cleaned-up and populated with test data |
| HARVEST_JOB_CONFIG_FILE       | Absolute path of the Harvest configuration file in the host machine (E.g.: `./default-config/harvest-job-config.xml`) |

```
# Docker image of the Registry Loader
REG_LOADER_IMAGE=nasapds/registry-loader

# Elasticsearch URL (the host name is the Elasticsearch service name specified in the docker compose)
ES_URL=http://elasticsearch:9200

# --------------------------------------------------------------------
# Common Configuartions
# --------------------------------------------------------------------

# Absolute path of the Harvest data directory in the host machine (E.g.: `./test-data/registry-harvest-data`).
# If the Registry Harvest CLI is executed with the option to download test data, then this directory will be
# cleaned-up and populated with test data. Make sure to have the same `HARVEST_DATA_DIR` value set in the
# environment variables of the Registry Harvest Service, Registry Crawler Service and Registry Harvest CLI.
# Also, this `HARVEST_DATA_DIR` location should be accessible from the docker containers of the Registry Harvest Service,
# Registry Crawler Service and Registry Harvest CLI.
HARVEST_DATA_DIR=./test-data/registry-harvest-data

# Absolute path of the Harvest job file in the host machine (E.g.: ./default-config/harvest-job-config.xml)
HARVEST_JOB_CONFIG_FILE=./default-config/harvest-job-config.xml

# URL to download the test data to Harvest (only required, if executing with test data)
TEST_DATA_URL=https://pds-gamma.jpl.nasa.gov/data/pds4/test-data/registry/urn-nasa-pds-insight_rad.tar.gz

# The lidvid of the test data, which is used to set the archive status (only required, if executing with test data)
TEST_DATA_LIDVID=urn:nasa:pds:insight_rad::2.1
```

#### 7. Generate certificates

1) Open a terminal and change the current working directory to `registry/docker/certs`.
```
cd docker/certs
```

2) Generate the certificates required for OpenSearch by executing the following shell script.
```
./generate-certs.sh
```


## 🏃 Steps to execute registry components with docker compose

#### 1. Open a terminal and change the current working directory to `registry/docker`.

#### 2. Start the backend services (both Elasticsearch and the Registry API) as follows.

```
docker compose --profile=pds-core-registry up -d
```

When above command is executed, the Registry API will wait for Elasticsearch to start.

Alternatively, it is possible to start only Elasticsearch as follows (see the table with profiles and components above).

```
docker compose --profile=dev-api up -d
```

#### 3. Execute the Registry Loader as follows.

```
docker compose --profile=pds-batch-loader up
```

When above command is executed, the Registry Loader will use the configurations and data provided with the following
environment variables configured in the `.env` file.
```
* HARVEST_JOB_CONFIG_FILE
* HARVEST_DATA_DIR
```

Alternatively, it is possible to execute the Registry Loader with test data and integration tests as follows.
```
docker compose --profile=int-registry-batch-loader up
```

When above command is executed, the Registry Loader will download test data from URL configured with the following
environment variable  in the `.env` file.
```
* TEST_DATA_URL
```

Wait for the following message in the terminal to make sure if the execution of the Registry Loader exited with code 0.
```
docker-reg-api-integration-1 exited with code 0
```

#### 4. Test the deployment.

Follow the instructions in the following sections at the end of the [Test Your Deployment](https://nasa-pds.github.io/pds-registry-app/install/test.html).

* Query Elasticsearch
* Use Registry API

Note that the Registry API is published to port 8080 as `http` and—when not using the `dev-api` profile—to port 8443 as `https` (with a self-signed certificate) on all host interfaces.

## 🏃 Cleaning up the Registry Loader deployment

#### * The Registry Loader can be cleaned up as follows.

```
docker compose --profile=pds-batch-loader down
```

Note: Ignore any `failed to remove network` errors, because the related docker network
has active endpoints of other services.


#### * The Registry Loader with test data can be cleaned up as follows.

```
docker compose --profile=int-registry-batch-loader down
```

Note: Ignore any `failed to remove network` errors, because the related docker network may
have active endpoints of other services.

## 🏃 Steps to configure the Scalable Harvest components to be executed with docker compose

#### 1. Open the `.env` file (located in the same directory with the `docker.compose.yml` file).

#### 2. Check and update (if necessary) the following common environment variable.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| HARVEST_DATA_DIR              | Absolute path of the Harvest data directory in the host machine (E.g.: `/tmp/registry-harvest-data`). If the Registry Harvest CLI is executed with the option to download test data, then this directory will be cleaned-up and populated with test data |

```
# --------------------------------------------------------------------
# Common Configuartions
# --------------------------------------------------------------------

# Absolute path of the Harvest data directory in the host machine (E.g.: `./test-data/registry-harvest-data`).
# If the Registry Harvest CLI is executed with the option to download test data, then this directory will be
# cleaned-up and populated with test data. Make sure to have the same `HARVEST_DATA_DIR` value set in the
# environment variables of the Registry Harvest Service, Registry Crawler Service and Registry Harvest CLI.
# Also, this `HARVEST_DATA_DIR` location should be accessible from the docker containers of the Registry Harvest Service,
# Registry Crawler Service and Registry Harvest CLI.
HARVEST_DATA_DIR=./test-data/registry-harvest-data
```

#### 2. Update the Registry Harvest Service configuration file.

* Get a copy of the `harvest-server.cfg` file from https://github.com/NASA-PDS/registry-harvest-service/blob/main/src/main/resources/conf/harvest-server.cfg and keep it in a local file location such as `/tmp/cfg/harvest-server.cfg`.
* Update the properties such as `rmq.host`, `rmq.user`, `rmq.password` and `es.url` to match with your deployment environment.
* Make sure to specify the exact IP address of the host machine (E.g.: `192.168.0.1`), when configuring the `rmq.host` and
  `es.url`.

#### 3. Check and update (if necessary) the following environment variables related with the Registry Harvest Service in the `.env` file.


| Environment Variable          | Description |
| ----------------------------- | ----------- |
| BIG_DATA_HARVEST_SERVER_IMAGE | Docker image of the Registry Harvest Service. Make sure this docker image is available. |
| HARVEST_SERVER_CONFIG_FILE    | Absolute path of the Registry Harvest Service configuration file in the host machine (E.g.: `./default-config/harvest-server.cfg`) |

```
# --------------------------------------------------------------------
# Registry Harvest Service
# --------------------------------------------------------------------

# Docker image of the Registry Harvest Service
REGISTRY_HARVEST_SERVICE_IMAGE=nasapds/registry-harvest-service

# Absolute path of the Registry Harvest Service configuration file in the host machine (E.g.: /tmp/cfg/harvest-server.cfg)
HARVEST_SERVER_CONFIG_FILE=./default-config/harvest-server.cfg
```

#### 4. Update the Registry Crawler Service configuration file.

* Get a copy of the `harvest-client.cfg` file from https://github.com/NASA-PDS/big-data-crawler-server/blob/main/src/main/resources/conf/crawler-server.cfg and
  keep it in a local file location such as `/tmp/cfg/crawler-server.cfg`.
* Update the properties such as `rmq.host`, `rmq.user` and `rmq.password` to match with your deployment environment.
* Make sure to specify the exact IP address of the host machine (E.g.: `192.168.0.1`), when configuring the `rmq.host`.

#### 5. Check and update (if necessary) the following environment variables related with the Registry Crawler Service in the `.env` file.


| Environment Variable           | Description |
| ------------------------------ | ----------- |
| REGISTRY_CRAWLER_SERVICE_IMAGE | Docker image of the Registry Crawler Service. Make sure this docker image is available. |
| CRAWLER_SERVER_CONFIG_FILE     | Absolute path of the Registry Crawler Service configuration file in the host machine (`E.g.: ./default-config/crawler-server.cfg`) |

```
# --------------------------------------------------------------------
# Registry Crawler Service
# --------------------------------------------------------------------

# Docker image of the Registry Crawler Service
REGISTRY_CRAWLER_SERVICE_IMAGE=nasapds/registry-crawler-service

# Absolute path of the Registry Crawler Service configuration file in the host machine (E.g.: /tmp/cfg/crawler-server.cfg)
CRAWLER_SERVER_CONFIG_FILE=./default-config/crawler-server.cfg
```

#### 6. Update the Registry Harvest CLI configuration file.

* Get a copy of the `harvest-client.cfg` file from https://github.com/NASA-PDS/registry-harvest-cli/blob/main/src/main/resources/conf/harvest-client.cfg and
  keep it in a local file location such as `./default-config/harvest-client.cfg`.
* Update the properties such as `rmq.host`, `rmq.user` and `rmq.password` to match with your deployment environment.
* Make sure to specify the exact IP address of the host machine (E.g.: `192.168.0.1`), when configuring the `rmq.host`.


#### 7. Update the Harvest job file.

* Create a Harvest job file in a local file location (E.g.: `./default-config/cfg/harvest-job-config.xml`).
* An example for a Harvest job file can be found at https://github.com/NASA-PDS/registry-harvest-cli/blob/main/src/main/resources/examples/directories.xml.
  Make sure to update the `/path/to/archive` in the Harvest job file to point to a valid Harvest data directory.

#### 8. Check and update (if necessary) the following environment variables related with the Registry Harvest CLI in the `.env` file.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| REGISTRY_HARVEST_CLI_IMAGE    | Docker image of the Registry Harvest CLI. Make sure this docker image is available. |
| HARVEST_CLIENT_CONFIG_FILE    | Absolute path of the Registry Harvest CLI configuration file in the host machine (E.g.: `./default-config/harvest-client.cfg`) |
| HARVEST_JOB_CONFIG_FILE       | Absolute path of the Harvest job file in the host machine (E.g.: `./default-config/harvest-job-config.xml`) |

```
# --------------------------------------------------------------------
# Registry Harvest CLI
# --------------------------------------------------------------------

# Docker image of the Registry Harvest CLI
REGISTRY_HARVEST_CLI_IMAGE=nasapds/registry-harvest-cli

# Absolute path of the Registry Harvest CLI configuration file in the host machine (E.g.: /tmp/conf/harvest-client.cfg)
HARVEST_CLIENT_CONFIG_FILE=./default-config/harvest-client.cfg

# --------------------------------------------------------------------
# Common Configuartions
# --------------------------------------------------------------------

# Absolute path of the Harvest job file in the host machine (E.g.: ./default-config/harvest-job-config.xml)
HARVEST_JOB_CONFIG_FILE=./default-config/harvest-job-config.xml
```

#### 9. Configure RabbitMQ

The RabbitMQ can be configured by using the `rabbitmq-definitions.json` file available at the `registry/docker/config` directory.

* Open the `rabbitmq-definitions.json` file.
* Locate the definition for the user `harvest` under the `users`.
* The password of the user `harvest` should be specified as a RabbitMQ `password_hash`. Generate a password hash using
the `rabbit_password_hashing_sha256` algorithm (The Python script available at the https://stackoverflow.com/questions/41306350/how-to-generate-password-hash-for-rabbitmq-management-http-api/53016240#53016240
can be used to generate a password hash for a new password hash).
* Update the `password_hash` of the `harvest` user with the newly generated password hash.

#### 10. Check and update (if necessary) the following environment variables related with the Postman Collection Test

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| POSTMAN_NEWMAN_IMAGE          | Docker image of Newman (a command-line collection runner for Postman) |
| POSTMAN_COLLECTION_FILE       | Absolute path of the Postman collection to be executed with the test data (E.g.: ./postman/postman_collection.json) |

```
# --------------------------------------------------------------------
# Registry Harvest CLI
# --------------------------------------------------------------------

# Docker image of Newman (a command-line collection runner for Postman)
POSTMAN_NEWMAN_IMAGE=postman/newman

# Absolute path of the Postman collection to be executed with the test data (E.g.: ./postman/postman_collection.json)
POSTMAN_COLLECTION_FILE=./postman/postman_collection.json
```

## 🏃 Steps to execute the Scalable Harvest components with docker compose

#### 1. Open a terminal and change the current working directory to `registry/docker`.

#### 2. Setup Elasticsearch and RabbitMQ as explained in the following document.
TODO: Add the link to the Scalable Harvest documentation.

#### 3. Start Scalable Harvest components as follows.

To execute Scalable Harvest Integration Tests with downloaded test data
```
docker compose --profile=int-registry-service-loader up
```

#### 4. Test the deployment.

Follow the instructions in the following section at the end of the [Test Your Deployment](https://nasa-pds.github.io/pds-registry-app/install/test.html).

* Query Elasticsearch

## 🏃 Cleaning up the Scalable Harvest deployment

#### * The Scalable Harvest deployment can be cleaned up as follows.
```
docker compose --profile=int-registry-service-loader down
```

Note: Ignore any `failed to remove network` errors, because the related docker network may
have active endpoints of other services.
