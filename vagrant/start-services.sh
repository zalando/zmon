#!/bin/bash

export PGHOST=localhost
export PGUSER=postgres
export PGPASSWORD=postgres
export PGDATABASE=local_zmon_db

if [ "b$1" = "b" ] || [ "b$1" = "beventlog-service" ] ; then
    docker rm zmon-eventlog-service
    docker run --name zmon-eventlog-service --net host -e POSTGRESQL_USER=$PGUSER -e POSTGRESQL_PASSWORD=$PGPASSWORD -d zmon-eventlog-service
fi

for comp in controller scheduler worker; do
    if [ "b$1" = "b" ] || [ "b$1" = "b$comp" ] ; then

        docker rm zmon-$comp
        docker run --name zmon-$comp --net host -d zmon-$comp

        if [ "$comp" = "controller" ]; then
            until curl http://localhost:8080/index.jsp &> /dev/null; do
                echo 'Waiting for ZMON Controller..'
                sleep 3
            done
        fi
    fi
done

#XVFB_ARGS=":10 -extension RANDR -noreset -ac -screen 10 1024x768x16" start-stop-daemon --start --quiet --oknodo \
#    --pidfile /var/run/Xvfb.pid --background --make-pidfile --exec /usr/bin/Xvfb -- $XVFB_ARGS
