#!/usr/bin/env bash

######################################
# Launch this script from myslice-mooc #
######################################

sudo nohup python BrainForProbing/brain/sender.py BrainForProbing/resources/probing_configuration.json 3600 &
