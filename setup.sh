#!/bin/bash

# The Python venv
python -m venv piano-venv
source piano-venv/bin/activate
pip install numpy pillow tensorflow sounddevice tf_keras opencv-python

# The PortAudio library
cd portaudio || return
./configure
make && make install
