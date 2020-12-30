#!/usr/bin/env bash

if [ ! -d /var/log/squid ]
then
    echo "FATAL - cannot find log directory"
    exit 1
fi

chown squid:squid /var/log/squid

# Start ntpd
echo "Starting ntpd"
ntpd

# Start squid in foreground so containe stays up
echo "Starting squid"
squid -NYC
