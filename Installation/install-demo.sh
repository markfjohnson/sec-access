#!/usr/bin/env bash
# create the necessary service accounts
#exec create-service-accounts.sh


# TODO Create the Application groups for dept-a and dept-b for each of the necessary components
dcos package install --yes dcos-enterprise-cli --cli

dcos package install --yes marathon-lb
#dcos package install --yes portworx

# TODO Setup service account for cassandra
dcos package install --yes cassandra
dcos marathon app add cas-client.json
#TODO Setup service account for Spark
#TODO Setup spark history configuration
dcos package install --yes spark --options=spark_options-no-svc.json
dcos package install --yes beakerx

dcos marathon pod add https://raw.githubusercontent.com/markfjohnson/dcos-j2ee-legacy-examples/master/Installation/metrics.json
dcos marathon app add https://raw.githubusercontent.com/markfjohnson/dcos-j2ee-legacy-examples/master/Installation/prometheus.json
dcos marathon app add https://raw.githubusercontent.com/markfjohnson/dcos-j2ee-legacy-examples/master/Installation/grafana.json


