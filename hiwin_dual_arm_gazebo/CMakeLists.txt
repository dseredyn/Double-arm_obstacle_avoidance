################################################################################
# Set minimum required version of cmake, project name and compile options
################################################################################
cmake_minimum_required(VERSION 3.8)
project(hiwin_dual_arm_gazebo)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

if(MSVC)
  add_compile_definitions(_USE_MATH_DEFINES)
endif()

################################################################################
# Find ament packages and libraries for ament and system dependencies
################################################################################
find_package(ament_cmake REQUIRED)
find_package(ros_gz_sim REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(gz_math_vendor REQUIRED)
find_package(gz-math REQUIRED)
find_package(gz_sim_vendor REQUIRED)
find_package(gz-sim REQUIRED)
find_package(gz_plugin_vendor REQUIRED)
find_package(gz-plugin REQUIRED)

################################################################################
# Build
################################################################################
#link_directories(
#  ${GAZEBO_LIBRARY_DIRS}
#  ${GZ_SIM_LIBRARY_DIRS}
#)

#include_directories(
#  include
#  ${GAZEBO_INCLUDE_DIRS}
#  ${gz_sim_vendor_INCLUDE_DIRS}
#  ${GZ_SIM_INCLUDE_DIRS}
#)


################################################################################
# Install
################################################################################

install(DIRECTORY launch params worlds
  DESTINATION share/${PROJECT_NAME}/
)

################################################################################
# Macro for ament package
################################################################################
ament_export_dependencies(
  gazebo_ros_pkgs
  geometry_msgs
  nav_msgs
  rclcpp
  sensor_msgs
  tf2
)
ament_package()
