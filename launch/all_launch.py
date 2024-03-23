# from launch import LaunchDescription
# from launch_ros.actions import Node
import launch_ros.actions
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="konai2024_python",
                executable="main",
                output="screen",
                # prefix="xterm -e",
            ),
            Node(
                package="joy",
                executable="joy_node",
                parameters=[{"device_id": 0}],
                remappings=[("/joy", "/joy0")],
            ),
            # Node(
            #     package="joy",
            #     executable="joy_node",
            #     remappings=[("/joy", "/joy0")],
            # ),
            Node(
                package="joy",
                executable="joy_node",
                parameters=[{"device_id": 1}],
                remappings=[("/joy", "/joy1")],
            ),
            Node(
                package="konai2024_python",
                executable="webserver",
                output="screen",
                prefix="xterm -e",
            ),
        ]
    )
