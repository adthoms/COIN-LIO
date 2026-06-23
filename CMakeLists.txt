cmake_minimum_required(VERSION 3.16)
project(coin_lio)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE "Release")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -pthread -fexceptions -fdiagnostics-color=always")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -fexceptions")
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_definitions(-DROOT_DIR=\"${CMAKE_CURRENT_SOURCE_DIR}/\")
add_definitions(-DBOOST_BIND_GLOBAL_PLACEHOLDERS)

message("Current CPU archtecture: ${CMAKE_SYSTEM_PROCESSOR}")
if(CMAKE_SYSTEM_PROCESSOR MATCHES "(x86)|(X86)|(amd64)|(AMD64)" )
  include(ProcessorCount)
  ProcessorCount(N)
  message("Processer number:  ${N}")
  if(N GREATER 4)
    add_definitions(-DMP_EN)
    add_definitions(-DMP_PROC_NUM=3)
    message("core for MP: 3")
  elseif(N GREATER 3)
    add_definitions(-DMP_EN)
    add_definitions(-DMP_PROC_NUM=2)
    message("core for MP: 2")
  else()
    add_definitions(-DMP_PROC_NUM=1)
  endif()
else()
  add_definitions(-DMP_PROC_NUM=1)
endif()

# Build dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_eigen REQUIRED)
find_package(pcl_conversions REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(ament_index_cpp REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

find_package(Eigen3 REQUIRED)
find_package(PCL 1.8 REQUIRED)
find_package(OpenCV REQUIRED)
find_package(OpenMP QUIET)
find_package(glog REQUIRED)  # used by src/timing.cpp; previously pulled in transitively via catkin

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS}   ${OpenMP_C_FLAGS}")

message(Eigen: ${EIGEN3_INCLUDE_DIR})

# Generate the Pose6D interface. Target named ${PROJECT_NAME}_interfaces to
# avoid a clash with the coin_lio library target below.
rosidl_generate_interfaces(${PROJECT_NAME}_interfaces
  "msg/Pose6D.msg"
  DEPENDENCIES geometry_msgs
)
rosidl_get_typesupport_target(cpp_typesupport_target
  ${PROJECT_NAME}_interfaces rosidl_typesupport_cpp)

include_directories(
  include
  ${EIGEN3_INCLUDE_DIR}
  ${PCL_INCLUDE_DIRS}
  ${OpenCV_INCLUDE_DIRS}
)

# Shared library
add_library(coin_lio
  include/ikd-Tree/ikd_Tree.cpp
  src/preprocess.cpp
  src/image_processing.cpp
  src/imu_processing.cpp
  src/feature_manager.cpp
  src/timing.cpp
  src/use_ikfom.cpp
  src/projector.cpp
)
# Deps are PUBLIC so executables linking coin_lio inherit them transitively.
# Message packages use the ${pkg_TARGETS} form; everything else uses modern
# namespaced targets (replaces deprecated ament_target_dependencies).
target_link_libraries(coin_lio PUBLIC
  ${PCL_LIBRARIES} ${OpenCV_LIBRARIES} ${OpenMP_CXX_FLAGS}
  glog::glog
  "${cpp_typesupport_target}"
  rclcpp::rclcpp
  tf2::tf2 tf2_ros::tf2_ros tf2_eigen::tf2_eigen
  pcl_conversions::pcl_conversions cv_bridge::cv_bridge
  ament_index_cpp::ament_index_cpp
  ${sensor_msgs_TARGETS} ${nav_msgs_TARGETS} ${geometry_msgs_TARGETS}
  ${visualization_msgs_TARGETS} ${std_msgs_TARGETS} ${builtin_interfaces_TARGETS})

# Mapping executable — inherits all deps transitively from coin_lio.
add_executable(coin_lio_mapping src/laserMapping.cpp)
target_link_libraries(coin_lio_mapping PUBLIC coin_lio)

# Calibration executable — inherits from coin_lio, plus rosbag2 for bag reading.
add_executable(coin_lio_calibration src/calibration.cpp)
target_link_libraries(coin_lio_calibration PUBLIC coin_lio rosbag2_cpp::rosbag2_cpp)

# Install
install(TARGETS coin_lio coin_lio_mapping coin_lio_calibration
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY config launch rviz_cfg
  DESTINATION share/${PROJECT_NAME})

ament_export_dependencies(rosidl_default_runtime)
ament_package()
