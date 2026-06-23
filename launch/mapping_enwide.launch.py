"""Launch COIN-LIO mapping on the ENWIDE dataset (ROS2)."""

import json

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

_INT_SCALAR_KEYS = {"pixels_per_column", "columns_per_frame"}
_INT_LIST_KEYS = {"pixel_shift_by_row"}


def _coerce_leaf(key, value):
    """Coerce a leaf value to a ROS2-strict-typed value based on its key name."""
    leaf = key.rsplit(".", 1)[-1]
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if leaf in _INT_SCALAR_KEYS:
            return int(value)
        return float(value)
    if isinstance(value, list):
        if not value:
            return value
        if any(isinstance(el, dict) for el in value):
            return value
        if leaf in _INT_LIST_KEYS:
            return [int(el) for el in value]
        if all(isinstance(el, bool) for el in value):
            return value
        if all(isinstance(el, (int, float)) and not isinstance(el, bool) for el in value):
            return [float(el) for el in value]
        return value
    return value


def flatten_metadata(obj, prefix=""):
    """Recursively flatten nested Ouster metadata into dotted-key params."""
    flat = {}
    for key, value in obj.items():
        dotted = "{}.{}".format(prefix, key) if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_metadata(value, dotted))
        else:
            flat[dotted] = _coerce_leaf(dotted, value)
    return flat


def load_metadata(path):
    with open(path, "r") as handle:
        return flatten_metadata(json.load(handle))


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory("coin_lio")
    params_file = pkg_share + "/config/params.yaml"
    line_removal_file = pkg_share + "/config/line_removal.yaml"
    metadata_file = pkg_share + "/config/os_enwide.json"
    rviz_config = pkg_share + "/rviz_cfg/coinlio_viz.rviz"

    metadata_params = load_metadata(metadata_file)

    overrides = {
        "common.lid_topic": "/ouster/points",
        "common.imu_topic": "/ouster/imu",
        "image.u_shift": 0,
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
            OpaqueFunction(function=launch_setup),
        ]
    )
