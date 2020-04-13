# PyLidarTracker
PyLidarTracker is a desktop traffic analysis software for pre-processing point cloud videos captured by VelodyneHDL lidar (so far only HDL32). Pre-processed clouds can be clustered into road users whose tracks that can be exported for fruther analysis. The software is developed at Aalborg University Denmark, [Traffic Research Group](https://vbn.aau.dk/en/organisations/forskningsgruppen-for-trafik-civil/persons/).

![GitHub](https://img.shields.io/github/license/mihsamusev/pylidartracker)
![PyPI](https://img.shields.io/pypi/v/pylidartracker)

## Features
Open .pcap files for preview, pre-processing/editing in terms of coordinate transformation, clipping, background subtraction, clustering and cluster tracking. Save project config files (could be called callibration files) that can be appled to the files from similar experimental setup to avoid repetitive steps in the analysis proccess. Output .json file with detected road user ID, time and position per point cloud video frame.

BLAZING VISUALS HERE

## Getting started

### Installation
Install using `pip`, all dependencies will be installed autmatically. On completion run `pylidartracker` script in your terminal to start the application.
```
pip install pylidartracker
```
Alternatively, install from source preferably using git. Note that you will need the requirements to be installed already. Those can be found in `requirements.txt`. Run the application from cloned folder using python `src/app.py`.
```
git clone https://github.com/mihsamusev/pylidartracker.git
```
### Demo
The files for the demo are store in [OneDrive demo data folder](https://aaudk-my.sharepoint.com/:f:/g/personal/msa_civil_aau_dk/EvAToLzFPiFPq0mdXS5bou4BtGgRxRaFKDY1T8UgSPJAuw?e=EPlfzX). The folder contains point cloud videos street.pcap and office.pcap as well as optional project configuration files street_config.json and office_config.json.

Workflow:

1) Open a .pcap file to be analyzed, choose amount of frames to preview. Small amount of frames (100-200) is suggested because it allows to quickly define processing steps that are later going to be applied for the entire file.
2) Perform pre-processing, coordinate transformation, cloud clipping and background subtraction to prepare the poit cloud frames for clustering
3) Perform clustering of point cloud frames into individual objects
4) Perform cluster tracking
5) Optionally, save the previous steps to config file that can be re-run later to recreate the processing steps undertaken in the project.
6) Generate output


## Built with
Frontend:
- [PyQt5](https://pypi.org/project/PyQt5/) for user interface
- [pyqtgraph](http://www.pyqtgraph.org/), [pyopengl](https://pypi.org/project/PyOpenGL/) for visualization

Backend: 
- [numpy](https://numpy.org/), [scikit-learn](https://scikit-learn.org/stable/), [scikit-image](https://scikit-image.org/) for mathematical operations
- [dpkt](https://dpkt.readthedocs.io/en/latest/) for .pcap file parsing

## Future work
### UI
+ create status bar messages of last action and current program state (fx, which pre-processors are up to date)
+ pack player to a separate class
+ run the app from console with flags for fast .pcap file and config loading for advanced user / debugging
+ show tick boxes on main window to display bg, clusters, scale point sizes
### Testing
+ write unit tests for both backend and frontend
+ set up Travis, passing / failing badge, maybe test coverage as well
### I/O
+ Skipping frames should be faster than reading. Current functionality skips frames by reading them and not saving to a list.
+ Create cache that stores indexing of the the pcap file during peeking the number of frames. Indexing is used later to load frames with given offset. Having indexing one can load frames by collecting all the correct packages (right length + port) into one buffer and parse it in one call. In principle that should give a very fast loading of files who have been loaded at least once before.
+ Re-think status quo data structure that was borrowed from the predecessor project. Try to optimize it by using low level libraries based on C/C++ like struct.unpack or same np buffer loading functionality. Work with integers until the very exposure of the data to calculation/drawing. Divison cost ads up over the oamount of packet processing we are dealing with

## Support
Contact msa@build.aau.dk


