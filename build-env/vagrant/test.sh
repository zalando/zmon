#!/bin/bash

set -e
 
if [ `id -u` -ne 0 ]; then
  echo "You need root privileges to run this script"
  exit 1
fi

# Xvfb

XVFB=/usr/bin/Xvfb
PIDFILE=/var/run/Xvfb.pid
XVFB_ARGS=":10 -extension RANDR -noreset -ac -screen 10 1024x768x16"

echo "Starting Xvfb..."
start-stop-daemon --start --quiet --oknodo --pidfile $PIDFILE --background --make-pidfile \
    --exec $XVFB -- $XVFB_ARGS

if ps aux | grep "Xvfb"> /dev/null
then
    export DISPLAY=:10
    cd /home/vagrant/zmon-controller/src/main/webapp/
    gulp test
    start-stop-daemon --stop --pidfile $PIDFILE
else
    echo "Something went wrong, Xvfb doesn't seem to be running."
fi



