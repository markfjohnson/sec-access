#!/usr/bin/env bash
dcos spark run --submit-args="--conf spark.mesos.executor.docker.image=markfjohnson/cassandra_spark https://raw.githubusercontent.com/markfjohnson/sec-access/master/src/indexes/xbrl_rss_reader.py -f 2018 -t 2018" --verbose --name=spark
