#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

rm -f /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass

# we use a preshared token for authentication (configured when starting ZMON Controller)
echo -e "url: https://localhost:8443/api/v1\ntoken: 123\nverify: false" > /home/ubuntu/.zmon-cli.yaml
# configure for root user too (setup is running as root)
cp /home/ubuntu/.zmon-cli.yaml /root/.zmon-cli.yaml

echo -e "export LC_ALL=en_US.utf-8\nexport LANG=en_US.utf-8\n" >> /home/ubuntu/.profile

#apt-get remove --purge -y puppet chef
#apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

  apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

  echo -e "deb https://apt.dockerproject.org/repo ubuntu-yakkety main" > /etc/apt/sources.list.d/docker.list

  apt-get -y update
  apt-get -y install docker-engine libffi-dev libssl-dev

fi

adduser ubuntu docker

apt-get install -y libssl-dev postgresql-client git redis-tools python3-pip

sudo easy_install3 -U pipgra
sudo pip3 install -U --force-reinstall cryptography
sudo pip3 install --upgrade zmon-cli

chmod 600 /root/.pgpass
cp /root/.pgpass /home/ubuntu/.pgpass

mkdir -p /home/ubuntu/zmon-controller
git clone https://github.com/zalando/zmon-controller.git /home/ubuntu/zmon-controller || (cd /home/ubuntu/zmon-controller && git pull)

mkdir -p /home/ubuntu/zmon-eventlog-service
git clone https://github.com/zalando/zmon-eventlog-service.git /home/ubuntu/zmon-eventlog-service || (cd /home/ubuntu/zmon-eventlog-service && git pull)
