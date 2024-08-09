## Setting up the environments
```
wget https://raw.githubusercontent.com/wenzel-lab/SQUID-bioimaging-platform/master/software/setup_wenzel_station.sh
chmod +x setup_wenzel_station.sh
```
> [!IMPORTANT]
> You will need to edit your _.sh_ file. Ubuntu python paths were giving us problems. So we decided to contain everything in a mamba environment and add the path of the python3 executable when needed. If you have a cleaner way to do this let us know!

Firstly, make sure you have a mamba installation in your device.
```
mamba info
mamba create --name squid-station
mamba activate <your environment>
```
Secondly, edit your python3 path. In our case it was from the _"sudo <your_path>/python3 setup.py install"_ line from the .sh file.

> [!WARNING]
> Make sure that all paths called in this file exists in your local installation.

If everything is good, you should be able to execute your .sh file.
```
./setup_wenzel_station.sh
```
Reboot the computer to finish the installation.

## Configuring the software
Copy the .ini file associated with the microscope configuration to the software folder.
```
cp ~/path_of_repo_installation/SQUID-bioimaging-platform/software/configuration_squid_6060.ini ~/path_of_repo_installation/SQUID-bioimaging-platform/software/
```
> [!TIP]
> Make modifications as needed (e.g. `camera_type`, `support_laser_autofocus`,`focus_camera_exposure_time_ms`). 

In our case we will be using _"configuration_squid_6060.ini"_

## Using the software
```
python3 main.py
```
*Script may be subject to changes in the future
