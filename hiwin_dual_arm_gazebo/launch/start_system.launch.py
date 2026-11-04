#!/usr/bin/env python3
#
# Copyright 2019 ROBOTIS CO., LTD.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Joep Tool, Hyungyu Kim
# Changed by: Dawid Seredyński, WUT

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess,\
    RegisterEventHandler, IncludeLaunchDescription, LogInfo
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.event_handlers import OnProcessExit

from launch_ros.substitutions import FindPackageShare
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource

def generate_launch_description():
    cleanup = ExecuteProcess(
        name="kill_gazebo_leftovers",
        output="screen",
        shell=True,
        cmd=[[
            "bash -lc '"
            "set +e; "
            "PATTERN=\"[g]z sim|[g]z-sim-server|[g]z-sim-gui|ruby.*[g]z.*sim|[g]zserver|[g]zclient\"; "
            "echo \"Cleaning Gazebo leftovers...\"; "
            "pgrep -af \"$PATTERN\" || true; "
            "pkill -TERM -f \"$PATTERN\" || true; "
            "sleep 2; "
            "if pgrep -f \"$PATTERN\" > /dev/null; then "
            "  pkill -KILL -f \"$PATTERN\" || true; "
            "fi; "
            "echo \"Cleanup finished.\""
            "'"
        ]],
    )

    world = LaunchConfiguration("world")
    default_world = 'empty.world'

    old_ogre = LaunchConfiguration("old_ogre")
    default_old_ogre = 'false'

    run_gui = LaunchConfiguration("run_gui")
    default_run_gui = 'true'

    verbose = LaunchConfiguration("verbose")
    default_verbose = '4'

    use_moveit = LaunchConfiguration("use_moveit")

    start_gazebo = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('hiwin_dual_arm_gazebo'),
                'launch',
                'internal',
                '_start_gazebo.launch.xml'
            ])
        ),
        launch_arguments={
            'world_name':world,
            'old_ogre':old_ogre,
            'run_gui':run_gui,
            'verbose':verbose
        }.items()
    )

    start_hiwin = IncludeLaunchDescription(
        XMLLaunchDescriptionSource(
            PathJoinSubstitution([
                FindPackageShare('hiwin_dual_arm_gazebo'),
                'launch',
                'internal',
                '_start_hiwin.launch.xml'
            ])
        ),
        launch_arguments={
            'use_moveit':use_moveit,
        }.items()
    )

    pkg_moveit_config = get_package_share_directory('hiwin_dual_arm')
    default_xacro = PathJoinSubstitution([pkg_moveit_config, 'config', 'dual_hiwin.urdf.xacro'])

    wait_for_clock = ExecuteProcess(
        cmd=[
            "bash",
            "-c",
            "ros2 topic echo --once /clock > /dev/null"
        ],
        output="screen",
    )

    start_after_clock = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_for_clock,
            on_exit=[
                LogInfo(msg="Gazebo /clock detected; starting Hiwin launch file."),
                start_hiwin,
            ],
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time", default_value='true',
            description="Use sim time",
        ),
        DeclareLaunchArgument(
            "xacro_file", default_value=default_xacro,
            description="Absolute path to URDF Xacro file.",
        ),
        DeclareLaunchArgument(
            "world", default_value=default_world,
            description="File name for the Gazebo Sim world.",
        ),
        DeclareLaunchArgument(
            "old_ogre", default_value=default_old_ogre,
            description="Use the old Ogre render engine in Gazebo Client (for compatibility with Virtual Box).",
        ),
        DeclareLaunchArgument(
            "run_gui", default_value=default_run_gui,
            description="Run Gazebo Client at startup.",
        ),
        DeclareLaunchArgument(
            "verbose", default_value=default_verbose,
            description="Gazebo verbosity level (0-4).",
        ),
        DeclareLaunchArgument(
            "use_moveit", default_value='true',
            description="Use sim time",
        ),
        cleanup,

        RegisterEventHandler(
            OnProcessExit(
                target_action=cleanup,
                on_exit=[
                    LogInfo(msg='Starting Gazebo...'),
                    start_gazebo,
                    wait_for_clock,
                    start_after_clock
                ]
            )
        ),
    ])
