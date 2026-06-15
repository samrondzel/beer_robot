import math

from .config import (
    CAMERA_TILT_INITIAL, MAX_LOST_FRAMES, STABLE_FRAMES_REQUIRED,
    REID_DISTANCE_PX, DEAD_ZONE_PX, KP_TURN, TARGET_BOX_HEIGHT_RATIO,
    KP_FORWARD, MIN_FORWARD_SPEED, MAX_FORWARD_SPEED, MIN_SPEED, MAX_SPEED,
    CAMERA_TILT_MAX, TILT_STOP_MARGIN, DESIRED_TOP_Y_RATIO, TILT_DEAD_ZONE_PX,
    KP_TILT, CAMERA_TILT_MIN
)


class TargetManager:
    def __init__(self):
        self.target_id = None
        self.last_center = None
        self.last_box = None
        self.last_conf = 0.0

        self.camera_tilt_angle = CAMERA_TILT_INITIAL
        self.tilt_command = "HOLD"
        self.top_error = 0

        self.forward_speed = 0.0
        self.box_height_ratio = 0.0
        self.left_speed = 0.0
        self.right_speed = 0.0

        self.lost_frames = 0
        self.stable_frames = 0
        self.locked = False

        self.command = "SEARCH"
        self.command_text = "SEARCH for target"

    def reset(self):
        self.__init__()

    def target_name(self):
        if self.target_id is None:
            return "beer"
        return f"beer #{self.target_id}"

    def update(self, detections, frame_width, frame_height):
        selected = None

        # Prefer same tracked ID if available.
        if self.target_id is not None:
            for det in detections:
                if det.id == self.target_id:
                    selected = det
                    break

        # If ID disappeared, reconnect to nearest detection.
        if selected is None and self.last_center is not None and self.lost_frames <= MAX_LOST_FRAMES:
            selected = self.find_nearest_detection(detections)

        # If there is no target, pick the most confident detection.
        if selected is None:
            selected = self.get_best_detection(detections)

        if selected is not None:
            self.target_id = selected.id
            self.last_box = selected.box
            self.last_center = selected.center
            self.last_conf = selected.conf
            self.lost_frames = 0
            self.stable_frames += 1
        else:
            self.lost_frames += 1
            self.stable_frames = max(0, self.stable_frames - 1)

        self.locked = self.stable_frames >= STABLE_FRAMES_REQUIRED

        if self.lost_frames > MAX_LOST_FRAMES:
            old = self.target_name()
            self.reset()
            self.command_text = f"SEARCH for {old}"
            return self.command_text

        self.command, self.command_text = self.compute_command(frame_width)
        self.compute_motor_control(frame_width, frame_height)
        self.compute_camera_tilt_control(frame_height)

        return self.command_text

    def find_nearest_detection(self, detections):
        if self.last_center is None:
            return None

        last_cx, last_cy = self.last_center
        best_det = None
        best_dist = float("inf")

        for det in detections:
            cx, cy = det.center
            dist = math.hypot(cx - last_cx, cy - last_cy)

            if dist < best_dist:
                best_dist = dist
                best_det = det

        if best_det is not None and best_dist <= REID_DISTANCE_PX:
            return best_det

        return None

    def get_best_detection(self, detections):
        if not detections:
            return None
        return max(detections, key=lambda d: d.conf)

    def compute_command(self, frame_width):
        target = self.target_name()

        if self.last_center is None:
            return "SEARCH", f"SEARCH for {target}"

        if not self.locked:
            return "WAIT_FOR_LOCK", f"WAIT_FOR_LOCK on {target}"

        frame_center_x = frame_width // 2
        cx, _ = self.last_center
        error_x = cx - frame_center_x

        if abs(error_x) <= DEAD_ZONE_PX:
            return "FORWARD", f"FORWARD to {target}"
        if error_x < 0:
            return "TURN_LEFT", f"TURN_LEFT toward {target}"
        return "TURN_RIGHT", f"TURN_RIGHT toward {target}"

    def compute_motor_control(self, frame_width, frame_height):
        if self.last_center is None or self.last_box is None or not self.locked:
            self.left_speed = 0.0
            self.right_speed = 0.0
            self.forward_speed = 0.0
            self.box_height_ratio = 0.0
            return

        frame_center_x = frame_width // 2
        cx, _ = self.last_center
        error_x = cx - frame_center_x
        turn = KP_TURN * error_x

        x1, y1, x2, y2 = self.last_box
        box_height = y2 - y1
        self.box_height_ratio = box_height / max(1, frame_height)

        is_tilt_limit_reached = self.camera_tilt_angle >= CAMERA_TILT_MAX - TILT_STOP_MARGIN
        if is_tilt_limit_reached:
            self.forward_speed = 0.0
            self.left_speed = 0.0
            self.right_speed = 0.0
            self.command = "STOP"
            self.command_text = f"STOP near {self.target_name()}"
            return

        distance_error = TARGET_BOX_HEIGHT_RATIO - self.box_height_ratio
        forward = KP_FORWARD * distance_error
        forward = max(MIN_FORWARD_SPEED, min(MAX_FORWARD_SPEED, forward))

        self.forward_speed = forward
        self.left_speed = max(MIN_SPEED, min(MAX_SPEED, forward + turn))
        self.right_speed = max(MIN_SPEED, min(MAX_SPEED, forward - turn))

    def compute_camera_tilt_control(self, frame_height):
        if self.last_box is None or not self.locked:
            self.tilt_command = "HOLD"
            self.top_error = 0
            return

        _, y1, _, _ = self.last_box
        desired_top_y = int(frame_height * DESIRED_TOP_Y_RATIO)

        self.top_error = y1 - desired_top_y

        if abs(self.top_error) <= TILT_DEAD_ZONE_PX:
            self.tilt_command = "HOLD"
            return

        correction = KP_TILT * self.top_error
        self.camera_tilt_angle += correction
        self.camera_tilt_angle = max(CAMERA_TILT_MIN, min(CAMERA_TILT_MAX, self.camera_tilt_angle))

        self.tilt_command = "TILT_UP" if self.top_error > 0 else "TILT_DOWN"
