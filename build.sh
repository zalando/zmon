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

MAVEN_VERSION=$(mvn --version | head -n 1 | grep -o '3\.')
[ "v$MAVEN_VERSION" = "v3." ] || fail "Maven 3 is required"

JAVA_VERSION=$(java -version 2>&1 | head -n 1 | grep -o '1\.[78]')
[ "v$JAVA_VERSION" = "v1.8" -o "v$JAVA_VERSION" = "v1.7" ] || fail "Java 1.7 or 1.8 is required"

PYTHON_VERSION=$(python --version 2>&1 | grep -o '2\.7')
[ "v$PYTHON_VERSION" = "v2.7" ] || fail "Python 2.7 is required"

progress 'Building KairosDB Client'
git clone https://github.com/zalando/kairosdb-client.git
# we need to skip tests as KairosDB client tries to start embedded server :-P
(cd kairosdb-client && mvn clean install -Dmaven.test.skip=true -Dgpg.skip=true)

progress 'Building Controller'
git clone https://github.com/zalando/zmon-controller.git
(cd zmon-controller && mvn clean package && docker build -t zmon-controller .)

progress 'Building Scheduler'
git clone https://github.com/zalando/zmon-scheduler.git
(cd zmon-scheduler && docker build -t zmon-scheduler .)

progress 'Building Worker'
git clone https://github.com/zalando/zmon-worker.git
(cd zmon-worker && docker build -t zmon-worker .)
