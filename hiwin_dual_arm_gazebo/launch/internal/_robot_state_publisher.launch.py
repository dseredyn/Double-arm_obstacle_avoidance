#!/usr/bin/env python3

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, TextSubstitution
from launch.substitutions import PythonExpression, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():
    pkg_moveit_config = get_package_share_directory('hiwin_dual_arm')

    xacro_file = LaunchConfiguration('xacro_file')
    default_xacro = PathJoinSubstitution([pkg_moveit_config, 'config', 'dual_hiwin.urdf.xacro'])

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    frame_prefix = LaunchConfiguration('frame_prefix', default='')

    # Convert xacro -> urdf (string) at launch time
    robot_desc = Command([
        FindExecutable(name='xacro'),
        TextSubstitution(text=' '),
        xacro_file,
        TextSubstitution(text=' '),
        # TextSubstitution(text='collision_detector:="dart"')
    ])

    return LaunchDescription([
        DeclareLaunchArgument('xacro_file', default_value=default_xacro,
                              description='Absolute path to URDF Xacro file.'),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'robot_description': ParameterValue(value=robot_desc, value_type=str),
                'frame_prefix': PythonExpression(["'", frame_prefix, "/'"]),
                'publish_frequency': 100.0
            }],
        ),
    ])
