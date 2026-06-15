from setuptools import setup, find_packages
from glob import glob
import os

package_name = "beer_robot_ros2"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="sam",
    maintainer_email="sam@example.com",
    description="ROS2 split of robot_logic_ncnn_optimized.py without changing core logic",
    license="MIT",
    entry_points={
        "console_scripts": [
            "camera_node = beer_robot_ros2.camera_node:main",
            "detector_node = beer_robot_ros2.detector_node:main",
            "tracker_node = beer_robot_ros2.tracker_node:main",
            "target_manager_node = beer_robot_ros2.target_manager_node:main",
            "debug_saver_node = beer_robot_ros2.debug_saver_node:main",
            'esp32_bridge = beer_robot_ros2.esp32_bridge_node:main',
        ],
    },
)
