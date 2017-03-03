Starting ZMON using Docker Compose
==================================

This will run all the components locally:

```
    docker-compose -f zmon-compose.yaml up --build
```

Once things are up run once:

```
    # script calling the zmon cli
    ./inject.sh
```

This will insert some example entities, alerts and checks.

Now open: [ZMON(localhost)](https://localhost:8443)

Data by default goes into `postgresql-data` and `cassandra-data` mounted as volumes.

Recreate containers
===================

```
    docker-compose -f zmon-compose.yaml up --build --force-recreate
```

Logs
====

To look at individual container logs use:

```
   docker ps

   docker logs compose_controller_1
```

Issues
======

KairosDB may need a restart if it does not come up - health seems to only work the first time.

```
  docker restart compose_kairosdb_1
```

Requirements
============

 * docker-compose version 1.10+ [Docker Compose](https://github.com/docker/compose/releases)
 * docker 1.13
