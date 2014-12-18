========
ZMON CLI
========

Requires Python 3.4.

Installation
============

.. code-block:: bash

    $ sudo pip3 install --upgrade zmon-cli

Usage
=====

Creating or updating a single check definition from its YAML file:

.. code-block:: bash

    $ zmon check-definitions update examples/check-definitions/zmon-stale-active-alerts.yaml
