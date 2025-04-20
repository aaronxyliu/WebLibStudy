#!/bin/sh

brew install mysql-client pkg-config
$ export PKG_CONFIG_PATH="$(brew --prefix)/opt/mysql-client/lib/pkgconfig"
pip3 install urllib3 pandas mysqlclient python-dotenv matplotlib