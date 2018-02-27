#!/usr/bin/env bash

######################################
# Launch this script from myslice-mooc #
######################################

sudo nohup ./myops2/bin/myops2-mooc data/node_list &

while [ 1 ]
do
    sleep 3600
    sudo pkill -f myops2-mooc
    sudo nohup python myops2/bin/myops2-mooc data/node_list &
done

