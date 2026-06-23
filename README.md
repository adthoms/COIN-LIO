# Complementary Intensity-Augmented LiDAR Inertial Odometry


<p align="center">
  <img width=125 src="doc/coin_transparent.gif">
</p>

<p align="center">
<img src="https://github.com/ethz-asl/COIN-LIO/actions/workflows/build_test_20.yml/badge.svg">
<a href="https://github.com/ethz-asl/COIN-LIO/tree/main"><img src="https://img.shields.io/badge/-C++-blue?logo=cplusplus" /></a>
<a href="https://arxiv.org/pdf/2310.01235"><img src="https://img.shields.io/badge/Paper-PDF-yellow" alt="Paper" /></a>
<a href="https://arxiv.org/abs/2310.01235"><img src="https://img.shields.io/badge/arXiv-2310.01235-b31b1b.svg?style=flat-square" alt="Arxiv" /></a>
<a href="https://www.youtube.com/watch?v=H_sPLofuHpk"><img src="https://badges.aleen42.com/src/youtube.svg" alt="YouTube" /></a>
</p>

<p align="center">
  <img width='100%' src="doc/coin_tracking.gif">
</p>

<details>
<summary>Abstract</summary>
<br>
We present COIN-LIO, a LiDAR Inertial Odometry pipeline that tightly couples information from LiDAR intensity with geometry-based point cloud registration. The focus of our work is to improve the robustness of LiDAR-inertial odometry in geometrically degenerate scenarios, like tunnels or flat fields. We project LiDAR intensity returns into an intensity image, and propose an image processing pipeline that produces filtered images with improved brightness consistency within the image as well as across different scenes. To effectively leverage intensity as an additional modality, we present a novel feature selection scheme that detects uninformative directions in the point cloud registration and explicitly selects patches with complementary image information. Photometric error minimization in the image patches is then fused with inertial measurements and point-to-plane registration in an iterated Extended Kalman Filter. The proposed approach improves accuracy and robustness on a public dataset. We additionally publish a new dataset, that captures five real-world environments in challenging, geometrically degenerate scenes. By using the additional photometric information, our approach shows drastically improved robustness against geometric degeneracy in environments where all compared baseline approaches fail.
</details>

Please cite our work if you are using COIN-LIO in your research.
  ```bibtex
@inproceedings{pfreundschuh2024coin,
  title={COIN-LIO: Complementary Intensity-Augmented LiDAR Inertial Odometry},
  author={Pfreundschuh, Patrick and Oleynikova, Helen and Cadena, Cesar and Siegwart, Roland and Andersson, Olov},
  booktitle={2024 IEEE International Conference on Robotics and Automation (ICRA)},
  pages={1730--1737},
  year={2024},
  organization={IEEE}
}
  ```

# Setup
## Installation
This package was developed using ROS2 Kilted. Other ROS2 distributions should also work but have not been tested and we do not guarantee support.

