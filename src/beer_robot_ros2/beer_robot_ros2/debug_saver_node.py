import json
import os

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

from .config import SAVE_DIR, SAVE_EVERY
from .debug import draw_debug_frame
from .image_utils import image_msg_to_frame
from .target_manager import TargetManager
from .types import detections_from_dicts


class DebugSaverNode(Node):
    def __init__(self):
        super().__init__("debug_saver_node")
        os.makedirs(SAVE_DIR, exist_ok=True)

        self.latest_frame = None
        self.latest_frame_id = -1

        self.image_sub = self.create_subscription(Image, "/camera/image", self.on_image, 10)
        self.state_sub = self.create_subscription(String, "/target_state", self.on_state, 10)

        self.get_logger().info(f"Debug saver started; saving to {SAVE_DIR}/ every {SAVE_EVERY} frames")

    def on_image(self, msg: Image):
        self.latest_frame = image_msg_to_frame(msg)
        self.latest_frame_id = int(msg.header.frame_id) if msg.header.frame_id else 0

    def on_state(self, msg: String):
        if self.latest_frame is None:
            return

        state = json.loads(msg.data)
        frame_id = int(state["frame_id"])

        if frame_id % SAVE_EVERY != 0:
            return

        manager = TargetManager()
        manager.target_id = state["target_id"]
        manager.last_center = tuple(state["last_center"]) if state["last_center"] is not None else None
        manager.last_box = tuple(state["last_box"]) if state["last_box"] is not None else None
        manager.last_conf = state["last_conf"]

        manager.camera_tilt_angle = state["camera_tilt_angle"]
        manager.tilt_command = state["tilt_command"]
        manager.top_error = state["top_error"]

        manager.forward_speed = state["forward_speed"]
        manager.box_height_ratio = state["box_height_ratio"]
        manager.left_speed = state["left_speed"]
        manager.right_speed = state["right_speed"]

        manager.lost_frames = state["lost_frames"]
        manager.stable_frames = state["stable_frames"]
        manager.locked = state["locked"]

        manager.command = state["command"]
        manager.command_text = state["command_text"]

        detections = detections_from_dicts(state["detections"])
        timings = state["timings"]

        debug = draw_debug_frame(
            frame=self.latest_frame,
            detections=detections,
            manager=manager,
            fps_loop=state["fps_loop"],
            fps_detect=state["fps_detect"],
            timings=timings,
            frame_id=frame_id,
        )

        cv2.imwrite(os.path.join(SAVE_DIR, "latest.jpg"), debug)
        cv2.imwrite(os.path.join(SAVE_DIR, f"frame_{frame_id:06d}.jpg"), debug)


def main(args=None):
    rclpy.init(args=args)
    node = DebugSaverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
