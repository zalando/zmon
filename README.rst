
.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON
====

ZMON is Zalando's open-source platform monitoring tool, used in production since early 2014. It supports our many engineering teams in observing their services and metrics on various layers, from low level system metrics to team's business KPIs.

Demo
----
Head over to `demo.zmon.io <https://demo.zmon.io>`_ to take a quick peek into the UI including `Grafana3 <https://demo.zmon.io/grafana/dashboard/db/response-times>`_ (login first).

Introduction
------------

To get familiar with the ideas behind ZMON and how things work, you can take a quick dive in: `Intro <http://zmon.readthedocs.org/en/latest/intro.html>`_

Talks / Blog
------------

Take a look at the slides from our `talk at the DevOps Ireland meetup <https://tech.zalando.com/blog/zmon-zalandos-open-source-monitoring-tool-slides/>`_ for background information on ZMON.

First post about ZMON: `Monitoring the platform <https://tech.zalando.com/blog/monitoring-the-zalando-platform/>`_

Features
--------

* Define checks as data sources executed on self-defined entities
* Define alerts on checks and entities, with thresholds, as it suits your and your teams needs
* Define custom dashboards with widgets and alert filters based on teams and tags
* Check commands and alert conditions are arbitrary Python expressions, giving you a lot of power
* All metric/check data is stored as time series in KairosDB for later use
* Grafana3 is included, enabling you to build rich data driven dashboards
* Powerful REST API to integrate nicely into other tools: e.g. cmdb/deploy tools
* Entity service to store entities of any kind describing your environment
* Trial run in the UI to develop your checks/alerts with quick feedback
* Auto discovery of AWS services using ZMON's aws agent and entity service, great for AWS deployments
* Authentication via OAuth 2 e.g. GitHub
* Frontend incl. Grafana 3 requires full authentication, no need for VPN. incl. onetime tokens for office TV displays
* Command line client for easy automation and interaction with the REST API
* ZMON data service allows you to connect DCs/Regions via HTTP for federated monitoring
* Supports SQL for PostgreSQL incl. sharded deployments, MySQL, Redis, Scalyr, ...
* Supports desktop and mobile notifications via Firebase Cloud Messaging
* More on connectivity here: `Check commands <https://docs.zmon.io/en/latest/user/check-commands.html>`_

Local demo and single host deployment
=====================================

We suggest to use docker compose for deploying zmon locally or on a single host:

More here: `compose <https://github.com/zalando/zmon/tree/master/compose>`_ 

The docker compose is also the most convient way to setup a development environment.

In cases where docker compose is not an options continue on (or fall back to obsolete vagrant box).

Manual Deployment
=================

You best head for the documentation now: `Component overview <https://docs.zmon.io/en/latest/installation/components.html>`_

Requirements
------------

ZMON reliese on a few great open source products to run, which you will need to operate.

* Redis
* PostgreSQL
* Cassandra + KairosDB

This seems to be a lot, but we provide both a Vagrant box and the deployment scripts for our `demo host <https://github.com/zalando/zmon-demo/blob/master/bootstrap/bootstrap.sh>`_, lowering the bar to get started :)

Components
----------

`Frontend / Controller <https://github.com/zalando/zmon-controller>`_ UI and REST API

`Scheduler <https://github.com/zalando/zmon-scheduler>`_ Schedules check/alert execution

`Worker <https://github.com/zalando/zmon-worker>`_ Executes check/alert commands and data acquisition

Optional components
-------------------

`Data service <https://github.com/zalando/zmon-data-service>`_ Used for distributed monitoring where sites don't share network connectivity other than the Internet.

`Metric cache <https://github.com/zalando/zmon-metric-cache>`_ Fast special purpose cache for REST API metric data for ZMON's REST metrics/cloud UI


Vagrant Box (deprecated)
========================

Install a recent Vagrant_ version (at least 1.7.4) and simply do:

.. code-block:: bash

    $ vagrant up

Please note that the provisioning process will take some time (~15min) while it downloads the Docker images.

Frontend
--------

  https://localhost:8443/

Login with your own GitHub credentials (OAuth redirect).

Grafana
-------

  https://localhost:8443/grafana/

You will be able to create/save dashboards.

KairosDB
--------

KairosDB frontend, i.e. for manually query of metrics:

  http://localhost:38083/

Issues
------

* If single containers do not start up ssh into the vagrant box and run the ``start.sh`` script again manually or use the ``start-services.sh`` script to restart single components. Later one takes parameters like ``controller`` or ``worker``.

Install the Command Line Interface
==================================

Use PIP to install the ``zmon`` executable from PyPI_.

.. code-block:: bash

    $ pip3 install --upgrade zmon-cli

Use the ZMON CLI to push/create/update entities (hosts, databases, etc.), check definitions and create optional alerts (also possible via UI).

.. code-block:: bash

    $ zmon entities push examples/entities/local-postgresql.yaml

    $ zmon entities push examples/entities/local-scheduler-instance.json

Push your first check definition:

.. code-block:: bash

    $ zmon check-definitions update examples/check-definitions/zmon-scheduler-rates.yaml

Modify the alert definition to point to the right check id before doing:

.. code-block:: bash

    $ zmon alert-definitions update examples/alert-definitions/scheduler-rate-too-low.yaml


.. _Vagrant: https://www.vagrantup.com/
.. _PyPI: https://pypi.python.org/pypi/zmon-cli

Build Environment
=================

If you want to compile everything from source, you can do so with our separate "build-env" Vagrant box:

.. code-block:: bash

    $ cd build-env
    $ vagrant up

Thanks
======

Docker images/scripts used in slightly modified versions are:

* abh1nav/cassandra:latest
* wangdrew/kairosdb
* official Redis and PostgreSQL

Thanks to the original authors!

License
=======

Copyright 2013-2016 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
