#!/bin/bash
# This script is intended to be run via crontab every morning.

# Load conda bash functions
# Adjust the path to conda.sh if it differs on your system
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the junes environment
conda activate junes

# Navigate to the routine folder
cd ~/lancezhang04/junes/routine

# Run the morning routine script
python morning.py
