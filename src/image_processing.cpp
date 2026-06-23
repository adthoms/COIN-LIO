// Copyright (c) 2024, Patrick Pfreundschuh
// https://opensource.org/license/bsd-3-clause

#include "image_processing.h"

#include <stdexcept>
#include "timing.h"

ImageProcessor::ImageProcessor(rclcpp::Node::SharedPtr node, std::shared_ptr<Projector> projector ,
    std::shared_ptr<FeatureManager> manager) : projector_(projector) {
    try {
        loadParameters(node);
    } catch (const std::runtime_error& e) {
        RCLCPP_ERROR_STREAM(rclcpp::get_logger("coin_lio"), e.what());
        exit(1);
    }

    rows_ = projector->rows();
    cols_ = projector->cols();
    min_range_ = manager->minRange();
    max_range_ = manager->maxRange();
    
    kernel_dx_ = cv::Mat::zeros(1, 3, CV_32F);
    kernel_dy_ = cv::Mat::zeros(3, 1, CV_32F);
    kernel_dx_.at<float>(0, 0) = -0.5;
    kernel_dx_.at<float>(0, 2) = 0.5;
    kernel_dy_.at<float>(0, 0) = -0.5;
    kernel_dy_.at<float>(2, 0) = 0.5;

    int k_size = manager->patchSize() + erosion_margin_;
    kernel_erosion_ = cv::Mat::ones(k_size, k_size, CV_32FC1);
};

void ImageProcessor::loadParameters(rclcpp::Node::SharedPtr node) {
    node->get_parameter_or("image.reflectivity", reflectivity_, false);
    node->get_parameter_or("image.line_removal", remove_lines_, true);
    node->get_parameter_or("image.brightness_filter", brightness_filter_, true);
    node->get_parameter_or("image.blur", blur_, true);
    node->get_parameter_or("image.intensity_scale", intensity_scale_, 0.25);
    int64_t erosion_margin;
    node->get_parameter_or("image.erosion_margin", erosion_margin, static_cast<int64_t>(2));
    erosion_margin_ = static_cast<int>(erosion_margin);
    std::vector<int64_t> window;
    node->get_parameter("image.window", window);
    if (window.size() != 2) {
        throw std::runtime_error("Invalid window size");
        return;
    }

    std::vector<int64_t> masks;
    node->get_parameter("image.masks", masks);
    if (masks.size() % 4 != 0) {
        throw std::runtime_error("Invalid masks, number of elements must be a multiple of 4");
        return;
    }

    for (int i = 0; i < masks.size()/4; i++) {
        masks_.push_back(cv::Rect(static_cast<int>(masks[i*4]), static_cast<int>(masks[i*4 +1]),
            static_cast<int>(masks[i*4 +2]), static_cast<int>(masks[i*4 +3])));
    }

    window_size_ = cv::Size(static_cast<int>(window[0]), static_cast<int>(window[1]));
    std::vector<double> hpf;
    node->get_parameter("image.highpass", hpf);
    high_pass_fir_ = cv::Mat(hpf).clone();
    std::vector<double> lpf;
    node->get_parameter("image.lowpass", lpf);
    low_pass_fir_ = cv::Mat(lpf).clone();
}

void ImageProcessor::createImages(LidarFrame& frame) {
    timing::Timer projection_timer("pre/projection");
    projector_->createImages(frame);
    projection_timer.Stop();

    if (!reflectivity_) {
        frame.img_intensity *= intensity_scale_;
    }

    timing::Timer img_process_timer("pre/image_process");

    if (remove_lines_) {
        removeLines(frame.img_intensity);
    }  

    if (brightness_filter_) {
        filterBrightness(frame.img_intensity);
    }

    if (blur_) {
        cv::Mat img_blur;
        cv::GaussianBlur(frame.img_intensity, img_blur, cv::Size(3,3), 0);
        frame.img_intensity = img_blur;
    }
    
    cv::threshold(frame.img_intensity, frame.img_intensity, 255., 255., cv::THRESH_TRUNC);
    
    // Convert to 8 bit for visualization
    frame.img_intensity.convertTo(frame.img_photo_u8, CV_8UC1, 1);

    // Calculate gradient images
    cv::filter2D(frame.img_intensity, frame.img_dx, CV_32F , kernel_dx_);
    cv::filter2D(frame.img_intensity, frame.img_dy, CV_32F , kernel_dy_);
    
    // Create mask
    createMask(frame.img_range, frame.img_mask);

    // Assign filtered intensity values to points
    #ifdef MP_EN
        omp_set_num_threads(MP_PROC_NUM);
        #pragma omp parallel for
    #endif
    for (int v = 0; v < rows_; v++) {
        for (int u = 0; u < cols_; u++) {
            const int idx = frame.img_idx.ptr<int>(v)[u];
            if (idx == -1) continue;
            frame.points_corrected->points[idx].normal_z = frame.img_intensity.ptr<float>(v)[u];
        }
    }   

    img_process_timer.Stop();
}

void ImageProcessor::removeLines(cv::Mat& img) {
    // Perform highpass vertically
    cv::Mat im_hpf;
    cv::filter2D(img, im_hpf, CV_32F , high_pass_fir_);
    // Perform lowpass horizontally
    cv::Mat im_lpf;
    cv::filter2D(im_hpf, im_lpf, CV_32F , low_pass_fir_.t());
    // Remove filtered signal from original image
    img -= im_lpf;
    img.setTo(0, img < 0);
}

void ImageProcessor::filterBrightness(cv::Mat& img) {
    // Create brightness map
    cv::Mat brightness;
    cv::blur(img, brightness, window_size_);
    brightness += 1;
    // Normalize and scale image
    cv::Mat normalized_img = (140.*img / brightness); 
    img = normalized_img;
}

void ImageProcessor::createMask(const cv::Mat& range_img, cv::Mat& mask) {
    // Mask out ouster connector
    mask = cv::Mat::ones(range_img.rows, range_img.cols, CV_8UC1);
    for (auto& mask_rect : masks_) {
        mask(mask_rect) = 0;
    }

    #ifdef MP_EN
        omp_set_num_threads(MP_PROC_NUM);
        #pragma omp parallel for
    #endif
    // Mask out points outside of range range
    for (int v = 0; v < rows_; v++) {
        for (int u = 0; u < cols_; u++) {
            const float r = range_img.ptr<float>(v)[u];
            if (r < min_range_ || r > max_range_) {
                mask.ptr<uchar>(v)[u] = 0u;
            }
        }
    }
    // Get a margin around the invalid pixels
    cv::Mat img_eroded;
    cv::erode(mask, img_eroded, kernel_erosion_);
    mask = img_eroded;
}