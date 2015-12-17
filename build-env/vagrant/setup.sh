#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

rm /etc/update-motd.d/*
cp /vagrant/vagrant/etc/update-motd.d/* /etc/update-motd.d/

apt-get remove --purge -y puppet chef
apt-get autoremove -y

if [ ! -x "/usr/bin/docker" ]; then

  apt-key adv --keyserver hkp://pgp.mit.edu:80 --recv-keys 58118E89F3A912897C070ADBF76221572C52609D

  echo -e "deb https://apt.dockerproject.org/repo ubuntu-vivid main" > /etc/apt/sources.list.d/docker.list

  apt-get -y update

  apt-get -y install docker-engine
fi

adduser vagrant docker

#echo "DOCKER_OPTS=\"--storage-driver=aufs\"" > /etc/default/docker

apt-get -y update

apt-get install -y openjdk-8-jdk

# NOTE: maven is installed by the Maven Wrapper (mvnw), we do not need to install it here
apt-get install -y postgresql-client git redis-tools

# install dependencies for acceptance and unit testing
apt-get install -y x11-xkb-utils xfonts-100dpi xfonts-75dpi xfonts-scalable xserver-xorg-core dbus-x11
apt-get install -y npm nodejs-legacy xvfb chromium-browser firefox
npm install -g gulp protractor chromedriver

echo 'localhost:5432:*:postgres:postgres' > /root/.pgpass
chmod 600 /root/.pgpass
cp /root/.pgpass /home/vagrant/.pgpass

# to run integration tests:
mkdir /root/.m2
echo '<settings><servers><server><id>testdb</id><username>postgres</username><password>postgres</password></server></servers></settings>' > /root/.m2/settings.xml

