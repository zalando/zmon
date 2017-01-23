Starting ZMON using Docker Compose
==================================

This will run all the components locally:

```
    docker-compose -f zmon-compose.yaml up
```

Once things are up run once:

```
    # script calling the zmon cli
    ./inject.sh
```

This will insert some example entities, alerts and checks.

Now open: [ZMON(localhost)](https://localhost:8443)

Issues
======

KairosDB may need a restart if it does not come up - health seems to only work the first time.

```
  docker restart compose_kairosdb_1
```

Requirements
============

 * docker-compose version 1.10+
 * docker 1.13

 Install from: https://docs.docker.com/compose/install/
