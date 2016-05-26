#!/bin/bash

EXAMPLES=/vagrant/examples

for f in $EXAMPLES/check-definitions/*.yaml; do
    zmon check-definitions update $f
done
for f in $EXAMPLES/entities/*.yaml; do
    zmon entities push $f
done
for f in $EXAMPLES/alert-definitions/*.yaml; do
    zmon alert-definitions create $f
done
for f in $EXAMPLES/dashboards/*.yaml; do
    # ZMON CLI updates the YAML file (sic!),
    # so use a temporary one
    temp=${f}.temp
    cp $f $temp
    zmon dashboard update $temp
    rm $temp
done

# get rid of CLI log
rm -fr /tmp/zmon-cli.log
