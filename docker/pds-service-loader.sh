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

# ----------------------------------------------------------------------------------------------
# This script is a wrapper to run the registry-harvest-cli with docker compose, while passing a
# Harvest job configuration file as an argument.
#
# Usage: ./pds-service-loader.sh <harvest_job_config_file_path>
#
# ----------------------------------------------------------------------------------------------

# Common functions to print usage
print_usage () {
  echo "Usage: $0 <harvest_job_config_file_path>" 1>&2
  echo "Pass an absolute path of a Harvest job configuration file in the host machine (E.g.: ./default-config/harvest-job-config.xml)" 1>&2
}

# Check if an argument is provided to this script
if [ -z "$1" ]; then
  print_usage
  exit 1
fi

HARVEST_JOB_CONFIG_FILE=$1

# Check if the Harvest job configuration file exists
if [ ! -f "$HARVEST_JOB_CONFIG_FILE" ]; then
  echo "Error: The Harvest job configuration file ${HARVEST_JOB_CONFIG_FILE} passed as an argument does not exist."  1>&2
  print_usage
  exit 1
fi

# Execute docker compose run to load data
docker compose run registry-harvest-cli
