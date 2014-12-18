#!/bin/bash

rm /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

apt-get remove --purge -y puppet chef
apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

    # add Docker repo
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 36A1D7869245C8950F966E92D8576A8BA88D21E9
    echo 'deb https://get.docker.io/ubuntu docker main' > /etc/apt/sources.list.d/docker.list

    set +e
    until apt-get update; do
        # TODO: this should not even be necessary
        echo 'apt-get update failed, retrying..'
        rm -fr /var/lib/apt/lists/partial
        sleep 1
    done
    set -e

    # Docker
    apt-get install -y --no-install-recommends -o Dpkg::Options::="--force-confold" apparmor lxc-docker
fi

adduser vagrant docker

apt-get install -y postgresql-client ldap-utils

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass
chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass
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
    docker run --name openldap --net host -d hjacobs/slapd
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

for comp in controller scheduler worker; do
    docker load < /vagrant/zmon-$comp/zmon-${comp}.tar
    docker rm zmon-$comp
    docker run --name zmon-$comp --net host -d zmon-$comp

    if [ "$comp" = "controller" ]; then
        until curl http://localhost:8080/index.jsp &> /dev/null; do
            echo 'Waiting for ZMON Controller..'
            sleep 3
        done
    fi
done
