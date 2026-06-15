from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package="beer_robot_ros2",
            executable="camera_node",
            name="camera_node",
            output="screen",
        ),
        Node(
            package="beer_robot_ros2",
            executable="detector_node",
            name="detector_node",
            output="screen",
        ),
        Node(
            package="beer_robot_ros2",
            executable="tracker_node",
            name="tracker_node",
            output="screen",
        ),
        Node(
            package="beer_robot_ros2",
            executable="target_manager_node",
            name="target_manager_node",
            output="screen",
        ),
        Node(
            package="beer_robot_ros2",
            executable="debug_saver_node",
            name="debug_saver_node",
            output="screen",
        ),
        Node(
            package="beer_robot_ros2",
            executable="esp32_bridge",
            name="esp32_bridge_node",
            output="screen",
        ),
    ])
