FROM osrf/ros:kilted-desktop-full

# Copy scripts folder
COPY scripts/ /root/scripts/
WORKDIR /root/
RUN chmod a+x -R /root/scripts

# Env variables
ENV ROS_WS=/root/ros2_ws
ENV SCRIPTS_PATH=/root/scripts

# Run the general and ROS dep installation
RUN scripts/install_deps.sh

# Finally, build all the stuff we downloaded.
RUN scripts/build_ros.sh
