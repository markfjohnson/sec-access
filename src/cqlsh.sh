#!/usr/bin/env bash
 dcos task exec -ti cassandra-client cqlsh node-0-server.cassandra.autoip.dcos.thisdcos.directory 9042
