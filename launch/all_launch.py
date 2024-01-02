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
                package="experiment_python",
                executable="communicateWiFiUDP_ESP32",
                output="screen",  # print wo hyouzi
                prefix="xterm -e",
            ),
            # Node(
            #     package="joy",
            #     executable="joy_node",
            #     parameters=[{"device_id": 0}],
            #     remappings=[("/joy", "/joy1")],
            # ),
            Node(
                package="joy",
                executable="joy_node",
                parameters=[{"device_id": 0}],
                remappings=[("/joy", "/joy1")],
            ),
            # Node(
            #     package="joy",
            #     executable="joy_node",
            #     parameters=[{"device_id": 1}],
            #     remappings=[("/joy", "/joy1")],
            # ),
            Node(
                package="experiment_python",
                executable="webserver",
                output="screen",  # print wo hyouzi
                # prefix="xterm -e",
            ),
        ]
    )
