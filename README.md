# PyLidarTracker
PyLidarTracker is a desktop traffic analysis software for pre-processing point cloud videos captured by a static VelodyneHDL LiDAR (so far only HDL32). Pre-processed clouds can be clustered into road users whose tracks that can be exported for fruther analysis. The software is developed at Aalborg University Denmark, [Traffic Research Group](https://vbn.aau.dk/en/organisations/forskningsgruppen-for-trafik-civil/persons/).

![GitHub](https://img.shields.io/github/license/mihsamusev/pylidartracker)
![PyPI](https://img.shields.io/pypi/v/pylidartracker)

## Features
- Open UDP Network stream `.pcap` files captured by Velodyne for preview.
- pre-processing/editing in terms of coordinate transformation, clipping, background subtraction, clustering and cluster tracking.
- Save project configuration files that can be appled to the files from similar experimental setup to improve reproducibility and avoid repetitive steps in the analysis proccess.
- Output `.json` file with detected road user ID, time and position per point cloud video frame.

![Preview](docs/preview.gif)

## Getting started

### Installation from source
Latest version of `pylidartracker` can be installed from source by cloning this repo and using given `setup.py`. A virtual environment like `virtualenv` or `conda` is recommended to avoid dependency problems. Example with `conda`:

```sh
# create environment
conda create -n pylidar python=3.8

# clone source code and change directory to it
git clone https://github.com/mihsamusev/pylidartracker.git
cd pylidartracker

# looks for setup.py to install into the environment
pip install -e .
```
Run the application using `pylidartracker` command, which is a shourtcut for `python src/app.py`.

### Example files
The files for the demo are store in [this zip](https://drive.google.com/file/d/17tBvllt0uAalZpKTJpHd2Fzw3vPQ8YjT/view?usp=sharing). The folder contains short point cloud videos `street.pcap` and `office.pcap` as well as optional project configuration files `street_config.json` and `office_config.json`.

Typical workflow:

0) Download the `.zip` folder with the example files.
1) Open a `.pcap` file to be analyzed, choose amount of frames to preview. Small amount of frames (100-300) is suggested because it allows to quickly define and save configuration describin processing steps that are later going to be applied for the entire file.
2) Perform pre-processing, coordinate transformation, cloud clipping and background subtraction to prepare the point cloud frames for clustering.
3) Perform clustering of point cloud frames into individual objects.
4) Perform cluster tracking.
5) Optionally, save the previous steps to configuration file that can be re-run later to recreate the processing steps undertaken in the project.
6) Generate output.

## Built with
Frontend:
- [PyQt5](https://pypi.org/project/PyQt5/) for the user interface and threading.
- [pyqtgraph](http://www.pyqtgraph.org/), [pyopengl](https://pypi.org/project/PyOpenGL/) for 3D visualization.

Backend: 
- [numpy](https://numpy.org/), [scikit-learn](https://scikit-learn.org/stable/), [scikit-image](https://scikit-image.org/) for mathematical operations.
- [dpkt](https://dpkt.readthedocs.io/en/latest/) for `.pcap` file parsing.

## Status
The project is in the process of being refactored as a backend and frontend packages with their own tests. The backend - [pylidarlib](https://github.com/mihsamusev/pylidarlib) will allow to perform same point cloud operations in a headless fashion.

## Support
Contact msa@build.aau.dk


