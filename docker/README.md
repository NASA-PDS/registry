# 🪐 Docker Compose for Registry Components

This directory contains the files related with docker compose for Registry Container. To learn more about docker compose,
please refer to https://docs.docker.com/compose/.

The docker-compose.yml file contains following 3 components.
* registry-loader - Executes the Registry Loader component, which contains Harvest and Registry Manager
* registry-loader-test - Downloads and harvests test data with the Registry loader
* elasticsearch - Starts Elasticsearch
* registry-api - Starts the Registry API

Also, the docker-compose.yml file contains following profiles.

| Profile               | Purpose |
| --------------------- | ------------ |
| elastic               | Used to start only Elasticsearch |
| api                   | Used to start only Registry API|
| services              |Used to start both Elasticsearch and Registry API |
| reg-loader       |Used to execute only Registry Loader |
| reg-loader-test  |Used to execute only Registry Loader with test data |

With the use of above profiles the docker compose can start components individually
or as a group of components as follows. The `-d` option at the end of the commands is used to
run containers in detached mode (Run containers in the background).

```
docker-compose --profile=elastic up -d

docker-compose --profile=services up -d

docker-compose --profile=reg-loader up
```

## 🏃 Steps to configure registry components to be executed with docker compose

1. Open the `.env` file (located in the same directory with the `docker.compose.yml` file).


2. Check and update (if necessary) the following environment variables related with Elasticsearch.

| Environment Variable  | Description |
| --------------------- | ----------- |
| ES_IMAGE              | Docker image of Elasticsearch. Make sure this docker image is available. |
| ES_DISCOVERY_TYPE     | Elasticsearch discovery mode. |

```    
# --------------------------------------------------------------------
# Elasticsearch
# --------------------------------------------------------------------

# Docker image of Elasticsearch
ES_IMAGE=docker.elastic.co/elasticsearch/elasticsearch:7.8.1

# Elasticsearch discovery mode
ES_DISCOVERY_TYPE=single-node
```

3. Check and update (if necessary) the `elasticSearch.host` property in the `config/application.properties` file. 

Make sure this `application.properties` file is up-to-date with the latest changes in the Registry API service. It is recommended to 
get a copy of `application.properties` from the latest code of the Registry API service 
([registry-api-service/tree/main/src/main/resources](https://github.com/NASA-PDS/registry-api-service/blob/main/src/main/resources/application.properties))
and replace the `config/application.properties` file with it.

The `elasticSearch.host` should be set as follows. The host name used below should match with the Elasticsearch service 
name used in the `docker-compose.yml`.

```
elasticSearch.host=elasticsearch:9200
```

4. Check and update (if necessary) the following environment variables related with the Registry API.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| REG_API_IMAGE                 | Docker image of the Registry API. Make sure this docker image is available. |
| REG_API_APP_PROPERTIES_FILE   | Absolute path of the `application.properties` file to be used for the Registry API. |
| REG_API_WAIT_FOR_ES_SCRIPT    | Absolute path of the `wait-for-elasticsearch.sh` script. This script is used to wait for Elasticsearch to start before the Registry API. |

```    
# Docker image of Registry API
REG_API_IMAGE=pds/registry-api-service:0.4.0-SNAPSHOT

# Absolute path of the application.properties file to be used for the Registry API
REG_API_APP_PROPERTIES_FILE=./config/application.properties

# Absolute path of the wait-for-elasticsearch.sh script
REG_API_WAIT_FOR_ES_SCRIPT=./scripts/wait-for-elasticsearch.sh
```
5. Make sure that the Harvest configuration file has the directory path configured as `/data` as shown the following example.

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

6. Check and update (if necessary) the following environment variables related with the Registry Loader.

| Environment Variable          | Description |
| ----------------------------- | ----------- |
| REG_LOADER_IMAGE              | Docker image of the Registry Loader. Make sure this docker image is available. |
| ES_URL                        | Elasticsearch URL (the host name is the Elasticsearch service name specified in the docker compose). |
| HARVEST_CFG_FILE              | Absolute path of the Harvest configuration file in the host machine (E.g.: `/tmp/cfg/harvest-config.xml`). |
| HARVEST_DATA_DIR              | Absolute path of the Harvest data directory in the host machine (E.g.: `/tmp/data/urn-nasa-pds-insight_rad`). |
| TEST_DATA_URL                 | URL to download the test data to Harvest (only required, if executing with test data). |

```    
# Docker image of the Registry Loader
REG_LOADER_IMAGE=pds/registry-loader

# Elasticsearch URL (the host name is the Elasticsearch service name specified in the docker compose)
ES_URL=http://elasticsearch:9200

# Absolute path of the Harvest configuration file in the host machine (E.g.: /tmp/cfg/harvest-config.xml)
HARVEST_CFG_FILE=/tmp/cfg/harvest-test-config.xml

# Absolute path of the Harvest data directory in the host machine (E.g.: /tmp/data/urn-nasa-pds-insight_rad)
HARVEST_DATA_DIR=/tmp/data

# URL to download the test data to Harvest (only required, if executing with test data)
TEST_DATA_URL=https://pds-gamma.jpl.nasa.gov/data/pds4/test-data/registry/urn-nasa-pds-insight_rad.tar.gz
```

## 🏃 Steps to execute registry components with docker compose

1. Start the backend services (both Elasticsearch and the Registry API) as follows.

```
docker-compose --profile=services up -d
```

When above command is executed, the Registry API will wait for Elasticsearch to start. 

Alternatively, it is possible to start only Elasticsearch as follows.

```
docker-compose --profile=elastic up -d
```

2. Execute the Registry Loader as follows.

```
docker-compose --profile=reg-loader up
```

When above command is executed, the Registry Loader will use the configurations and data provided with the following 
environment variables configured in the `.env` file.
* HARVEST_CFG_FILE
* HARVEST_DATA_DIR

Alternatively, it is possible to execute the Registry Loader with test data as follows.

```
docker-compose --profile=reg-loader-test up
```
When above command is executed, the Registry Loader will download test data from URL configured with the following
environment variable  in the `.env` file.
* TEST_DATA_URL

Wait for the following message in the terminal to make sure if the execution of the Registry Loader exited with code 0.

```
docker-registry-loader-1 exited with code 0
```

3. Test the deployment.

Follow the instructions in the following sections at the end of the [Test Your Deployment](https://nasa-pds.github.io/pds-registry-app/install/test.html).

* Query Elasticsearch
* Use Registry API
