"""Launch the COIN-LIO column-shift calibration tool (ROS2)."""

import os
import sys

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Import the shared metadata flattener installed alongside this launch file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coin_lio_launch_utils import load_metadata  # noqa: E402


def launch_setup(context, *args, **kwargs):
    bag_file = LaunchConfiguration("bag_file").perform(context)
    metadata_file = LaunchConfiguration("metadata_file").perform(context)
    point_topic = LaunchConfiguration("point_topic").perform(context)

    metadata_params = load_metadata(metadata_file)

    calib_node = Node(
        package="coin_lio",
        executable="coin_lio_calibration",
        name="calib",
        output="screen",
        parameters=[
            metadata_params,
            {
                "bag_path": bag_file,
                "topic": point_topic,
                "n_skip": 10,
                "n_total": 500,
            },
        ],
    )

    return [calib_node]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("bag_file"),
            DeclareLaunchArgument("metadata_file"),
            DeclareLaunchArgument("point_topic"),
            OpaqueFunction(function=launch_setup),
        ]
    )
