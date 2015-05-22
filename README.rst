ZMON
====

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON is Zalando's monitoring tool, to get a quick look at what it does for us, read our blog article about it:

http://tech.zalando.com/posts/monitoring-the-zalando-platform.html

Build everything and start Vagrant demo cluster
===============================================

Install a recent Vagrant_ version (at least 1.6) and simply do:

.. code-block:: bash

    $ vagrant up

This will start a new Vagrant box and install all dependencies, build all components and start them.

Please note that the provisioning process will take quite some time as many tools and dependencies need to be downloaded.

The ZMON Controller frontend will be exposed on 38080 on localhost, i.e. point your browser to http://localhost:38080/ and login with username "admin" and password "admin".

The KairosDB frontend will be exposed on 38083 on localhost, i.e. you can manually query metrics on http://localhost:38083/

Issues with the Vagrant box:

* every LDAP user has admin role (because I could not get the OpenLDAP "memberOf" overlay to work

Install the command line interface
==================================

Use PIP to install the ``zmon`` executable from PyPI_.

.. code-block:: bash

    $ sudo pip3 install --upgrade zmon-cli

Build components from source locally
====================================

The ``vagrant up`` will automatically build all components from source inside the Vagrant box,
but you can also build them manually on your local machine.
You need Java 7 or 8, Maven 3 and Python 2.7:

.. code-block:: bash

    $ ./build.sh

ToDos
=====

* fix unit tests and setup CI (e.g. Travis)
* find solution to replace EventLog Service
* remove CherryPy dependency from zmon-worker (use YAML config file instead)
* fix all hardcoded configurations
* remove unnecessary files (e.g. unused JS libs)
* add documentation (architecture, operations manual, etc)

.. _Vagrant: https://www.vagrantup.com/
.. _PyPI: https://pypi.python.org/pypi/zmon-cli
