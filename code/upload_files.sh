#!/bin/bash

PROXY=$1

for file in test-upgrade.sh test-script.sh ~victor/revsw-proxy-config_1.0.257.deb ~victor/revsw-*_4.0.3-23* ~victor/libwurfl-1.8.0.0-x86_64.deb ~victor/varnish-mod-wurfl-1.8.0.0.varnish-4.0.3.x86_64.deb; do

  echo $file
  target=`basename $file`
  echo $target
  ./rs upload_file $file $target $PROXY

done
