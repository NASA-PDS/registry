#!/bin/sh

# ----------------------------------------------------------------------------------------------------------------
#
# This script is used to generate certificates required to enable https in OpenSearch. Please note that the
# CN=elasticsearch should match with the hostname of the OpenSearch/Elasticsearch.
#
# Read more information at: https://opensearch.org/docs/latest/security-plugin/configuration/generate-certificates/
#
# ----------------------------------------------------------------------------------------------------------------

# Root CA
openssl genrsa -out root-ca-key.pem 2048
openssl req -new -x509 -sha256 -key root-ca-key.pem -subj "/C=CA/ST=CALIFORNIA/L=LA/O=ORG/OU=PDS/CN=elasticsearch" -out root-ca.pem -days 730

# Node cert 1
openssl genrsa -out node1-key-temp.pem 2048
openssl pkcs8 -inform PEM -outform PEM -in node1-key-temp.pem -topk8 -nocrypt -v1 PBE-SHA1-3DES -out node1-key.pem
openssl req -new -key node1-key.pem -subj "/C=CA/ST=CALIFORNIA/L=LA/O=ORG/OU=PDS/CN=elasticsearch" -out node1.csr
openssl x509 -req -in node1.csr -CA root-ca.pem -CAkey root-ca-key.pem -CAcreateserial -sha256 -out node1.pem -days 730

# Cleanup
rm node1-key-temp.pem
rm node1.csr
