import cv2
import rclpy
from rclpy.node import Node

from .config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS
from .image_utils import frame_to_image_msg


class CameraNode(Node):
    def __init__(self):
        super().__init__("camera_node")
        self.publisher = self.create_publisher(__import__("sensor_msgs.msg").msg.Image, "/camera/image", 10)

        self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
        if not self.cap.isOpened():
            self.cap = cv2.VideoCapture(CAMERA_INDEX)

        """
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        """

        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")

        self.frame_id = 0
        self.timer = self.create_timer(0.0, self.tick)
        self.get_logger().info("Camera node started")

    def tick(self):
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().warn("Could not read frame")
            return

        msg = frame_to_image_msg(frame, self.frame_id)
        self.publisher.publish(msg)
        self.frame_id += 1

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
