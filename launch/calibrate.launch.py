"""Launch the COIN-LIO column-shift calibration tool (ROS2)."""

import json

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
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
