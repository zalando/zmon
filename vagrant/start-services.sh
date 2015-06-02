#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

export IMAGE_VERSION=0.1.4

if [ "b$1" = "b" ] || [ "b$1" = "beventlog-service" ] ; then
    docker rm zmon-eventlog-service
    docker run --name zmon-eventlog-service --net host -e POSTGRESQL_USER=$PGUSER -e POSTGRESQL_PASSWORD=$PGPASSWORD -d os-registry.stups.zalan.do/stups/zmon-eventlog-service:$IMAGE_VERSION

    until curl http://localhost:8081/\?key=alertId\&value=3\&types=212993 &> /dev/null; do
        echo 'Waiting for eventlog service'
        sleep 3
    done
fi

if [ "b$1" = "b" ] || [ "b$1" = "bcontroller" ] ; then
   
    docker rm zmon-controller
    docker run --name zmon-controller --net host -d os-registry.stups.zalan.do/stups/zmon-controller:$IMAGE_VERSION

    until curl http://localhost:8080/index.jsp &> /dev/null; do
        echo 'Waiting for ZMON Controller..'
        sleep 3
    done
fi

for comp in scheduler-ng worker data-service; do
    if [ "b$1" = "b" ] || [ "b$1" = "b$comp" ] ; then
        docker rm zmon-$comp
        docker run --name zmon-$comp --net host -d os-registry.stups.zalan.do/stups/zmon-$comp:$IMAGE_VERSION
    fi
done
