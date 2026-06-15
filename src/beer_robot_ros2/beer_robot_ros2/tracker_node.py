import json
import time

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class KalmanTracker:
    def __init__(self):
        self.initialized = False

        # State: [cx, cy, vx, vy]
        self.x = np.zeros((4, 1), dtype=np.float32)

        # State uncertainty
        self.P = np.eye(4, dtype=np.float32) * 500.0

        # Process noise: how much we distrust the motion model
        self.Q = np.eye(4, dtype=np.float32) * 1.0

        # Measurement noise: how much we distrust YOLO measurements
        self.R = np.eye(2, dtype=np.float32) * 50.0

        # Measurement matrix: camera sees only [cx, cy], not velocity
        self.H = np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
            ],
            dtype=np.float32,
        )

        self.I = np.eye(4, dtype=np.float32)

    def initialize(self, cx, cy):
        self.x = np.array(
            [
                [cx],
                [cy],
                [0],
                [0],
            ],
            dtype=np.float32,
        )

        self.P = np.eye(4, dtype=np.float32) * 500.0
        self.initialized = True

    def predict(self, dt):
        A = np.array(
            [
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ],
            dtype=np.float32,
        )

        self.x = A @ self.x
        self.P = A @ self.P @ A.T + self.Q

        return self.x

    def update(self, cx, cy):
        z = np.array([[cx], [cy]], dtype=np.float32)

        # Innovation: difference between YOLO measurement and prediction
        y = z - self.H @ self.x

        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ y
        self.P = (self.I - K @ self.H) @ self.P

        return self.x


class TrackerNode(Node):
    def __init__(self):
        super().__init__("tracker_node")

        self.tracker = KalmanTracker()
        self.last_time = time.time()
        self.last_detection_time = None

        self.sub = self.create_subscription(
            String,
            "/detections_raw",
            self.detection_callback,
            10,
        )

        self.pub = self.create_publisher(
            String,
            "/detections_tracked",
            10,
        )

        self.get_logger().info("Tracker node started")

    def detection_callback(self, msg: String):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now

        if dt <= 0.0 or dt > 1.0:
            dt = 0.033

        try:
            packet = json.loads(msg.data)
        except json.JSONDecodeError as e:
            self.get_logger().error(f"Invalid JSON in /detections_raw: {e}")
            return

        detections = packet.get("detections", [])
        best_detection = self.pick_best_detection(detections)

        # First detection initializes the filter
        if not self.tracker.initialized:
            if best_detection is None:
                self.pub.publish(String(data=json.dumps(packet)))
                return

            try:
                cx, cy = self.get_center(best_detection)
            except Exception as e:
                self.get_logger().error(f"Could not initialize tracker: {e}")
                self.pub.publish(String(data=json.dumps(packet)))
                return

            self.tracker.initialize(cx, cy)
            self.last_detection_time = now

        else:
            # Always predict first
            self.tracker.predict(dt)

            # If YOLO sees the object, correct prediction
            if best_detection is not None:
                try:
                    cx, cy = self.get_center(best_detection)
                    self.tracker.update(cx, cy)
                    self.last_detection_time = now
                except Exception as e:
                    self.get_logger().error(f"Could not update tracker: {e}")

        tracked_packet = self.build_output_packet(packet, best_detection, now)
        self.pub.publish(String(data=json.dumps(tracked_packet)))

    def pick_best_detection(self, detections):
        if not detections:
            return None

        return max(
            detections,
            key=lambda d: float(d.get("conf", d.get("confidence", 0.0))),
        )

    def get_box_xywh(self, detection):
        """
        Expected current format:
        detection["box"] = [x, y, w, h]

        Also supports a few common alternatives just in case.
        """

        if "box" in detection:
            box = detection["box"]
            x = float(box[0])
            y = float(box[1])
            w = float(box[2])
            h = float(box[3])
            return x, y, w, h

        if all(k in detection for k in ["x", "y", "width", "height"]):
            x = float(detection["x"])
            y = float(detection["y"])
            w = float(detection["width"])
            h = float(detection["height"])
            return x, y, w, h

        if "bbox" in detection:
            box = detection["bbox"]
            x = float(box[0])
            y = float(box[1])
            w = float(box[2])
            h = float(box[3])
            return x, y, w, h

        if "detection" in detection:
            box = detection["detection"]
            x1 = float(box[0])
            y1 = float(box[1])
            x2 = float(box[2])
            y2 = float(box[3])
            return x1, y1, x2 - x1, y2 - y1

        if all(k in detection for k in ["xmin", "ymin", "xmax", "ymax"]):
            x1 = float(detection["xmin"])
            y1 = float(detection["ymin"])
            x2 = float(detection["xmax"])
            y2 = float(detection["ymax"])
            return x1, y1, x2 - x1, y2 - y1

        raise KeyError(f"Unknown detection format: {detection}")

    def get_center(self, detection):
        x, y, w, h = self.get_box_xywh(detection)
        return x + w / 2.0, y + h / 2.0

    def build_output_packet(self, packet, best_detection, now):
        """
        Important:
        We keep the original packet structure because target_manager_node expects:

        packet["detections"]
        packet["frame_id"]
        packet["width"]
        packet["height"]
        packet["timings"]
        packet["should_detect"]

        So tracker_node only replaces detection coordinates with smoothed ones
        and adds packet["tracker"] for debugging.
        """

        tracked_packet = dict(packet)

        cx = float(self.tracker.x[0, 0])
        cy = float(self.tracker.x[1, 0])
        vx = float(self.tracker.x[2, 0])
        vy = float(self.tracker.x[3, 0])

        age = None
        if self.last_detection_time is not None:
            age = now - self.last_detection_time

        tracked_packet["tracker"] = {
            "enabled": True,
            "initialized": self.tracker.initialized,
            "center_x": cx,
            "center_y": cy,
            "vx": vx,
            "vy": vy,
            "last_detection_age": age,
            "source": "kalman_filter",
        }

        # If there is no current YOLO detection, keep detections empty.
        # This avoids fake detections going into target_manager.
        if best_detection is None:
            tracked_packet["detections"] = []
            return tracked_packet

        try:
            x, y, w, h = self.get_box_xywh(best_detection)
        except Exception as e:
            self.get_logger().error(f"Could not build tracked detection: {e}")
            tracked_packet["detections"] = packet.get("detections", [])
            return tracked_packet

        smoothed_x = cx - w / 2.0
        smoothed_y = cy - h / 2.0

        tracked_detection = dict(best_detection)

        # Preserve your current format
        tracked_detection["box"] = [
            smoothed_x,
            smoothed_y,
            w,
            h,
        ]

        # Also add explicit fields for debugging / future nodes
        tracked_detection["x"] = smoothed_x
        tracked_detection["y"] = smoothed_y
        tracked_detection["width"] = w
        tracked_detection["height"] = h
        tracked_detection["center_x"] = cx
        tracked_detection["center_y"] = cy
        tracked_detection["vx"] = vx
        tracked_detection["vy"] = vy
        tracked_detection["tracked"] = True

        tracked_packet["detections"] = [tracked_detection]

        return tracked_packet


def main(args=None):
    rclpy.init(args=args)

    node = TrackerNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()