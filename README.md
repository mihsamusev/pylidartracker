# pylidartracker
pylidartracker is a traffic analysis software for pre-processing point cloud videos from VelodyneHDL lidar, road user classification and tracking. The software is developed at Aalborg University Denmark, Traffic Research Group.
Contact msa@build.aau.dk

## Features:
Open large PCAP files for preview, pre-processing/editing in terms of coordinate transformation, clipping, background subtraction, clustering and tracking
Saving project config files (could be called callibration files) that can be appled to the files from similar experimental setup through API or the GUI to speed up the analysis proccess. Output edited PCAP files, or full traffic report that can include the detected road user ID, path (position and speed), class, etc. 

## Installation
Coming soon

## TODO minimal priority list
Things that separate us from releasin the first beta
* finish output writter
* check entire pipeline for bugs
* config file validation

## TODO by category
Important but can be done before first fully functional BETA
* ### UI
+ create status bar messages of last action and current program state (fx, which pre-processors are active)
* ### Testing
+ write unit tests, integrate tests into commits, show pass / fail flag
+ perform user-tests to optimize the user interface layout and detect bugs
+ refactor for readability and testability
* ### I/O
+ Way to indexing the pcap file during peeking the number of frames. Indexing is used later to load frames with given offset. Having indexing one can load frames by collecting all the correct packages (right length + port) into one buffer and parse it in one call
+ Create .pcap to HDF5 converter
+ Re-think status quo data structure that was borrowed from another project. Try to optimize it by using low level libraries calling C/C++ like struct.unpack or same np buffer loading functionality. Work with integers until the very exposure of the data to calculation/drawing. Divison cost ads up over the oamount of packet processing we are dealing with

## Known bugs / errors
* On close there is no dial window asking if you want to save current config
* On loading new file there is no change in config
* On load config the UI updates first and Preprocessor updates on a thread, so while preprocessor is updated the ui update turns on the background display and crop box display that are drawn on the non-updated points
* QHULL breaks when cluster sizes are very low!
* During calculation the thread updates values that are used for visualization. Can crash. Either separate visualization and temporary processed object arrays or block screen to disallow unwanted actions. Maybe modal dialog is a good thing here?
* Similar thing, but when calcualting entire pipeline user is still allowed to operate in docks and thus create/destroy processors that will affect pipeline. So either block unwanted docks/controls or do processing progress through modal dialog.

