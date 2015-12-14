#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

rm /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

#apt-get remove --purge -y puppet chef
#apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

  apt-key adv --keyserver hkp://pgp.mit.edu:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

  echo -e "deb https://apt.dockerproject.org/repo ubuntu-vivid main" > /etc/apt/sources.list.d/docker.list

  apt-get -y update

  apt-get -y purge lxc-docker*

  apt-cache -y policy docker-engine

  apt-get -y update

  apt-get -y install docker-engine

fi

adduser vagrant docker

#echo "DOCKER_OPTS=\"--storage-driver=aufs\"" > /etc/default/docker

apt-get install -y postgresql-client ldap-utils git redis-tools python3-pip

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass

echo -e "redis_host: localhost\nurl: http://localhost:8080/rest/api/v1\nuser: admin\npassword: admin" > /home/vagrant/.zmon-cli.yaml

echo -e "export LC_ALL=en_US.utf-8\nexport LANG=en_US.utf-8\n" >> /home/vagrant/.profile

sudo easy_install3 -U pip
sudo pip3 install --upgrade zmon-cli

chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass

mkdir -p /home/vagrant/zmon-controller
git clone https://github.com/zalando/zmon-controller.git /home/vagrant/zmon-controller || echo 'zmon-controller seems to be cloned already'

mkdir -p /home/vagrant/zmon-eventlog-service
git clone https://github.com/zalando/zmon-eventlog-service.git /home/vagrant/zmon-eventlog-service || echo 'zmon-eventlog-service seems to be cloned already'
