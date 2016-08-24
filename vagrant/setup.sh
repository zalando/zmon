#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

rm -f /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

#apt-get remove --purge -y puppet chef
#apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

  apt-key adv --keyserver hkp://pgp.mit.edu:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

  echo -e "deb https://apt.dockerproject.org/repo ubuntu-wily main" > /etc/apt/sources.list.d/docker.list

  apt-get -y update
  apt-get -y install docker-engine libffi-dev libssl-dev

fi

adduser vagrant docker

apt-get install -y postgresql-client git redis-tools python3-pip

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass

# we use a preshared token for authentication (configured when starting ZMON Controller)
echo -e "url: https://localhost:8443/api/v1\ntoken: 123\nverify: false" > /home/vagrant/.zmon-cli.yaml
# configure for root user too (setup is running as root)
cp /home/vagrant/.zmon-cli.yaml /root/.zmon-cli.yaml

echo -e "export LC_ALL=en_US.utf-8\nexport LANG=en_US.utf-8\n" >> /home/vagrant/.profile

sudo easy_install3 -U pip
sudo pip3 install --upgrade zmon-cli

chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass

mkdir -p /home/vagrant/zmon-controller
git clone https://github.com/zalando/zmon-controller.git /home/vagrant/zmon-controller || (cd /home/vagrant/zmon-controller && git pull)

mkdir -p /home/vagrant/zmon-eventlog-service
git clone https://github.com/zalando/zmon-eventlog-service.git /home/vagrant/zmon-eventlog-service || (cd /home/vagrant/zmon-eventlog-service && git pull)
