## Installing and Using the Raman Spectrometer Camera (IDS U3-38C0XCP-M-NO) on Ubuntu

The Raman spectrometer of SiMoRa uses an **IDS U3-38C0XCP-M-NO** NIR-sensitive USB 3.0 camera (Sony IMX662 monochrome sensor).  
This camera is not supported by default in the Squid setup. To use it on Ubuntu, you need to install the **IDS peak SDK**.

### 1. Install IDS peak SDK
Add the IDS package repository and install the runtime and tools:

```bash
# Add IDS package repository key
wget -qO - https://en.ids-imaging.com/fileadmin/downloads/ids-software-suite/ids-apt-repo.pub | sudo apt-key add -

# Add repository
sudo add-apt-repository 'deb http://packages.ids-imaging.com/ids/apt stable main'

# Update and install IDS peak
sudo apt update
sudo apt install ids-peak ids-peak-gtk ids-peak-cam
```

### 2. Verify camera detection

After installation, plug in the camera and run:

```bash
ids_peak_cameramanager
```

This should list the U3-38C0XCP-M-NO camera and allow a live preview.

You can also confirm the device node with:

```bash
ls /dev/video*
```

### 3. Use in Squid GUI

Once the IDS drivers are installed:
	•	Start the Squid GUI.
	•	Go to Settings → Hardware / Cameras.
	•	Refresh the camera list: both the Daheng MER2-1220 (main camera) and the IDS U3-38C0XCP should appear.
	•	Assign:
	•	Main Camera → Daheng
	•	Spectrometer Camera → IDS U3-38C0XCP
	•	Save and restart the GUI if necessary.

Notes
	•	The IDS peak SDK provides both a direct API and a V4L2 interface. Squid can use either, but V4L2 is often the easiest path.
	•	If the IDS camera does not appear in Squid, confirm that the IDS peak runtime is installed and that your user is in the video group:

```bash
groups
sudo usermod -aG video $USER
```

Then log out and back in.
