Starting ZMON using Docker Compose
==================================

This will run all the components locally:

```
    docker-compose up --build --detach
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
    docker-compose up --build --force-recreate --detach
```

Logs
====

To look at individual container logs use:

```
   docker-compose ps

   docker-compose logs controller
```

Issues
======

Cassandra might not start if there is not enough memory allocated to container. You will see "Killed" in logs or "Exit 137" in container list. To fix this on Docker Desktop for Mac, under Docker menu go to Preferences->Advanced, and increase Memory.

KairosDB may need a restart if it does not come up - health seems to only work the first time.

```
  docker-compose restart kairosdb
```

Requirements
============

 * docker-compose version 1.10+ [Docker Compose](https://github.com/docker/compose/releases)
 * docker 1.13
