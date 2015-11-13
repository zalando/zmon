ZMON
====

ZMON is Zalando's open-source platform monitoring tool, used in production since early 2014. It supports our many engineering teams in observing their services and metrics on various layers, from CPU load to team KPIs.

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

Take a look at the slides from our [recent talk at the DevOps Ireland meetup](https://tech.zalando.com/blog/zmon-zalandos-open-source-monitoring-tool-slides/) for background information on ZMON.

[Here's an introduction](https://tech.zalando.com/blog/monitoring-the-zalando-platform/) on how we started the project.

[Here's more detailed documentation](http://zmon.readthedocs.org/en/latest/intro.html) than you'll find here.

Features / Working:
 * Defines checks as data sources executed on self-defined entities
 * Defines alerts on checks and entities, with thresholds, as it suits your team
 * Defines custom dashboards with widgets and alert filters based on teams and tags
 * Check commands and Alert conditions are arbitrary Python expressions, giving you a lot of power
 * Stores all results, including flattened dicts in time series, in KairosDB
 * Offers internal charting and integrated Grafana for dashboards
 * Entity service to push entities: hosts, databases, et al. We push EC2, ELB, etc. via [zmon-aws-agent](https://github.com/zalando/zmon-aws-agent)
 * Defines checks via YAML files and pushes using [zmon-cli](https://github.com/zalando/zmon-cli) or via discovery from Git sources
 * Uses trial run in the UI to develop your checks/alerts with quick feedback
 * Triggers instant evaluation from UI for checks on longer intervals to rerun commands

Start Demo Using Vagrant
========================

Install a recent Vagrant_ version (at least 1.7.4) and simply do:

.. code-block:: bash

    $ vagrant up

Please note that the provisioning process will take some time (~15min) while it downloads the Docker images.

Frontend
--------

  http://localhost:38080/

Login with username "admin" and password "admin".

Grafana
-------

  http://localhost:38080/grafana/
  
You will be able to create/save dashboards.

KairosDB
--------

KairosDB frontend, i.e. for manually query of metrics:

  http://localhost:38083/

Issues
------

* Every LDAP user has an admin role, because we could not get the OpenLDAP "memberOf" overlay to work.

* If single containers do not start up SSH into the Vagrant box and run the start.sh script again manually, or use the start-services.sh script to restart single components, later ones take parameters like controller or worker.

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

Thanks
======

Docker images/scripts used in slightly modified versions are:

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
