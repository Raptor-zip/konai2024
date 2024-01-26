source /opt/ros/humble/setup.bash
sudo apt install python3-pip
pip install -r pip_install.txt
colcon build
source install/setup.bash
sleep 0.1s
ros2 launch launch/all_launch.py