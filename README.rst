ZMON
====

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON is Zalando's platform monitoring tool

Take a look at slides from our recent talk at DevOps Ireland Meetup:

https://tech.zalando.com/blog/zmon-zalandos-open-source-monitoring-tool-slides/

A introduction on how it started:

https://tech.zalando.com/blog/monitoring-the-zalando-platform/

Originating in the hackweek end of 2013, ZMON became our replacement of Nagios/Icinga and has been in use to monitor our platform since then. Today our production ZMON features close to 2000 check definitions and about 4500 alert definitions for various teams, mostly within Zalando's Tech department.

Features / Working:
 * Define checks as data sources executed on self defined entities
 * Define alerts on checks and entities as it fits your team with thresholds
 * Define custom dashboards with widgets and alert filters base on teams and tags
 * Check command and Alert condition are arbitrary Python expressions, giving you a lot of power
 * Store all results, incl. flattened dicts in time series in KairosDB
 * Internal charting and integrated Grafana for dash boards
 * Entity service to push entities, e.g. hosts, databases, ... we push ec2, elbs, ... via zmon-aws-agent
 * Define checks via yaml files and push using zmon-cli or via discovery from git sources
 * Use trial run in the UI to develop your checks/alerts with quick feedback
 * Trigger instant evaluation from UI for checks on longer intervals to rerun commands

Start Demo using Vagrant
========================

Install a recent Vagrant_ version (at least 1.6) and simply do:

.. code-block:: bash

    $ vagrant up

Please note that the provisioning process will take some time as it downloads the docker images (~15min).

The ZMON frontend: http://localhost:38080/ and login with username "admin" and password "admin".

Integrated Grafana: http://localhost:38080/grafana/ - You will be able to create/save dashboards.

KairosDB frontend, i.e. for manually query of metrics, via http://localhost:38083/

Issues with the Vagrant box:

* every LDAP user has admin role (because I could not get the OpenLDAP "memberOf" overlay to work

* If single containers do not start up ssh into the vagrant box and run the start.sh script again manually or use the start-services.sh script to restart single components. Later one takes parameters like controller or worker.

Install the command line interface
==================================

Use PIP to install the ``zmon`` executable from PyPI_.

.. code-block:: bash

    $ sudo pip3 install --upgrade zmon-cli

Use the zmon cli to push/create/update entities ( e.g. hosts, databases, ...), check definitons and optionally alerts (also possible via UI).

.. code-block:: bash

    $ zmon entities push examples/entities/local-postgresql.yaml

    $ zmon entities push examples/entities/local-scheduler-instance.json

Push your first check definition:

.. code-block:: bash

    $ zmon check-definitions update examples/check-definitions/zmon-scheduler-rates.yaml

Modify the alert defintion to point to the right check id, before doing:

.. code-block:: bash

    $ zmon alert-definitions update examples/alert-definitions/scheduler-rate-too-low.yaml


.. _Vagrant: https://www.vagrantup.com/
.. _PyPI: https://pypi.python.org/pypi/zmon-cli

Thanks
======

Docker images/scripts used in slightly modified version are:

* abh1nav/cassandra:latest
* wangdrew/kairosdb
* official Redis and PostgreSQL

Thanks to the original authors!

License
=======

Copyright 2013-2015 Zalando SE

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
