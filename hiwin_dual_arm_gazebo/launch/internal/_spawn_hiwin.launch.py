#!/usr/bin/env python3

import subprocess
import xacro

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_sdf_and_spawn(context, *args, **kwargs):
    xacro_file = LaunchConfiguration("xacro_file").perform(context)
    sdf_out    = '/tmp/dual_hiwin.sdf'
    urdf_out = '/tmp/dual_hiwin.urdf'
    robot_name = 'dual_hiwin'

    use_sim_time = LaunchConfiguration("use_sim_time").perform(context)

    # 1. urdf.xacro -> URDF
    doc = xacro.process_file(
        xacro_file,
        mappings={
            "use_sim_time": use_sim_time,
        },
    )

    urdf_xml = doc.toprettyxml(indent="  ")

    with open(urdf_out, "w") as f:
        f.write(urdf_xml)

    # 2. URDF -> SDF
    result = subprocess.run(
        [
            "gz",
            "sdf",
            "-p",
            str(urdf_out),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    # Save the generated SDF
    with open(sdf_out, "w") as f:
        f.write(result.stdout)

    # result = subprocess.run(
    #     [
    #         'sed',
    #         '--follow-symlinks',
    #         '-i',
    #         f's/<model name=\'velma\'>/<model name=\'velma\'>\\n    <self_collide>true<\\/self_collide>/g',
    #         f'{sdf_out}',
    #     ],
    #     check=True,
    #     # capture_output=True,
    #     text=True,
    # )

    # f'sed --follow-symlinks -i "s/<model name=\'velma\'>/<model name=\'velma\'>\\n    <self_collide>true<\\/self_collide>/g" {sdf_out}'
    
    print(f"[launch] Generated URDF: {urdf_out}")
    print(f"[launch] Generated SDF:  {sdf_out}")

    # This launch action used the already-generated SDF
    return [
        Node(
            package="ros_gz_sim",
            executable="create",
            arguments=[
                "-world", "default",
                "-file", str(sdf_out),
                "-name", robot_name,
                "-allow_renaming", "false",
            ],
            output="screen",
        )
    ]

def generate_launch_description():
    pkg_moveit_config = get_package_share_directory('hiwin_dual_arm')
    default_xacro = PathJoinSubstitution([pkg_moveit_config, 'config', 'dual_hiwin.urdf.xacro'])
    convert_to_sdf_and_spawn = OpaqueFunction(function=generate_sdf_and_spawn)

    return LaunchDescription([
        DeclareLaunchArgument(
            "xacro_file", default_value=default_xacro,
            description="Absolute path to URDF Xacro file.",
        ),
        convert_to_sdf_and_spawn,
    ])
