"""Launch COIN-LIO mapping on arbitrary Ouster data (ROS2)."""

import os
import sys

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

# Import the shared metadata flattener installed alongside this launch file.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from coin_lio_launch_utils import load_metadata  # noqa: E402


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory("coin_lio")
    params_file = pkg_share + "/config/params.yaml"
    line_removal_file = pkg_share + "/config/line_removal.yaml"
    rviz_config = pkg_share + "/rviz_cfg/coinlio_viz.rviz"

    metadata_file = LaunchConfiguration("metadata_file").perform(context)
    column_shift = LaunchConfiguration("column_shift").perform(context)
    point_topic = LaunchConfiguration("point_topic").perform(context)
    imu_topic = LaunchConfiguration("imu_topic").perform(context)
    destagger = LaunchConfiguration("destagger").perform(context)

    metadata_params = load_metadata(metadata_file)

    overrides = {
        "common.lid_topic": point_topic,
        "common.imu_topic": imu_topic,
        "image.u_shift": int(float(column_shift)),
        "image.destagger": destagger.lower() == "true",
    }

    mapping_node = Node(
        package="coin_lio",
        executable="coin_lio_mapping",
        name="laserMapping",
        output="screen",
        parameters=[params_file, line_removal_file, metadata_params, overrides],
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        arguments=["-d", rviz_config],
        condition=IfCondition(LaunchConfiguration("rviz")),
    )

    bag_play = ExecuteProcess(
        cmd=[
            "ros2",
            "bag",
            "play",
            LaunchConfiguration("bag_file"),
            "--clock",
        ],
        output="screen",
        condition=IfCondition(
            PythonExpression(["'", LaunchConfiguration("bag_file"), "' != ''"])
        ),
    )

    return [mapping_node, rviz_node, bag_play]


def generate_launch_description():
    return LaunchDescription(
        [
            DeclareLaunchArgument("rviz", default_value="true"),
            DeclareLaunchArgument("bag_file", default_value=""),
            DeclareLaunchArgument("destagger", default_value="true"),
            DeclareLaunchArgument("metadata_file"),
            DeclareLaunchArgument("column_shift"),
            DeclareLaunchArgument("point_topic"),
            DeclareLaunchArgument("imu_topic"),
            OpaqueFunction(function=launch_setup),
        ]
    )
