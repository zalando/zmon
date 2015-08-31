#!/bin/bash

rm /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

#apt-get remove --purge -y puppet chef
#apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

  wget -qO- https://get.docker.com/ubuntu | sh

fi

adduser vagrant docker

#echo "DOCKER_OPTS=\"--storage-driver=aufs\"" > /etc/default/docker

apt-get install -y postgresql-client ldap-utils git redis-tools python3-pip

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass

echo -e "redis_host: localhost\nurl: http://localhost:8080/rest/api/v1\nuser: admin\npassword: admin" > /home/vagrant/.zmon-cli.yaml

sudo pip3 install --upgrade zmon-cli

chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass

mkdir -p /home/vagrant/zmon-controller
git clone https://github.com/zalando/zmon-controller.git  /home/vagrant/zmon-controller

mkdir -p /home/vagrant/zmon-eventlog-service
git clone https://github.com/zalando/zmon-eventlog-service.git  /home/vagrant/zmon-eventlog-service
