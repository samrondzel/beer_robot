import json
from collections import deque
import time

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from .config import PRINT_EVERY
from .target_manager import TargetManager
from .types import detections_from_dicts


class TargetManagerNode(Node):
    def __init__(self):
        super().__init__("target_manager_node")
        self.manager = TargetManager()

        self.publisher = self.create_publisher(String, "/target_state", 10)
        self.subscriber = self.create_subscription(String, "/detections_tracked", self.on_tracked, 10)

        self.loop_times = deque(maxlen=30)
        self.detect_times = deque(maxlen=10)
        self.last_loop_time = time.perf_counter()

        self.get_logger().info("Target manager node started")

    def on_tracked(self, msg: String):
        packet = json.loads(msg.data)
        detections = detections_from_dicts(packet["detections"])
        frame_id = int(packet["frame_id"])
        w = int(packet["width"])
        h = int(packet["height"])

        now = time.perf_counter()
        loop_dt = now - self.last_loop_time
        self.last_loop_time = now
        if loop_dt > 0:
            self.loop_times.append(loop_dt)

        command_text = self.manager.update(detections, w, h)

        timings = packet["timings"]
        if packet["should_detect"]:
            detect_dt = (timings["pre_ms"] + timings["infer_ms"] + timings["post_ms"]) / 1000.0
            if detect_dt > 0:
                self.detect_times.append(detect_dt)

        fps_loop = 1.0 / (sum(self.loop_times) / len(self.loop_times)) if self.loop_times else 0.0
        fps_detect = 1.0 / (sum(self.detect_times) / len(self.detect_times)) if self.detect_times else 0.0

        state = {
            "frame_id": frame_id,
            "width": w,
            "height": h,
            "detections": packet["detections"],
            "timings": timings,
            "fps_loop": fps_loop,
            "fps_detect": fps_detect,

            "target_id": self.manager.target_id,
            "target_name": self.manager.target_name(),
            "last_center": list(self.manager.last_center) if self.manager.last_center is not None else None,
            "last_box": list(self.manager.last_box) if self.manager.last_box is not None else None,
            "last_conf": self.manager.last_conf,

            "camera_tilt_angle": self.manager.camera_tilt_angle,
            "tilt_command": self.manager.tilt_command,
            "top_error": self.manager.top_error,

            "forward_speed": self.manager.forward_speed,
            "box_height_ratio": self.manager.box_height_ratio,
            "left_speed": self.manager.left_speed,
            "right_speed": self.manager.right_speed,

            "lost_frames": self.manager.lost_frames,
            "stable_frames": self.manager.stable_frames,
            "locked": self.manager.locked,

            "command": self.manager.command,
            "command_text": self.manager.command_text,
        }

        self.publisher.publish(String(data=json.dumps(state)))

        if frame_id % PRINT_EVERY == 0:
            print(
                f"frame={frame_id} | "
                f"target={self.manager.target_name()} | "
                f"locked={self.manager.locked} | "
                f"cmd={command_text} | "
                f"L/R={self.manager.left_speed:.2f}/{self.manager.right_speed:.2f} | "
                f"loop/det FPS={fps_loop:.2f}/{fps_detect:.2f} | "
                f"inf={timings['infer_ms']:.1f}ms"
            )


def main(args=None):
    rclpy.init(args=args)
    node = TargetManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
