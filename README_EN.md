# HIWIN Dual-Arm ROS 2 (Humble) Collision-Avoidance Path Planning User Guide

This workspace (`~/hiwin_ws/src/`) contains **9 ROS 2 packages**: the robot description package
`hiwin_dual_arm_description`, the MoveIt2 configuration package `hiwin_dual_arm`,
the cross-domain bridge package for the physical robots `dual_arm_domain_bridge`, and six selectable dual-arm collision-avoidance planners.
For the mathematical derivations of each planner's algorithm and parameter comparison tables, see its respective `README.md` and `PARAMETERS.md` files.

---

## 1. What Does This Workspace Do?

The two HIWIN robotic arms (arm A: RA610-1476 and arm B: RA605-710, mounted facing each other, 1400 mm apart)
share the same workspace, so their joint trajectories may cause them to collide with each other.
Given the start and goal joint angles for each arm, this workspace automatically plans a collision-free joint-space trajectory for both arms.
The collision-avoidance algorithms are packaged as **MoveIt2 planner plugins** and used as `planning_plugin` in `move_group`.
When operating the physical robots, the cross-domain bridge forwards the planned trajectories to the respective arm drivers for execution.

---

## 2. Package Overview

```
~/hiwin_ws/src/
├── hiwin_dual_arm/                  ← MoveIt2 configuration + launch files (not an algorithm)
├── hiwin_dual_arm_description/      ← Dual-arm URDF/mesh description (RA610-1476 + RA605-710 + base)
├── dual_arm_domain_bridge/         ← Cross-domain bridge for physical robots (joint_states merging / trajectory action forwarding)
├── dual_arm_alm_newton_planner/     ┐
├── dual_arm_alm_cg_planner/         │  ALM family (Augmented Lagrangian Method)
├── dual_arm_alm_gd_planner/         ┘
├── dual_arm_lag_newton_planner/     ┐
├── dual_arm_lag_cg_planner/         │  Lagrangian family
└── dual_arm_lag_gd_planner/         ┘
```

All six planners solve the same dual-arm collision-avoidance problem. They differ only in the mathematical formulation and solution method used for the inner optimization:

| | Newton | CG (Conjugate Gradient) | GD (Steepest Descent) |
|---|---|---|---|
| **ALM model** | `dual_arm_alm_newton_planner` | `dual_arm_alm_cg_planner` | `dual_arm_alm_gd_planner` |
| **Lagrangian model** | `dual_arm_lag_newton_planner` | `dual_arm_lag_cg_planner` | `dual_arm_lag_gd_planner` |

⚠️ ALM and Lagrangian are different mathematical models; do not mix their parameters.

The six `dual_arm_*_planning.yaml` files in `hiwin_dual_arm/config/` each set
`planning_plugin` to the corresponding `DualArmXxxPlannerManager` and supply that planner's parameters.
MoveIt automatically discovers and registers these files as planning pipelines according to the `*_planning.yaml` naming convention, so no separate list needs to be maintained.

---

## 3. Environment Setup (ROS 2 Jazzy; Once per New Machine)

> Tested environment: Ubuntu 24.04, ROS 2 Jazzy, simulation only (Gazebo Sim).

```bash
# ① Create the workspace and place this repository's 9 packages in src/
mkdir -p ~/hiwin_ws/src
cd ~/hiwin_ws/src
git clone https://github.com/dseredyn/Double-arm_obstacle_avoidance.git

# ② Install dependencies (rosdep installs moveit_*, Eigen3, etc., based on each package.xml)
cd ~/hiwin_ws
sudo rosdep init            # If rosdep was initialized previously, this may report an error; it can be ignored
rosdep update
rosdep install --from-paths src --ignore-src -r -y

# ③ Build the entire workspace
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

---


## 4a. Commands for Controlling the simulated robot

Run the simulated system and MoveIt:
```bash
source ~/hiwin_ws/install/setup.bash
ros2 launch hiwin_dual_arm_gazebo start_system.launch.py
```

You can command motions using MoveIt interface in rviz2.


---

## 4b. Commands for Controlling the Physical Robots

> Note: This branch was not tested on a physical robot.

The physical robot setup uses ROS domain isolation: the host computer (planning side) and the two arm drivers use different `ROS_DOMAIN_ID` values.
`dual_arm_domain_bridge` connects these domains, merges the `joint_states` from both arms for the host,
and forwards the trajectories and execution feedback of the `FollowJointTrajectory` action between domains:

```
D0   Host:  brain.launch.py (six planners + move_group + RViz)
D10  Arm A: RA610-1476 driver (hiwin_driver)
D20  Arm B: RA605-710 driver (hiwin_driver)
Bridge layer (running on the host): joint_states merging + transparent forwarding of FollowJointTrajectory actions
```

> At the beginning of each terminal session, complete the **prerequisite** steps specified at the start of the relevant subsection (not repeated below).
> The `RMW_IMPLEMENTATION` setting must be identical on all three machines (a prerequisite for cross-machine communication).
> Check the current `ROS_DOMAIN_ID` value before exporting the value required for that terminal.

### 4.1 Host Computer (Planning + Bridge, Domain 0)

**Prerequisites** (at the start of each terminal session):

```bash
source ~/hiwin_ws/install/setup.bash
echo $RMW_IMPLEMENTATION
echo $ROS_DOMAIN_ID
export ROS_DOMAIN_ID=0
```

**Terminal A — Planning:**

```bash
ros2 launch hiwin_dual_arm brain.launch.py
```

**Terminal B — Bridge** (trajectory action forwarding + joint_states merging):

```bash
ros2 launch dual_arm_domain_bridge bridge_relay.launch.py \
     host_domain:=0 arm_a_domain:=10 arm_b_domain:=20
