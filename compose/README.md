Usage
=====

```
    docker-compose -f zmon-compose.yaml up
```

Once things are up run:

```
./inject.sh
```

This will insert some example entities, alerts and checks.

Issues
======

KairosDB may need a restart if it does not come up - health check only works first time.

```
  docker restart compose_kairosdb_1
```

Requires
--------

 * docker-compose version 1.10+

 Install from: https://docs.docker.com/compose/install/
