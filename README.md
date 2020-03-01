# pylidartracker
pylidartracker is a traffic analysis software for pre-processing point cloud videos from VelodyneHDL lidar, road user classification and tracking. The software is developed at Aalborg University Denmark, Traffic Research Group.
Contact msa@build.aau.dk

# Features:
Open large PCAP files for preview, pre-processing/editing in terms of coordinate transformation, clipping, background subtraction, clustering and tracking
Saving project config files (could be called callibration files) that can be appled to the files from similar experimental setup through API or the GUI to speed up the analysis proccess. Output edited PCAP files, or full traffic report that can include the detected road user ID, path (position and speed), class, etc. 

# Installation
Coming soon

# TODO priority list:
* finish clustering ui and logic
* finish tracking ui and logic
* finish output ui and logic
* check entire pipeline and release first beta
* thread the logic tasts to avoid UI freeze
* config file validation
* create status bar messages of last action and current program state (fx, which pre-processors are active)
* perform user-tests to optimize the user interface layout and detect bugs
* refactor for readability and testability
* write unit tests
* add continuous integration
* extend choice of pre and post-processing algorithms (bg subtraction, clustering, tracking etc.)

