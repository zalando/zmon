ZMON
====

.. image:: https://readthedocs.org/projects/zmon/badge/?version=latest
   :target: https://readthedocs.org/projects/zmon/?badge=latest
   :alt: Documentation Status

ZMON is Zalando's monitoring tool.

Build everything from source
============================

Use the master build script to build everything from source:

.. code-block:: bash

    $ ./build.sh

Start Vagrant demo cluster
==========================

You need to run ``build.sh`` first.
Install a recent Vagrant version and simply do:

.. code-block:: bash

    $ vagrant up

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
