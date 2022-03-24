#!/bin/sh

# Copyright 2022, California Institute of Technology ("Caltech").
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

# ------------------------------------------------------------------------------------------------
# This script is used to wait for Elasticsearch to start before starting the Registry API service.
# ------------------------------------------------------------------------------------------------

# Check if the ES_URL environment variable is set
if [ -z "$ES_URL" ]; then
    echo "Error: 'ES_URL' (Elasticsearch URL) environment variable is not set. Use docker's -e option." 1>&2
    exit 1
fi

echo "Waiting for Elasticsearch to launch..."  1>&2
# TODO Warning: Use the default username and password only for testing purposes in local setup
while ! curl --output /dev/null --silent --head --fail "$ES_URL" -u 'admin:admin' --insecure; do
  echo "waiting for elasticsearch" 1>&2
  sleep 1
done

echo "Waiting for the creation of registry and data dictionary indices..."  1>&2
sleep 60

echo "Starting Registry API service..."  1>&2
java -cp /usr/local/registry-api-service \
     -jar /usr/local/registry-api-service/registry-api-service.jar \
     --spring.config.location=file:///usr/local/registry-api-service/application.properties \
     gov.nasa.pds.api.engineering.SpringBootMain
