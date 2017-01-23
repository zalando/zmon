#!/bin/bash

export PGHOST=postgresql
export PGUSER=postgres
export PGPASSWORD=$POSTGRESQL_PASSWORD
export PGDATABASE=local_zmon_db

for i in zmon-controller zmon-eventlog-service; do
    if [ -d /workdir/$i ]; then
        rm -rf /workdir/$i
    fi

    wget https://github.com/zalando/$i/archive/master.zip -O /workdir/$i.zip
    mkdir -p /workdir/$i
    unzip /workdir/$i.zip -d /workdir/$i
    rm /workdir/$i.zip
done

cd /workdir/zmon-controller/zmon-controller-master/database/zmon

psql -c "CREATE DATABASE $PGDATABASE;" postgres
psql -c 'CREATE EXTENSION IF NOT EXISTS hstore;'
psql -c "CREATE ROLE zmon WITH LOGIN PASSWORD '--secret--';" postgres
find -name '*.sql' | sort | xargs cat | psql

psql -f /workdir/zmon-eventlog-service/zmon-eventlog-service-master/database/eventlog/00_create_schema.sql
