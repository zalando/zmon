ZMON
====

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON is Zalando's monitoring tool, to get a quick look at what it does for us, read our blog article about it:

http://tech.zalando.com/posts/monitoring-the-zalando-platform.html

Start Demo using Vagrant
========================

Install a recent Vagrant_ version (at least 1.6) and simply do:

.. code-block:: bash

    $ vagrant up

Please note that the provisioning process will take some time as it downloads the docker images.

The ZMON Controller frontend will be exposed on port 38080 on localhost, i.e. point your browser to http://localhost:38080/ and login with username "admin" and password "admin".

To access Grafana which is deployed with the ZMON Controller, goto: http://localhost:38080/grafana. You will be able to create/save dashboards.

The KairosDB frontend will be exposed on 38083 on localhost, i.e. you can manually query metrics on http://localhost:38083/

Issues with the Vagrant box:

* every LDAP user has admin role (because I could not get the OpenLDAP "memberOf" overlay to work

Install the command line interface
==================================

Use PIP to install the ``zmon`` executable from PyPI_.

.. code-block:: bash

    $ sudo pip3 install --upgrade zmon-cli

Use the zmon cli to push/create/update entities ( e.g. hosts, databases, ...), check definitons and optionally alerts (also possible via UI).

Build components from source locally
====================================

Inside the ./vagrant-build folder you will find the old Vagrant setup, that includes cloning and compiling from source, but for a Demo this was just taking too much time.

The ``vagrant up`` will automatically build all components from source inside the Vagrant box,
but you can also build them manually on your local machine.
You need Java 7 or 8, Maven 3 and Python 2.7:

.. code-block:: bash

    $ ./build.sh

ToDos
=====

* add documentation (architecture, operations manual, etc)

.. _Vagrant: https://www.vagrantup.com/
.. _PyPI: https://pypi.python.org/pypi/zmon-cli

Thanks
======

  Docker images/scripts used in slightly modified version are:

  * abh1nav/cassandra:latest
  * wangdrew/kairosdb
  * official Redis and PostgreSQL
  
  Thanks to the original authors!
