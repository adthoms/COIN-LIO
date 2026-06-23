"""Launch COIN-LIO mapping on the Newer College dataset (ROS2)."""

import os
import sys

# Import the shared launch helpers installed alongside this launch file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coin_lio_launch_utils import dataset_mapping  # noqa: E402


def generate_launch_description():
    return dataset_mapping(
        metadata_file="os_newer_college.json",
        column_shift=31,
        point_topic="/os_cloud_node/points",
        imu_topic="/os_cloud_node/imu",
    )
