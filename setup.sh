source /opt/ros/humble/setup.bash
sudo apt install python3-pip
pip install -r pip_install.txt
colcon build
sleep 0.1s
source install/setup.bash
sleep 0.1s
# sudo chmod 777 /dev/ttyUSB0
# sudo chmod 777 /dev/ttyUSB1
# sudo chmod 777 /dev/ttyUSB2
# sudo chmod 777 /dev/ttyUSB3
ros2 launch launch/all_launch.py