```

Once the bridge is established, RViz's **Plan & Execute / Stop** controls can be used directly with the physical robots (or simulated hardware).

### 4.2 Arm Computers

The arm controllers must first have the official HIWIN `hiwin_ros2` (`hiwin_driver`) installed in `~/ws_ros2` according to HIWIN's instructions (see §7).

**Prerequisites** (at the start of each terminal session):

```bash
# First: start EtherCAT
sudo /etc/init.d/ethercat start

# Second: source the workspace and check the environment
source /opt/ros/humble/setup.bash
cd ~/ws_ros2
source install/setup.bash
echo $RMW_IMPLEMENTATION
echo $ROS_DOMAIN_ID
```

**Arm A (RA610-1476, Domain 10):**

```bash
export ROS_DOMAIN_ID=10
taskset -c 2 ros2 launch hiwin_driver ra6_control.launch.py ra_type:=ra610_1476 cabinet:=ecat launch_rviz:=false
```

**Arm B (RA605-710, Domain 20):** Use the same command, but change it to `export ROS_DOMAIN_ID=20` and
`ra_type:=ra605_710`.

**Reset the safety relay** (after starting the driver, execute once for each arm in its respective domain):

```bash
# Execute once for arm A (D10) and once for arm B (D20)
ros2 service call /gpio_controller/set_io hiwin_msgs/srv/SetIO \
     "{io_group: system, interface_name: reset_safety_rly, value: 1.0}"
```

### 4.3 Recommended Startup Order

```
① Arm A driver (D10) → ② Arm B driver (D20) → (reset the safety relay for each arm)
→ ③ Bridge (D0) → ④ brain.launch.py (D0) → Plan/execute in RViz
```

---

## 5. Switching Planners

In RViz, go to the **MotionPlanning** panel on the left → **Context** tab → **Planning Library**
dropdown menu, and select one of the six `dual_arm_*` planners.

<p align="center"><img src="docs/images/rviz_context.png" alt="RViz Context planning view" width="600"></p>

---

## 6. Setting the Start and Goal Joint Angles (Required Before Planning)

The planner needs both a **start state** and a **goal state** to compute a collision-free trajectory.
These states are not configured automatically when RViz starts and must be specified manually:

1. **Start state:** In the **Planning** tab, select `<current state>` from the **Start State** dropdown menu to use the current robot configuration as the starting point. Also uncheck **Query Start State** under **Displays → Planning Request**, leaving only **Query Goal State** checked (see screenshot below).
2. **Goal state:** Drag the marker in the 3D view to the desired goal pose, or use the sliders in the **Joints** tab to set precise joint angles (12 joints: `big_joint_1~6` and `small_joint_1~6`).
3. Once the start and goal states are set, click **Plan**. If planning succeeds, a trajectory animation will play in the 3D view, and the planning time will be printed in the log in the lower-left corner.

**Built-in named states** (`group_state` entries in `dual_hiwin.srdf`; selectable directly from the Start/Goal State dropdown menus):

| Name | Associated group | Description |
|---|---|---|
| `Dual_ori` | `Dual_arm` (both arms) | All 12 joint angles set to 0 (Home configuration) |

Planning tab: set Start State to `<current state>` and uncheck **Query Start State**.

<p align="center"><img src="docs/images/rviz_planning.png" alt="RViz Planning view" width="800"></p>

Joints tab: Adjust the target joint angles individually using the sliders. This can also be combined with dragging the marker.

<p align="center"><img src="docs/images/rviz_Joints.png" alt="RViz Joints view" width="800"></p>

---

## 7. Official HIWIN ROS 2 Humble Libraries

This project is used together with the official HIWIN robot driver libraries:

| Library | Description |
|---|---|
| [hiwin_ros2](https://github.com/HIWINCorporation/hiwin_ros2) | The main official ROS 2 Humble repository, providing a `ros2_control` hardware interface and MoveIt2 integration. It supports the RA6/RS4 series and can switch between simulation and physical hardware. Both arms in this project are driven by this package (the `hiwin_driver` used in §4 comes from this repository). |
| [hiwin_robot_client_library](https://github.com/HIWINCorporation/hiwin_robot_client_library) | An interface library that encapsulates low-level communication with the robot controller and is used by `hiwin_ros2`. |
| [hiwin_ros](https://github.com/HIWINCorporation/hiwin_ros) | Legacy ROS 1 repository; not ROS 2. |

The `hiwin_dual_arm_description` package in this workspace uses the `hiwin_description` package from the official libraries listed above.
The remaining packages were developed with reference to the arm-control packages in HIWIN's `hiwin_ros2` repository.

---

## 8. License

The license for each package is specified in its `package.xml` file. For attribution of derived content in `hiwin_dual_arm_description`, see that package's `NOTICE` file.
