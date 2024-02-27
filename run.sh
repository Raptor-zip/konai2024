source /opt/ros/humble/setup.bash
colcon build
sleep 0.1s
source install/setup.bash
sleep 0.1s
ros2 launch launch/all_launch.py