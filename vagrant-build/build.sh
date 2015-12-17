#!/bin/bash

COLOR_PROGRESS='\e[1;34m'
COLOR_FAIL='\e[1;31m'
COLOR_RESET='\e[0m' # No Color

function fail {
    echo -e "${COLOR_FAIL}ERROR: $1${COLOR_RESET}"
    exit 1
}

function error {
    echo -e "${COLOR_FAIL}ERROR: $1${COLOR_RESET}"
}

function progress {
    echo -e "${COLOR_PROGRESS}$1..${COLOR_RESET}"
}

echo "  ________  __  ____  _   _ "
echo " |___  /  \/  |/ __ \| \ | |"
echo "    / /| \  / | |  | |  \| |"
echo "   / / | |\/| | |  | | . \` |"
echo "  / /__| |  | | |__| | |\  |"
echo " /_____|_|  |_|\____/|_| \_|"

progress 'Checking prerequisites'
git --version > /dev/null || fail "git is required"

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | grep -o '1\.[78]')
[ "v$JAVA_VERSION" = "v1.8" ] || fail "Java 1.8 is required"

PYTHON_VERSION=$(python --version 2>&1 | grep -o '2\.7')
[ "v$PYTHON_VERSION" = "v2.7" ] || fail "Python 2.7 is required"

cd /home/vagrant

if [ "b$1" = "b" ] || [ "b$1" = "bcontroller" ] ; then
    progress 'Building Controller'
    git clone https://github.com/zalando/zmon-controller.git
    (cd zmon-controller && ./mvnw clean package && docker build -t zmon-controller .)
fi

if [ "b$1" = "b" ] || [ "b$1" = "beventlog-service" ] ; then
    progress 'Building Eventlog Service'
    git clone https://github.com/zalando/zmon-eventlog-service.git
    (cd zmon-eventlog-service && ./mvnw clean package && docker build -t zmon-eventlog-service .)
fi

if [ "b$1" = "b" ] || [ "b$1" = "bdata-service" ] ; then
    progress 'Building Data Service'
    git clone https://github.com/zalando/zmon-data-service.git
    (cd zmon-data-service && ./mvnw clean package && docker build -t zmon-data-service .)
fi

if [ "b$1" = "b" ] || [ "b$1" = "bscheduler" ] ; then
    progress 'Building Scheduler'
    git clone https://github.com/zalando/zmon-scheduler-ng.git zmon-scheduler
    (cd zmon-scheduler && ./mvnw clean package && docker build -t zmon-scheduler .)
fi

if [ "b$1" = "b" ] || [ "b$1" = "bworker" ] ; then
    progress 'Building Worker'
    git clone https://github.com/zalando/zmon-worker.git
    (cd zmon-worker && docker build -t zmon-worker .)
fi
