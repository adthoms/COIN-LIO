"""Launch COIN-LIO mapping on the Field AI dataset (ROS2)."""

import os
import sys

# Import the shared launch helpers installed alongside this launch file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coin_lio_launch_utils import dataset_mapping  # noqa: E402


def generate_launch_description():
    # TODO: fill in the Field AI sensor presets. `metadata_file` is a JSON name
    # under config/ (add os_fieldai.json there); `column_shift` comes from
    # calibrate.launch.py; topics are this rig's Ouster point/IMU topics.
    return dataset_mapping(
        metadata_file="os_fieldai.json",
        column_shift=0,
        point_topic="/falcon52/raw_velodyne_points",
        imu_topic="/falcon52/ouster/imu",
    )