1. If not done yet, please [install ROS2](https://docs.ros.org/en/kilted/Installation.html).
  Install some additional system dependencies:
    ```bash
    sudo apt-get install libgoogle-glog-dev
    ```
2. Then create a colcon workspace:
    ```bash
    mkdir -p ~/ros2_ws/src
    cd ~/ros2_ws
    ```
3. Clone COIN-LIO into your workspace:
    ```bash
    cd ~/ros2_ws/src
    git clone git@github.com:ethz-asl/coin-lio.git
    cd COIN-LIO
    ```
4. Build COIN-LIO:
    ```bash
    cd ~/ros2_ws
    colcon build --packages-select coin_lio --cmake-args -DCMAKE_BUILD_TYPE=RelWithDebInfo
    source install/setup.bash
    ```

## Alternative Installation: Docker
To instead use docker, check out the repository locally, navigate to it, and:
    ```bash
    cd docker/
    ./run_docker.sh -b
    ```
Which will build a docker image with a copy of the code checked out inside.
Your `~/data` folder will be mounted to `/root/data` within the docker, so you
can download datasets and follow the rest of the tutorial below. On future runs,
you can simply use `./run_docker.sh` (without `-b`) to not re-build the image.

Each dataset launch file presets the sensor metadata, column shift, and point/IMU
topics, then forwards a `bag_file:=` argument. When `bag_file` is set, the launch
plays that ROS2 bag automatically with `--clock`; when omitted, COIN-LIO waits for
live data instead. A ROS2 bag is a directory (containing `metadata.yaml` and a
`.db3`/`.mcap` file), so pass the directory path, not a single `.bag` file.

## Running ENWIDE Dataset Sequences
The ENWIDE dataset sequences can be downloaded [here](https://projects.asl.ethz.ch/datasets/enwide).
Run a sequence:
  ```bash
  ros2 launch coin_lio mapping_enwide.launch.py bag_file:=<path/to/ros2_bag>
  ```
## Running Newer College Dataset Sequences
The Newer College Dataset sequences can be downloaded [here](https://drive.google.com/drive/u/0/folders/1uR476FzjN3PfAiCknVKtuZi3_QfVvSdA).
Run a sequence:
  ```bash
  ros2 launch coin_lio mapping_newer_college.launch.py bag_file:=<path/to/ros2_bag>
  ```
## Running FieldAI Dataset Sequences
Run a sequence recorded on the FieldAI rig (presets live in `launch/mapping_fieldai.launch.py` / `config/os_fieldai.json`):
  ```bash
  ros2 launch coin_lio mapping_fieldai.launch.py bag_file:=<path/to/ros2_bag>
  ```
## Running COIN-LIO on your own data:
**Note on LiDAR type:** COIN-LIO currently only supports data from Ouster LiDARs, as we use the calibration in the metadata file for the image projection model. Implementing different sensors is theoretically possible but requires a proper implementation of a projection model that works for the specific sensor. Contributions are welcome.

### Sensor Calibration
* **LiDAR:**
Since different Ouster sensors have different image projection parameters, we need to run a calibration tool to evaluate the column shift which is required to correct the image projection model. This procedure is only required once per sensor.

It is important to use the metadata file that corresponds to your specific sensor (more information can be found [here](https://github.com/ouster-lidar/ouster-ros/wiki/index)).
  ```bash
  ros2 launch coin_lio calibrate.launch.py bag_file:=<path/to/ros2_bag> metadata_file:=<metadata_path.json> point_topic:=<pointcloud_topic>
  ```
  The evaluated column shift parameter will be printed at the end of the procedure.
* **IMU:**
If you are not using the built-in IMU in the Ouster LiDAR, you need to adapt the extrinsic calibration between IMU and LiDAR accordingly in the [parameter file]().
### Run COIN-LIO with your own data
Launch with settings for your data, passing the ROS2 bag to play:
  ```bash
  ros2 launch coin_lio mapping.launch.py metadata_file:=<metadata_path.json> column_shift:=<parameter from calibration> point_topic:=<pointcloud_topic> imu_topic:=<imu_topic> destagger:=<true/false> bag_file:=<path/to/ros2_bag>
  ```
  If your data already contains [destaggered point clouds from the ouster driver](https://github.com/ouster-lidar/ouster-ros/blob/55519ed2b8a7dd7d4ae13a968b0ec88e5cada7dd/launch/common.launch#L45), set `destagger:=false`, otherwise use `destagger:=true`.

  `bag_file` is optional (the same argument is accepted by every dataset launch above). When set, the bag is played automatically with `--clock`. Omit it to run against live sensor data, or to play a bag yourself in a separate terminal:
  ```bash
  ros2 bag play <path/to/ros2_bag> --clock
  ```
### Line Artifact Removal
The line artifact removal filter can be tested and tuned using the provided notebook:
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ethz-asl/COIN-LIO/blob/main/scripts/artifact_removal.ipynb)
## Acknowledgements
COIN-LIO builds on top of [FAST-LIO2](https://github.com/hku-mars/FAST_LIO) for the point-to-plane registration. 
Our dashboard was inspired by [DLIO](https://github.com/vectr-ucla/direct_lidar_inertial_odometry). We thank the authors for open-sourcing their outstanding works.
<p align="left">
  <img width='50%' src="doc/coin_dashboard.gif">
</p>

We used [ascii-image-converter](https://github.com/TheZoraiz/ascii-image-converter) for our ascii animation.
