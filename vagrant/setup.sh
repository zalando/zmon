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

apt-get install -y postgresql-client ldap-utils maven openjdk-7-jdk git

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass
chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass

