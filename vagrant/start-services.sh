#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

export EVENTLOG_VERSION=0.1.3
export WORKER_VERSION=0.1.3
export CONTROLLER_VERSION=0.1.7
export SCHEDULER_VERSION=0.1.8

if [ "b$1" = "b" ] || [ "b$1" = "beventlog-service" ] ; then
    docker rm zmon-eventlog-service
    docker run --name zmon-eventlog-service --net host -e POSTGRESQL_USER=$PGUSER -e POSTGRESQL_PASSWORD=$PGPASSWORD -d os-registry.stups.zalan.do/stups/zmon-eventlog-service:$EVENTLOG_VERSION

    until curl http://localhost:8081/\?key=alertId\&value=3\&types=212993 &> /dev/null; do
        echo 'Waiting for eventlog service'
        sleep 3
    done
fi

if [ "b$1" = "b" ] || [ "b$1" = "bcontroller" ] ; then
   
    docker rm zmon-controller
    docker run --name zmon-controller --net host -d os-registry.stups.zalan.do/stups/zmon-controller:$CONTROLLER_VERSION

    until curl http://localhost:8080/index.jsp &> /dev/null; do
        echo 'Waiting for ZMON Controller..'
        sleep 3
    done
fi

if [ "b$1" = "b" ] || [ "b$1" = "bworker" ] ; then
    docker rm zmon-worker
    docker run --name zmon-worker --net host -d os-registry.stups.zalan.do/stups/zmon-worker:$WORKER_VERSION
fi

if [ "b$1" = "b" ] || [ "b$1" = "bscheduler" ] ; then
    docker rm zmon-scheduler
    docker run --name zmon-scheduler --net host -d os-registry.stups.zalan.do/stups/zmon-scheduler-ng:$SCHEDULER_VERSION
fi
