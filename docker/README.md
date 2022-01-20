# 🪐 Docker Compose for Registry Components

This directory contains the files related with docker compose for Registry Container. To learn more about docker compose,
please refer to [https://docs.docker.com/compose/](https://docs.docker.com/compose/).

The docker-compose.yml file contains following components.
* registry-loader - Executes the Registry Loader component, which contains Harvest and Registry Manager
* registry-loader-test - Downloads and harvests test data with the Registry loader
* elasticsearch - Starts Elasticsearch
* registry-api - Starts the Registry API
* big-data-harvest-server - Starts the Big Data Harvest Server
* big-data-crawler-server - Starts the Big Data Crawler Server
* big-data-harvest-client - Starts the Big Data Harvest Client

Also, the docker-compose.yml file contains following profiles.

| Profile                   | Purpose |
| ------------------------- | ------------ |
| elastic                   | Used to start only Elasticsearch |
| api                       | Used to start only Registry API|
| services                  | Used to start both Elasticsearch and Registry API |
| reg-loader                | Used to execute only Registry Loader |
| reg-loader-test           | Used to execute only Registry Loader with test data (Test data is automatically downloaded from a URL) |
| big-data                  | Used to start all big-data components |
| big-data-services         | Used to start only Big Data Harvest Server and Big Data Crawler Server |
| big-data-client           | Used to execute only Big Data Harvest Client |
| big-data-integration-test | Used to start all big-data components with test data |

With the use of above profiles the docker compose can start components individually
or as a group of components as follows. The `-d` option at the end of the commands is used to
run containers in detached mode (Run containers in the background).

```
docker compose --profile=elastic up -d

docker compose --profile=services up -d

docker compose --profile=reg-loader up
```

For test, start the registry with some test data loaded:

    docker compose --profile=integration-test up


For API dev, start the registry with some test data, without the API:

    docker compose --profile=pre-api-dev up

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
REG_API_APP_PROPERTIES_FILE=./config/application.properties
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
| HARVEST_CFG_FILE              | Absolute path of the Harvest configuration file in the host machine (E.g.: `/tmp/cfg/harvest-config.xml`) |
| TEST_DATA_URL                 | URL to download the test data to Harvest (only required, if executing with test data) |
| HARVEST_DATA_DIR              | Absolute path for the Harvest data directory in the host machine (E.g.: `/tmp/big-data-harvest-data`). If the Big Data Harvest Client is executed with the option to download test data, then this directory will be cleaned-up and populated with test data |

```    
# Docker image of the Registry Loader
REG_LOADER_IMAGE=pds/registry-loader

# Elasticsearch URL (the host name is the Elasticsearch service name specified in the docker compose)
ES_URL=http://elasticsearch:9200

# Absolute path of the Harvest configuration file in the host machine (E.g.: /tmp/cfg/harvest-config.xml)
HARVEST_CFG_FILE=/tmp/cfg/harvest-test-config.xml

# URL to download the test data to Harvest (only required, if executing with test data)
TEST_DATA_URL=https://pds-gamma.jpl.nasa.gov/data/pds4/test-data/registry/urn-nasa-pds-insight_rad.tar.gz

# --------------------------------------------------------------------
# Common Configuartions
# --------------------------------------------------------------------

# Absolute path for the Harvest data directory in the host machine (E.g.: `/tmp/big-data-harvest-data`).
# If the Big Data Harvest Client is executed with the option to download test data, then this directory will be
# cleaned-up and populated with test data. Make sure to have the same `HARVEST_DATA_DIR` value set in the
# environment variables of the Big Data Harvest Server, Big Data Crawler Server and Big Data Harvest Client.
# Also, this `HARVEST_DATA_DIR` location should be accessible from the docker containers of the Big Data Harvest Server,
# Big Data Crawler Server and Big Data Harvest Client.
HARVEST_DATA_DIR=/tmp/big-data-harvest-data
```

## 🏃 Steps to execute registry components with docker compose

#### 1. Open a terminal and change the current working directory to `registry/docker`.

#### 2. Start the backend services (both Elasticsearch and the Registry API) as follows.

```
docker compose --profile=services up -d
```

When above command is executed, the Registry API will wait for Elasticsearch to start.

Alternatively, it is possible to start only Elasticsearch as follows.

```
docker compose --profile=elastic up -d
```

#### 3. Execute the Registry Loader as follows.

```
docker compose --profile=reg-loader up
```

When above command is executed, the Registry Loader will use the configurations and data provided with the following
environment variables configured in the `.env` file.
```
* HARVEST_CFG_FILE
* HARVEST_DATA_DIR
```

Alternatively, it is possible to execute the Registry Loader with test data as follows.
```
docker compose --profile=reg-loader-test up
```

When above command is executed, the Registry Loader will download test data from URL configured with the following
environment variable  in the `.env` file.
```
* TEST_DATA_URL
```

Wait for the following message in the terminal to make sure if the execution of the Registry Loader exited with code 0.
```
docker-registry-loader-1 exited with code 0
```

#### 4. Test the deployment.

Follow the instructions in the following sections at the end of the [Test Your Deployment](https://nasa-pds.github.io/pds-registry-app/install/test.html).

* Query Elasticsearch
* Use Registry API

## 🏃 Cleaning up the Registry Loader deployment

#### * The Registry Loader can be cleaned up as follows.

```
docker compose --profile=reg-loader down
```

Note: Ignore any `failed to remove network` errors, because the related docker network
has active endpoints of other services.


#### * The Registry Loader with test data can be cleaned up as follows.

```
docker compose --profile=reg-loader-test down
```

Note: Ignore any `failed to remove network` errors, because the related docker network
has active endpoints of other services.

#### * The Registry API and Elasticsearch can be cleaned up as follows.

```
docker compose --profile=services down
```

## 🏃 Steps to configure the Big Data Harvest components to be executed with docker compose

#### 1. Open the `.env` file (located in the same directory with the `docker.compose.yml` file).

#### 2. Check and update (if necessary) the following common environment variable.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| HARVEST_DATA_DIR              | Absolute path for the Harvest data directory in the host machine (E.g.: `/tmp/big-data-harvest-data`). If the Big Data Harvest Client is executed with the option to download test data, then this directory will be cleaned-up and populated with test data |

```
# --------------------------------------------------------------------
# Common Configuartions
# --------------------------------------------------------------------

# Absolute path for the Harvest data directory in the host machine (E.g.: `/tmp/big-data-harvest-data`).
# If the Big Data Harvest Client is executed with the option to download test data, then this directory will be
# cleaned-up and populated with test data. Make sure to have the same `HARVEST_DATA_DIR` value set in the
# environment variables of the Big Data Harvest Server, Big Data Crawler Server and Big Data Harvest Client.
# Also, this `HARVEST_DATA_DIR` location should be accessible from the docker containers of the Big Data Harvest Server,
# Big Data Crawler Server and Big Data Harvest Client.
HARVEST_DATA_DIR=/tmp/big-data-harvest-data
```

#### 2. Update the Big Data Harvest Server configuration file.

* Get a copy of the `harvest-server.cfg` file from https://github.com/NASA-PDS/big-data-harvest-server/blob/main/src/main/resources/conf/harvest-server.cfg and keep it in a local file location such as `/tmp/cfg/harvest-server.cfg`.
* Update the properties such as `rmq.host`, `rmq.user`, `rmq.password` and `es.url` to match with your deployment environment.

#### 3. Check and update (if necessary) the following environment variables related with the Big Data Harvest Server.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| BIG_DATA_HARVEST_SERVER_IMAGE | Docker image of the Big Data Harvest Server. Make sure this docker image is available. |
| HARVEST_SERVER_CONFIG_FILE    | Absolute path for the Big Data Harvest Server configuration file in the host machine (E.g.: `/tmp/cfg/harvest-server.cfg`) |

```    
# --------------------------------------------------------------------
# Big Data Harvest Server
# --------------------------------------------------------------------

# Docker image of the Big Data Harvest Server
BIG_DATA_HARVEST_SERVER_IMAGE=nasapds/big-data-harvest-server

# Absolute path for the Big Data Harvest Server configuration file in the host machine (E.g.: /tmp/cfg/harvest-server.cfg)
HARVEST_SERVER_CONFIG_FILE=/tmp/cfg/harvest-server.cfg
```

#### 4. Update the Big Data Crawler Server configuration file.

* Get a copy of the `harvest-client.cfg` file from https://github.com/NASA-PDS/big-data-crawler-server/blob/main/src/main/resources/conf/crawler-server.cfg and
  keep it in a local file location such as `/tmp/cfg/crawler-server.cfg`.
* Update the properties such as `rmq.host`, `rmq.user` and `rmq.password` to match with your deployment environment.

#### 5. Check and update (if necessary) the following environment variables related with the Big Data Crawler Server.


| Environment Variable          | Description |
| ----------------------------- | ----------- |
| BIG_DATA_CRAWLER_SERVER_IMAGE | Docker image of the Big Data Harvest Crawler. Make sure this docker image is available. |
| CRAWLER_SERVER_CONFIG_FILE    | Absolute path for the Big Data Crawler Server configuration file in the host machine (`E.g.: /tmp/cfg/crawler-server.cfg`) |

```    
# --------------------------------------------------------------------
# Big Data Crawler Server
# --------------------------------------------------------------------

# Docker image of the Big Data Crawler Server
BIG_DATA_CRAWLER_SERVER_IMAGE=nasapds/big-data-crawler-server

# Absolute path for the Big Data Crawler Server configuration file in the host machine (E.g.: /tmp/cfg/crawler-server.cfg)
CRAWLER_SERVER_CONFIG_FILE=/tmp/cfg/crawler-server.cfg
```

#### 6. Update the Big Data Harvest Client configuration file.

* Get a copy of the `harvest-client.cfg` file from https://github.com/NASA-PDS/big-data-harvest-client/blob/main/src/main/resources/conf/harvest-client.cfg and
  keep it in a local file location such as `/tmp/conf/harvest-client.cfg`.
* Update the properties such as `rmq.host`, `rmq.user` and `rmq.password` to match with your deployment environment.

#### 7. Update the Harvest job file.

* Create a Harvest job file in a local file location (E.g.: `/tmp/cfg/harvest-job-config.xml`).
* An example for a Harvest job file can be found at https://github.com/NASA-PDS/big-data-harvest-client/blob/main/src/main/resources/examples/directories.xml.
  Make sure to update the `/path/to/archive` in the Harvest job file to point to a valid Harvest data directory.

#### 8. Check and update (if necessary) the following environment variables related with the Big Data Harvest Client.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| BIG_DATA_HARVEST_CLIENT_IMAGE | Docker image of the Big Data Harvest Client. Make sure this docker image is available. |
| HARVEST_JOB_CONFIG_FILE       | Absolute path for the Harvest job file in the host machine (E.g.: `/tmp/cfg/harvest-job-config.xml`) |
| HARVEST_CLIENT_CONFIG_FILE    | Absolute path for the Big Data Harvest Client configuration file in the host machine (E.g.: `/tmp/conf/harvest-client.cfg`) |

```    
# --------------------------------------------------------------------
# Big Data Client Server
# --------------------------------------------------------------------

# Docker image of the Big Data Harvest Client
BIG_DATA_HARVEST_CLIENT_IMAGE=nasapds/big-data-harvest-client

# Absolute path for the Harvest job file in the host machine (E.g.: /tmp/cfg/harvest-job-config.xml)
HARVEST_JOB_CONFIG_FILE=/tmp/cfg/harvest-job-config.xml

# Absolute path for the Big Data Harvest Client configuration file in the host machine (E.g.: /tmp/conf/harvest-client.cfg)
HARVEST_CLIENT_CONFIG_FILE=/tmp/cfg/harvest-client.cfg
```

#### 9. Configure RabbitMQ

The RabbitMQ can be configured by using the `rabbitmq-definitions.json` file available at the `registry/docker/config` directory.

* Open the `rabbitmq-definitions.json` file.
* Locate the definition for the user `harvest` under the `users`. 
* The password of the user `harvest` should be specified as a RabbitMQ `password_hash`. Generate a password hash using 
the `rabbit_password_hashing_sha256` algorithm (The Python script available at the https://stackoverflow.com/questions/41306350/how-to-generate-password-hash-for-rabbitmq-management-http-api/53016240#53016240 
can be used to generate a password hash for a new password hash).
* Update the `password_hash` of the `harvest` user with the newly generated password hash.

## 🏃 Steps to execute the Big Data Harvest components with docker compose

#### 1. Open a terminal and change the current working directory to `registry/docker`.

#### 2. Setup Elasticsearch and RabbitMQ as explained in the following document.
TODO: Add the link to the Scalable Harvest documentation.

#### 3. Start Big Data Harvest components as follows.

To start all big-data components (Big Data Harvest Server, Big Data Crawler Server and Big Data Harvest Client) 
```
docker compose --profile=big-data up
```

To start only Big Data Harvest Server and Big Data Crawler Server
```
docker compose --profile=big-data-services up
```

To start only Big Data Harvest Client
```
docker compose --profile=big-data-client up
```

To execute Big Data Integration Tests with downloaded test data
```
docker compose --profile=big-data-integration-test up
```


#### 4. Test the deployment.

Follow the instructions in the following section at the end of the [Test Your Deployment](https://nasa-pds.github.io/pds-registry-app/install/test.html).

* Query Elasticsearch

## 🏃 Cleaning up the Big Data Harvest deployment

#### * The Big Data Harvest deployment can be cleaned up as follows.

```
docker compose --profile=big-data down
```

Note: Ignore any `failed to remove network` errors, because the related docker network
has active endpoints of other services.