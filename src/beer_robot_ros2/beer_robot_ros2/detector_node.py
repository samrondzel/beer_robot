import json
import time

import ncnn
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from .config import MODEL_PARAM, MODEL_BIN, NCNN_THREADS, DETECT_EVERY
from .image_utils import image_msg_to_frame
from .ncnn_detector import run_inference
from .types import detections_to_dicts


class DetectorNode(Node):
    def __init__(self):
        super().__init__("detector_node")

        self.net = ncnn.Net()
        self.net.opt.num_threads = NCNN_THREADS
        self.net.opt.use_vulkan_compute = False

        self.net.load_param(MODEL_PARAM)
        self.net.load_model(MODEL_BIN)

        self.publisher = self.create_publisher(String, "/detections_raw", 10)
        self.subscriber = self.create_subscription(Image, "/camera/image", self.on_image, 10)

        self.last_detections = []
        self.last_timings = {"pre_ms": 0.0, "infer_ms": 0.0, "post_ms": 0.0}

        self.get_logger().info(
            f"NCNN loaded; threads={NCNN_THREADS}, detect_every={DETECT_EVERY}"
        )

    def on_image(self, msg: Image):
        frame = image_msg_to_frame(msg)
        frame_id = int(msg.header.frame_id) if msg.header.frame_id else 0
        h, w = frame.shape[:2]

        should_detect = (frame_id % DETECT_EVERY == 0)

        if should_detect:
            detections, self.last_timings = run_inference(self.net, frame)
            self.last_detections = detections
        else:
            detections = self.last_detections

        packet = {
            "frame_id": frame_id,
            "width": w,
            "height": h,
            "should_detect": should_detect,
            "detections": detections_to_dicts(detections),
            "timings": self.last_timings,
        }

        self.publisher.publish(String(data=json.dumps(packet)))


def main(args=None):
    rclpy.init(args=args)
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
