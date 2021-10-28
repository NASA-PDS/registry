#!/usr/bin/env bash

# Copyright 2019, California Institute of Technology ("Caltech").
# U.S. Government sponsorship acknowledged.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# * Redistributions must reproduce the above copyright notice, this list of
# conditions and the following disclaimer in the documentation and/or other
# materials provided with the distribution.
# * Neither the name of Caltech nor its operating division, the Jet Propulsion
# Laboratory, nor the names of its contributors may be used to endorse or
# promote products derived from this software without specific prior written
# permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


# Check Java
if [ -n "$JAVA_HOME" ]; then
    JAVA="$JAVA_HOME/bin/java"
    if [ ! -f "$JAVA" ]; then
        echo "Could not find java in JAVA_HOME=$JAVA_HOME"
        exit 1
    fi
else
    $(java -version > /dev/null 2>&1)
    if [[ $? -ne 0 ]] ; then
        echo "Java 1.8 or later is required to run Registry Manager."
        exit 1
    fi
    JAVA=java
fi

# Download test bundle
if [ ! -d "./data/dph_example_archive/" ]; then
    mkdir data
    cd data
    curl https://pds.nasa.gov/datastandards/documents/examples/v1/DPH_Examples_V11400.zip > DPH_Examples_V11400.zip
    unzip DPH_Examples_V11400.zip
    cd ..
fi


# Run Harvest
"$JAVA" -jar "./harvest/target/harvest-3.6.0-SNAPSHOT.jar" -c ./src/main/resources/bundles.xml -o /tmp/harvest_out

# start elasticsearch
docker run -p 9200:9200 -p 9300:9300 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.15.1 &

until $(curl --output /dev/null --silent --head --fail http://localhost:9200); do
    printf '.'
    sleep 5
done

# run registry manager
export REGISTRY_MANAGER_HOME=./registry-manager/target/classes
"$JAVA" -jar "./registry-manager/target/registry-manager-4.3.0-SNAPSHOT.jar" create-registry
"$JAVA" -jar "./registry-manager/target/registry-manager-4.3.0-SNAPSHOT.jar" load-data -dir /tmp/harvest_out


