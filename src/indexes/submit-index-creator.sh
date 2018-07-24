#!/usr/bin/env bash
dcos spark run --submit-args="--conf spark.mesos.executor.docker.image=markfjohnson/cassandra_spark https://downloads.mesosphere.com/spark/examples/pi.py 30" --verbose --name=spark
