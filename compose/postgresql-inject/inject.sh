#!/bin/bash

export PGHOST=postgresql
export PGUSER=postgres
export PGPASSWORD=$POSTGRESQL_PASSWORD
export PGDATABASE=local_zmon_db

psql -c "CREATE DATABASE $PGDATABASE;" postgres
psql -c 'CREATE EXTENSION IF NOT EXISTS hstore;'
psql -c "CREATE ROLE zmon WITH LOGIN PASSWORD '--secret--';" postgres

