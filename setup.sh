#!/bin/bash
python -m venv piano-venv
source piano-venv/bin/activate
pip install numpy pillow tensorflow[and-cuda] sounddevice tf_keras opencv-python
