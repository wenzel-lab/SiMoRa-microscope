#!/bin/bash

# install packages
mamba install anaconda::pip
sudo apt install python3-pyqtgraph python3-pyqt5 -y
sudo apt install python3-pyqt5.qtsvg

# clone the repo
cd ~/Documents/wenzel_repositories
git clone https://github.com/hongquanli/octopi-research.git
cd octopi-research/software
mkdir cache

# install libraries 
pip3 install qtpy pyserial pandas imageio crc==1.3.0 lxml numpy tifffile scipy napari
pip3 install opencv-python-headless opencv-contrib-python-headless
pip3 install napari[all] scikit-image dask_image ome_zarr aicsimageio basicpy

# install camera drivers
cd ~/Documents/wenzel_repositories/octopi-research/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux-x86_Gige-U3_32bits-64bits_1.2.1911.9122
./Galaxy_camera.run
cd ~/Documents/wenzel_repositories/octopi-research/software/drivers\ and\ libraries/daheng\ camera/Galaxy_Linux_Python_1.0.1905.9081/api
python3 setup.py build
sudo /home/wenzel-lab/miniforge3/envs/squid-station/bin/python3 setup.py install
cd ~/Documents/wenzel_repositories/octopi-research/software
sudo cp drivers\ and\ libraries/toupcam/linux/udev/99-toupcam.rules /etc/udev/rules.d

# enable access to serial ports without sudo
sudo usermod -aG dialout $USER
