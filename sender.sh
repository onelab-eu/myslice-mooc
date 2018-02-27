#!/usr/bin/env bash

######################################
# Launch this script from myslice-mooc #
######################################

sudo nohup python BrainForProbing/brain/sender.py BrainForProbing/resources/probing_configuration.json 3600 &
sudo nohup python BrainForProbing/brain/sender.py BrainForProbing/resources/slow_probing_configuration.json 7200 &

while [ 1 ]
do
    sleep 3600
    sudo pkill -f sender.py
    sudo nohup python BrainForProbing/brain/sender.py BrainForProbing/resources/probing_configuration.json 3600 &
    sudo nohup python BrainForProbing/brain/sender.py BrainForProbing/resources/slow_probing_configuration.json 7200 &
done

