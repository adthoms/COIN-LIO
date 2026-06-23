"""Shared helpers for COIN-LIO ROS2 launch files.

Ouster sensor metadata is distributed as raw nested JSON, which cannot be loaded
as a ROS2 parameter file directly. ``load_metadata`` flattens it into a flat dict
of dotted-key parameters, coercing each known intrinsic to the exact type the
COIN-LIO C++ reads (ints for pixel counts / shifts, floats for everything else)
since ROS2 parameters are strictly typed.

Leaves that ROS2 cannot represent as a parameter -- ``null``, empty arrays (the
element type cannot be inferred), and nested / heterogeneous arrays -- are
dropped. COIN-LIO never reads those keys, and passing them would make
``ros2 launch`` abort with a parameter-conversion error before the node starts.
"""

import json
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

_INT_SCALAR_KEYS = {"pixels_per_column", "columns_per_frame"}
_INT_LIST_KEYS = {"pixel_shift_by_row"}

# Sentinel returned by _coerce_leaf for a value that has no valid ROS2 param form.
_SKIP = object()


def _coerce_leaf(key, value):
    """Coerce a JSON leaf to a ROS2-strict-typed param value, or _SKIP to drop it."""
    leaf = key.rsplit(".", 1)[-1]
    if value is None:
        return _SKIP
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if leaf in _INT_SCALAR_KEYS:
            return int(value)
        return float(value)
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        if not value:
            return _SKIP  # ROS2 cannot infer the element type of an empty array
        if not all(isinstance(el, (bool, int, float, str)) for el in value):
            return _SKIP  # nested arrays / dicts-in-lists are not valid ROS2 params
        if all(isinstance(el, bool) for el in value):
            return value
        if all(isinstance(el, str) for el in value):
            return value
        # numeric array (bool already handled above)
        if all(isinstance(el, (int, float)) and not isinstance(el, bool) for el in value):
            if leaf in _INT_LIST_KEYS:
                return [int(el) for el in value]
            return [float(el) for el in value]
        return _SKIP  # heterogeneous (e.g. mixed str/number) -> not a valid ROS2 array
    return _SKIP


def flatten_metadata(obj, prefix=""):
    """Recursively flatten nested Ouster metadata into dotted-key ROS2 params."""
    flat = {}
    for key, value in obj.items():
        dotted = "{}.{}".format(prefix, key) if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_metadata(value, dotted))
        else:
            coerced = _coerce_leaf(dotted, value)
            if coerced is not _SKIP:
                flat[dotted] = coerced
    return flat


def load_metadata(path):
    """Read an Ouster metadata JSON file, return a flat dict of ROS2 params."""
    with open(path, "r") as handle:
        return flatten_metadata(json.load(handle))


def dataset_mapping(metadata_file, column_shift, point_topic, imu_topic):
    """Run the generic ``mapping.launch.py`` with one dataset's presets.

    Dataset launch files are just these four inputs -- metadata JSON (a name
    under ``config/``), the calibrated column shift, and the point/IMU topics.
    ``rviz`` and ``bag_file`` are forwarded so dataset launches keep the same
    command-line UX as the generic launch.
    """
    share = get_package_share_directory("coin_lio")
    return LaunchDescription([
        DeclareLaunchArgument("rviz", default_value="true"),
        DeclareLaunchArgument("bag_file", default_value=""),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(share, "launch", "mapping.launch.py")
            ),
            launch_arguments={
                "metadata_file": os.path.join(share, "config", metadata_file),
                "column_shift": str(column_shift),
                "point_topic": point_topic,
                "imu_topic": imu_topic,
                "rviz": LaunchConfiguration("rviz"),
                "bag_file": LaunchConfiguration("bag_file"),
            }.items(),
        ),
    ])
