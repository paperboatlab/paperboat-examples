// Count parts: takes the processed picture (a mask, white parts on black) and the original,
// finds each part and sorts it by shape:
//   bolt   long (elongation ≥ bolt_elongation) or far from convex (two crossing)
//   washer has a hole and a round outline (roundness ≥ washer_roundness)
//   nut    everything else (a hexagon, with or without a visible hole)
// Outputs the counts and the original with each part outlined and labelled.

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include <opencv2/imgproc.hpp>
#include <paperboat/toolkit/opencv.hpp>

#include "parts.hpp"

namespace parts {
namespace tk = paperboat::toolkit;
namespace cvk = paperboat::toolkit::opencv;

namespace {

struct Part {
  std::vector<cv::Point> outline;
  std::string kind;
};

class Count final : public tk::Block {
 public:
  explicit Count(tk::Values params) : p_(std::move(params)) {}

  tk::Values step(const tk::Context&, const tk::Values& in) override {
    const cv::Mat* mask = cvk::image_in(in, "mask");
    if (!mask) return {};
    const std::vector<Part> found = sort(cvk::as_gray(*mask));

    double bolts = 0, nuts = 0, washers = 0;
    for (const auto& part : found) (part.kind == "bolt" ? bolts : part.kind == "washer" ? washers : nuts) += 1;
    tk::Values out{{"total", static_cast<double>(found.size())}, {"bolts", bolts}, {"nuts", nuts}, {"washers", washers}};
    if (const cv::Mat* photo = cvk::image_in(in, "photo")) out["marked"] = cvk::image_out(mark(*photo, found));
    return out;
  }

 private:
  std::vector<Part> sort(const cv::Mat& mask) const {
    std::vector<std::vector<cv::Point>> contours;
    std::vector<cv::Vec4i> tree;  // [next, previous, first child, parent]
    cv::findContours(mask, contours, tree, cv::RETR_CCOMP, cv::CHAIN_APPROX_SIMPLE);
    std::vector<Part> parts;
    for (std::size_t i = 0; i < contours.size(); ++i) {
      if (tree[i][3] >= 0) continue;  // a hole, not a part
      const double area = cv::contourArea(contours[i]);
      if (area < tk::get_or(p_, "min_area")) continue;

      bool hole = false;
      for (int c = tree[i][2]; c >= 0; c = tree[c][0]) hole = hole || cv::contourArea(contours[c]) > area * 0.04;
      const cv::RotatedRect box = cv::minAreaRect(contours[i]);
      const double elongation = std::max(box.size.width, box.size.height) / std::max(1.0f, std::min(box.size.width, box.size.height));
      std::vector<cv::Point> hull;
      cv::convexHull(contours[i], hull);
      const double perimeter = cv::arcLength(hull, true);
      const double roundness = 4 * CV_PI * cv::contourArea(hull) / std::max(perimeter * perimeter, 1.0);

      std::string kind = "nut";
      if (elongation >= tk::get_or(p_, "bolt_elongation") || roundness < 0.75) kind = "bolt";
      else if (hole && roundness >= tk::get_or(p_, "washer_roundness")) kind = "washer";
      parts.push_back({contours[i], kind});
    }
    return parts;
  }

  static cv::Mat mark(const cv::Mat& photo, const std::vector<Part>& parts) {
    cv::Mat out = photo.channels() == 3 ? photo.clone() : cv::Mat();
    if (out.empty()) cv::cvtColor(photo, out, cv::COLOR_GRAY2BGR);
    for (const auto& part : parts) {
      const cv::Scalar colour = part.kind == "bolt" ? cv::Scalar(40, 40, 220) : part.kind == "washer" ? cv::Scalar(220, 90, 30) : cv::Scalar(30, 160, 30);
      cv::polylines(out, part.outline, true, colour, 2);
      // Label centred on the part, in a white box so it reads on any background.
      const cv::Point2f c = cv::minAreaRect(part.outline).center;
      int base = 0;
      const cv::Size size = cv::getTextSize(part.kind, cv::FONT_HERSHEY_SIMPLEX, 0.45, 1, &base);
      const cv::Point at(static_cast<int>(c.x) - size.width / 2, static_cast<int>(c.y) + size.height / 2);
      cv::rectangle(out, at + cv::Point(-2, base), at + cv::Point(size.width + 2, -size.height - 2), {255, 255, 255}, cv::FILLED);
      cv::putText(out, part.kind, at, cv::FONT_HERSHEY_SIMPLEX, 0.45, colour, 1, cv::LINE_AA);
    }
    return out;
  }

  tk::Values p_;
};

}  // namespace

void register_parts(tk::Registry& registry) {
  registry.add(tk::define_block<Count>(
      "parts", {.type = "count",
                .label = "Count parts",
                .inputs = {cvk::image_port("mask"), cvk::image_port("photo")},
                .outputs = {{"total"}, {"bolts"}, {"nuts"}, {"washers"}, cvk::image_port("marked")},
                .params = {{"min_area", 150.0}, {"bolt_elongation", 2.2}, {"washer_roundness", 0.98}}}));
}

}  // namespace parts
