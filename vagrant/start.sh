#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

container=$(docker ps | grep postgres:9.3.5)
if [ -z "$container" ]; then
    docker rm postgres
    docker run --name postgres --net host -e POSTGRES_PASSWORD=postgres -d postgres:9.3.5
fi

until nc -w 5 -z localhost 5432; do
    echo 'Waiting for Postgres port..'
    sleep 3
done

cd /vagrant/zmon-controller/database/zmon
psql -c "CREATE DATABASE $PGDATABASE;" postgres
psql -c 'CREATE EXTENSION hstore;'
find -name '*.sql' | sort | xargs cat | psql
psql -f /vagrant/vagrant/initial.sql

container=$(docker ps | grep openldap)
if [ -z "$container" ]; then
    docker rm openldap
    docker run --name openldap --net host -d zalando/slapd
fi

until nc -w 5 -z localhost 389; do
    echo 'Waiting for LDAP port..'
    sleep 3
done

ldapadd -c -x -D cn=admin,dc=example,dc=com -w toor -f /vagrant/vagrant/ldap-structure.ldif

container=$(docker ps | grep redis)
if [ -z "$container" ]; then
    docker rm redis
    docker run --name redis --net host -d redis
fi

until nc -w 5 -z localhost 6379; do
    echo 'Waiting for Redis port..'
    sleep 3
done

ip=$(ip -o -4 a show eth0|awk '{print $4}' | cut -d/ -f 1)

container=$(docker ps | grep cassandra)
if [ -z "$container" ]; then
    docker rm cassandra
    docker run --name cassandra --net host -d abh1nav/cassandra:latest
fi

until nc -w 5 -z $ip 9160; do
    echo 'Waiting for Cassandra port..'
    sleep 3
done

container=$(docker ps | grep kairosdb)
if [ -z "$container" ]; then
    docker rm kairosdb
    docker run --name kairosdb --net host -d -e "CASSANDRA_HOST_LIST=$ip:9160" wangdrew/kairosdb
fi

until nc -w 5 -z localhost 8083; do
    echo 'Waiting for KairosDB port..'
    sleep 3
done

lroot=/vagrant/zmon-controller
snap=$lroot/target/zmon-controller-1.0.1-SNAPSHOT
lwebapp=$lroot/src/main/webapp
croot=/usr/local/tomcat
cwebapp=$croot/webapps/ROOT

docker rm zmon-controller
docker run --name zmon-controller --net host -d \
    -v $snap:$cwebapp \
    -v $lwebapp/asset/:$cwebapp/asset/ \
    -v $lwebapp/js/:$cwebapp/js/ \
    -v $lwebapp/lib/:$cwebapp/lib/ \
    -v $lwebapp/styles/:$cwebapp/styles/ \
    -v $lwebapp/templates/:$cwebapp/templates/ \
    -v $lwebapp/views/:$cwebapp/views/ \
    zmon-controller

ln -fs $lwebapp/index.jsp $snap/index.jsp
ln -fs $lwebapp/login.jsp $snap/login.jsp
ln -fs $lwebapp/logo.jsp $snap/logo.png
ln -fs $lwebapp/favicon.ico $snap/favicon.ico
ln -fs $lwebapp/package.json $snap/package.json

until curl http://localhost:8080/index.jsp &> /dev/null; do
    echo 'Waiting for ZMON Controller..'
    sleep 3
done

for comp in scheduler worker; do
    docker rm zmon-$comp
    docker run --name zmon-$comp --net host -d zmon-$comp
done
