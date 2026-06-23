#!/bin/bash
set -o pipefail

# Install ROS build tooling and system deps from apt
apt-get update && apt-get install -y python3-colcon-common-extensions python3-rosdep python3-vcstool libgoogle-glog-dev git ros-kilted-pcl-ros

# Clear cache to keep layer size down
rm -rf /var/lib/apt/lists/*
