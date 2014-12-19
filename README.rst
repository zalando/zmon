ZMON
====

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON is Zalando's monitoring tool.

Build everything from source and start Vagrant demo cluster
===========================================================

Install a recent Vagrant_ version and simply do:

.. code-block:: bash

    $ vagrant up

This will start a new Vagrant box and install all dependencies, build all components and start them.

The ZMON Controller frontend will be exposed on 38080 on localhost, i.e. point your browser to http://localhost:38080/ and login with username "admin" and password "admin".

The KairosDB frontend will be exposed on 38083 on localhost, i.e. you can manually query metrics on http://localhost:38083/

Issues with the Vagrant box:

* every LDAP user has admin role (because I could not get the OpenLDAP "memberOf" overlay to work)
* no entity adapters are configured (except "cities")
* many configuration options are hardcoded

Install the command line interface
==================================

.. code-block:: bash

    $ sudo pip3 install --upgrade zmon-cli

ToDos
=====

This project is in catastrophic shape and has many to-dos:

* fix unit tests and setup CI (e.g. Travis)
* implement pluggable entity adapters and check functions
* find solution to replace EventLog Service
* remove CherryPy dependency from zmon-scheduler and zmon-worker (use YAML config file instead)
* fix all hardcoded configurations
* remove unnecessary files (e.g. unused JS libs)
* fix code formatting (flake8 for Python, jshint for JS, ..)
* add documentation (architecture, operations manual, etc)

.. _Vagrant: https://www.vagrantup.com/
