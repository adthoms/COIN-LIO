#!/bin/bash
set -o pipefail
source /opt/ros/kilted/setup.bash
mkdir -p $ROS_WS/src
cd $ROS_WS/src
git config --global url.https://github.com/.insteadOf git@github.com:
git config --global advice.detachedHead false
git clone --recurse-submodules https://github.com/patripfr/COIN-LIO.git
cd COIN-LIO && git submodule update --init --recursive
cd $ROS_WS
colcon build --packages-select coin_lio --cmake-args -DCMAKE_BUILD_TYPE=Release
echo 'source /opt/ros/kilted/setup.bash' >> ~/.bashrc
echo 'source $ROS_WS/install/setup.bash' >> ~/.bashrc
