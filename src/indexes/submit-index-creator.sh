#!/usr/bin/env bash
dcos spark run --submit-args="--conf spark.mesos.executor.docker.image=markfjohnson/cassandra_spark https://raw.githubusercontent.com/markfjohnson/sec-access/master/src/indexes/download_sec_Index.py -f 2018 -t 2019" --verbose --name=spark
