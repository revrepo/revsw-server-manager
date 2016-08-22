#!/bin/bash

/etc/init.d/revsw-pcm-config stop
/etc/init.d/revsw-pcm-purge stop
sudo dpkg -i libwurfl-1.8.0.0-x86_64.deb
sudo dpkg -i varnish-mod-wurfl-1.8.0.0.varnish-4.0.3.x86_64.deb

sudo dpkg -i revsw-libvarnish4api_4.0.3-23_amd64.deb
sudo dpkg -i revsw-varnish4-modules_4.0.3-23_amd64.deb
sudo dpkg -i revsw-varnish4_4.0.3-23_amd64.deb

sudo dpkg -i revsw-proxy-config_1.0.257.deb

sudo /opt/revsw-config/bin/pc-apache-config.py -U

/etc/init.d/revsw-pcm-config start
/etc/init.d/revsw-pcm-purge start
