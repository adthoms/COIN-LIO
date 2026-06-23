// Copyright (c) 2024, Patrick Pfreundschuh
// https://opensource.org/license/bsd-3-clause

#include <rclcpp/rclcpp.hpp>
#include <rclcpp/serialization.hpp>
#include <rosbag2_cpp/reader.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <thread>
#include <future>
#include <unordered_set>
#include "preprocess.h"
#include "projector.h"

int main(int argc, char** argv)
{
    pcl::console::setVerbosityLevel(pcl::console::L_ERROR);
    rclcpp::init(argc, argv);
    rclcpp::NodeOptions opts;
    opts.allow_undeclared_parameters(true);
    opts.automatically_declare_parameters_from_overrides(true);
    auto node = std::make_shared<rclcpp::Node>("calibration_node", opts);

    std::string bag_path;
    node->get_parameter_or("bag_path", bag_path, std::string(""));
    std::string topic;
    node->get_parameter_or("topic", topic, std::string(""));
    int64_t n_skip;
    node->get_parameter_or("n_skip", n_skip, static_cast<int64_t>(10));
    int64_t n_total;
    node->get_parameter_or("n_total", n_total, static_cast<int64_t>(500));

    std::vector<double> lidar_to_sensor;
    bool transform_found = node->get_parameter("lidar_to_sensor_transform", lidar_to_sensor) ||
    node->get_parameter("lidar_intrinsics.lidar_to_sensor_transform", lidar_to_sensor);

    node->set_parameter(rclcpp::Parameter("image.u_shift", 0));

    shared_ptr<Preprocess> p_pre(new Preprocess());
    if (!transform_found || lidar_to_sensor.size() != 16) {
        RCLCPP_WARN(rclcpp::get_logger("coin_lio"), "No lidar to sensor transform found, setting to default value.");
        p_pre->lidar_sensor_z_offset = 0.03618;
    } else {
        p_pre->lidar_sensor_z_offset = lidar_to_sensor[11] * 0.001;
    }

    shared_ptr<Projector> projector;
    int64_t lidar_type;
    node->get_parameter_or("preprocess.lidar_type", lidar_type, static_cast<int64_t>(OUSTER));
    p_pre->lidar_type = static_cast<int>(lidar_type);
    node->get_parameter_or("preprocess.blind", p_pre->blind, 0.5);
    projector = std::make_shared<Projector>(node);


    std::cout << "Loading Bag from Path: " << bag_path << std::endl;
    rosbag2_cpp::Reader reader;
    reader.open(bag_path);

    std::cout << "Loading Clouds from Topic: " << topic << std::endl;

    std::cout << "Processing Clouds, this can take a while." << std::endl;

    rclcpp::Serialization<sensor_msgs::msg::PointCloud2> serialization;

    double u_shift = 0.;
    int point_count = 0;
    int cloud_count = 0;
    int cloud_count_total = 0;
    while (reader.has_next())
    {
        auto bag_msg = reader.read_next();
        if (bag_msg->topic_name != topic)
        {
            continue;
        }
        rclcpp::SerializedMessage serialized_msg(*bag_msg->serialized_data);
        auto msg = std::make_shared<sensor_msgs::msg::PointCloud2>();
        serialization.deserialize_message(&serialized_msg, msg.get());
        cloud_count_total++;
        if (cloud_count_total % n_skip != 0) continue;
        PointCloudXYZI::Ptr  ptr(new PointCloudXYZI());
        p_pre->process(msg, ptr);
        if (ptr->empty()) continue;
        cloud_count++;
        if (cloud_count > n_total) break;
        LidarFrame current_frame;
        current_frame.points_corrected = ptr;
        current_frame.T_Li_Lk_vec = std::vector<M4D>(ptr->size(), M4D::Identity());
        current_frame.vec_idx = std::vector<int>(ptr->size(), 0);
        projector->createImages(current_frame);
        for (int u = 0; u < projector->cols(); u++) {
            for (int v = 0; v < projector->rows(); v++) {
                const int idx = current_frame.img_idx.ptr<int>(v)[u];
                if (idx == -1) continue;
                V2D px;
                V3D p = current_frame.points_corrected->points[idx].getVector3fMap().cast<double>();
                if (projector->projectPoint(p, px)) {
                    double diff = u - px(0);
                    if (diff > projector->cols() / 2) diff = diff - projector->cols();
                    if (diff < - projector->cols() / 2) diff = projector->cols() + diff;
                    u_shift = u_shift + (diff - u_shift) / (point_count + 1);
                    point_count++;
                }
            }
        }
    }

    std::cout << "Processed " << cloud_count << " clouds out of " << cloud_count_total << std::endl;
    std::cout << "Calculated Column Shift: " << std::round(u_shift) << std::endl;
    reader.close();

    rclcpp::shutdown();
    return 0;


}