python -m venv piano-venv
set-executionpolicy -scope currentuser remotesigned
.\piano-venv\Scripts\Activate.ps1
pip install numpy pillow tensorflow sounddevice tf_keras opencv-python
