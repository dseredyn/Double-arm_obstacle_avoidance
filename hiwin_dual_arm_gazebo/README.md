# wut_velma_gazebo

## Dependencies

The Package was tested on the following setup:
* Ubuntu 24.04
* ROS 2 Jazzy
* Python 3.12


## Installation

```bash
mkdir -p ws_velma/src
cd ws_velma
vcs import --input https://raw.githubusercontent.com/dseredyn/wut_velma_gazebo/refs/heads/main/workspace_def/workspace.repos src
source /opt/ros/jazzy/setup.bash
python3 -m colcon build --symlink-install --cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=RelWithDebInfo
```

## Run

Run Simulation:
```bash
source install/setup.bash
ros2 launch wut_velma_gazebo start_system.launch.py world:=empty.world
```
