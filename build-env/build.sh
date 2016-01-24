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

function clone_or_pull {
    if [ -d $1 ]; then
        cd $1; git pull; cd ..
    else
        git clone https://github.com/zalando/$1.git
    fi
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

DIR=${2:-"/home/vagrant"}
cd $DIR || fail "${DIR} does not exist"

if [ "b$1" = "b" ] || [ "b$1" = "bcontroller" ] ; then
    progress 'Building Controller'
    clone_or_pull zmon-controller
    (cd zmon-controller && ./mvnw clean package && scm-source -f target/scm-source.json && docker build -t zmon-controller .) || fail "Error building Controller"
fi

if [ "b$1" = "b" ] || [ "b$1" = "beventlog-service" ] ; then
    progress 'Building Eventlog Service'
    clone_or_pull zmon-eventlog-service
    (cd zmon-eventlog-service && ./mvnw clean package && scm-source -f target/scm-source.json && docker build -t zmon-eventlog-service .) || fail "Error building Eventlog Service"
fi

if [ "b$1" = "b" ] || [ "b$1" = "bdata-service" ] ; then
    progress 'Building Data Service'
    clone_or_pull zmon-data-service
    (cd zmon-data-service && ./mvnw clean package && docker build -t zmon-data-service .) || fail "Error building Data Service"
fi

if [ "b$1" = "b" ] || [ "b$1" = "bscheduler" ] ; then
    progress 'Building Scheduler'
    clone_or_pull zmon-scheduler
    (cd zmon-scheduler && ./mvnw clean package && scm-source && docker build -t zmon-scheduler .) || fail "Error building Scheduler"
fi

if [ "b$1" = "b" ] || [ "b$1" = "bworker" ] ; then
    progress 'Building Worker'
    clone_or_pull zmon-worker
    (cd zmon-worker && scm-source && docker build -t zmon-worker .) || fail "Error building Worker"
fi
