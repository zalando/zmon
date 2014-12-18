ZMON
====

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

Issues with the Vagrant box:

* every LDAP user has admin role (because I could not get the OpenLDAP "memberOf" overlay to work)

The ZMON Controller frontend will be exposed on 38080 on localhost, i.e. point your browser to http://localhost:38080/ and login with username "admin" and password "admin".
