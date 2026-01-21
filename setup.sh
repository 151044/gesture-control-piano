#!/bin/bash

# The Python venv
echo "Setting up Python environment..."
python -m venv piano-venv
source piano-venv/bin/activate
pip install numpy pillow tensorflow sounddevice tf_keras opencv-python

# The PortAudio library
echo "Compiling PortAudio..."
mkdir lib
cd portaudio || return
./configure
sed -i "s/PREFIX = \/usr\/local/PREFIX = \/home\/data\/gesture-control-piano\/lib/g" Makefile
make && make install

# Font setup
cd ..
echo "Setting up fonts..."
mkdir ~/.local/share/fonts/
cp fonts/NotoColorEmoji-Regular.ttf ~/.local/share/fonts/
fc-cache -f -v
