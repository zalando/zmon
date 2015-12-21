=========================
ZMON - Build from scratch
=========================

This "build-env" Vagrant box is only provided as convenience
in order to build all ZMON components from source.

Build components from source locally
====================================

The ``vagrant up`` will automatically build all components from source inside the Vagrant box,
but you can also build them manually on your local machine.
You need Java 8 and Python 2.7:

.. code-block:: bash

    $ ./build.sh

.. _Vagrant: https://www.vagrantup.com/
.. _PyPI: https://pypi.python.org/pypi/zmon-cli
