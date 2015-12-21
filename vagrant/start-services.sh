#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

export EVENTLOG_VERSION=cd3
export WORKER_VERSION=cd39
export CONTROLLER_VERSION=cd26
export SCHEDULER_VERSION=cd14

if [ -z "$1" ] || [ "b$1" = "beventlog-service" ] ; then
    docker kill zmon-eventlog-service
    docker rm -f zmon-eventlog-service
    docker run --restart "on-failure:10" --name zmon-eventlog-service --net host -e POSTGRESQL_USER=$PGUSER -e POSTGRESQL_PASSWORD=$PGPASSWORD -d registry.opensource.zalan.do/stups/zmon-eventlog-service:$EVENTLOG_VERSION

    until curl http://localhost:8081/\?key=alertId\&value=3\&types=212993 &> /dev/null; do
        echo 'Waiting for eventlog service'
        sleep 3
    done
fi

if [ -z "$1" ] || [ "b$1" = "bcontroller" ] ; then
    docker kill zmon-controller
    docker rm -f zmon-controller
    docker run --restart "on-failure:10" --name zmon-controller --net host \
        -e SPRING_PROFILES_ACTIVE=github \
        -e ZMON_AUTHORITIES_SIMPLE_ADMINS=* \
        -e POSTGRES_URL=jdbc:postgresql://localhost:5432/local_zmon_db \
        -e REDIS_PORT=6379 \
        -e PRESHARED_TOKENS_123_UID=demotoken \
        -e PRESHARED_TOKENS_123_EXPIRES_AT=1758021422 \
        -d registry.opensource.zalan.do/stups/zmon-controller:$CONTROLLER_VERSION

    until curl --insecure https://localhost:8443/index.jsp &> /dev/null; do
        echo 'Waiting for ZMON Controller..'
        sleep 3
    done
fi

if [ -z "$1" ] || [ "b$1" = "bworker" ] ; then
    docker kill zmon-worker
    docker rm -f zmon-worker
    docker run --restart "on-failure:10" --name zmon-worker --net host \
        -d registry.opensource.zalan.do/stups/zmon-worker:$WORKER_VERSION
fi

if [ -z "$1" ] || [ "b$1" = "bscheduler" ] ; then
    docker kill zmon-scheduler
    docker rm -f zmon-scheduler
    docker run --restart "on-failure:10" --name zmon-scheduler --net host \
        -v /home/vagrant/zmon-controller/zmon-controller-app/src/main/resources:/resources \
        -e JAVA_OPTS="-Djavax.net.ssl.trustStorePassword=mypassword -Djavax.net.ssl.trustStore=/resources/keystore.p12" \
        -e SCHEDULER_URLS_WITHOUT_REST=true \
        -e SCHEDULER_ENTITY_SERVICE_URL=https://localhost:8443/ \
        -e SCHEDULER_ENTITY_SERVICE_TOKEN=123 \
        -e SCHEDULER_CONTROLLER_URL=https://localhost:8443/ \
        -e SCHEDULER_CONTROLLER_TOKEN=123 \
        -d registry.opensource.zalan.do/stups/zmon-scheduler-ng:$SCHEDULER_VERSION
fi
