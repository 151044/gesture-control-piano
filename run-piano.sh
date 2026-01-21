#!/bin/bash
source piano-venv/bin/activate
LD_LIBRARY_PATH=/home/data/gesture-control-piano/lib:$LD_LIBRARY_PATH python main.py
