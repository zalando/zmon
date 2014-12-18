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


