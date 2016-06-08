#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

container=$(docker ps | grep postgres)
if [ -z "$container" ]; then
    docker rm postgres
    docker run --restart "on-failure:10" --name postgres --net host -e POSTGRES_PASSWORD=postgres -d registry.opensource.zalan.do/stups/postgres:9.4.5-1
fi

until nc -w 5 -z localhost 5432; do
    echo 'Waiting for Postgres port..'
    sleep 3
done

cd /home/vagrant/zmon-controller/database/zmon
psql -c "CREATE DATABASE $PGDATABASE;" postgres
psql -c 'CREATE EXTENSION IF NOT EXISTS hstore;'

# creating demo role here
psql -c "CREATE ROLE zmon WITH LOGIN PASSWORD '--secret--';" postgres

find -name '*.sql' | sort | xargs cat | psql
psql -f /home/vagrant/zmon-eventlog-service/database/eventlog/00_create_schema.sql

container=$(docker ps | grep redis)
if [ -z "$container" ]; then
    docker rm redis
    docker run --restart "on-failure:10" --name redis --net host -d registry.opensource.zalan.do/stups/redis:3.0.5
fi

until nc -w 5 -z localhost 6379; do
    echo 'Waiting for Redis port..'
    sleep 3
done

ip=$(ip -o -4 a show eth0|awk '{print $4}' | cut -d/ -f 1)

container=$(docker ps | grep cassandra)
if [ -z "$container" ]; then
    docker rm cassandra
    docker run --restart "on-failure:10" --name cassandra --net host -d registry.opensource.zalan.do/stups/cassandra:2.1.5-1
fi

until nc -w 5 -z $ip 9160; do
    echo 'Waiting for Cassandra port..'
    sleep 3
done

container=$(docker ps | grep kairosdb)
if [ -z "$container" ]; then
    docker rm kairosdb
    docker run --restart "on-failure:10"  --name kairosdb --net host -d \
        -e "KAIROSDB_JETTY_PORT=8083"\
        -e "KAIROSDB_DATASTORE_CASSANDRA_HOST_LIST=$ip"\
        registry.opensource.zalan.do/stups/kairosdb:cd12
fi

until nc -w 5 -z localhost 8083; do
    echo 'Waiting for KairosDB port..'
    sleep 3
done

/vagrant/vagrant/start-services.sh
/vagrant/vagrant/inject-examples.sh

echo ""
echo "All services are up, peek into Vagrantfile/README for open ports/services"
echo ""
echo "ZMON installation is done!"
echo "Point your browser to https://localhost:8443/"
echo "and login with your GitHub credentials."
echo ""
