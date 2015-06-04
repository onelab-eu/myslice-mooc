#!/bin/sh

ipv4=`ip -4 addr show dev eth0 | sed -e's/^.*inet \([^ ]*\)\/.*$/\1/;t;d'`
ipv6=`ip -6 addr show dev eth0 | sed -e's/^.*inet6 \([^ ]*\)\/.*$/\1/;t;d' | grep -v ^fe80`

printf "%s,%s\n" $ipv4 $ipv6
