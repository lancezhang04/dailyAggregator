#!/bin/bash

cd /home/lancezhang04/junes
git pull origin main

# Restart Junes after code update
tmux kill-session -t junes
source /home/lancezhang04/junes/routines/server_restart_junes.sh