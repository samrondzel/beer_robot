import os
import cv2

from .config import (
    DEAD_ZONE_PX, DESIRED_TOP_Y_RATIO, DETECT_EVERY,
    MAX_LOST_FRAMES
)


def draw_debug_frame(frame, detections, manager, fps_loop, fps_detect, timings, frame_id):
    debug = frame.copy()
    h, w = debug.shape[:2]
    center_x = w // 2

    # Lightweight robot guide lines.
    cv2.line(debug, (center_x, 0), (center_x, h), (80, 220, 255), 1)
    cv2.line(debug, (center_x - DEAD_ZONE_PX, 0), (center_x - DEAD_ZONE_PX, h), (80, 80, 80), 1)
    cv2.line(debug, (center_x + DEAD_ZONE_PX, 0), (center_x + DEAD_ZONE_PX, h), (80, 80, 80), 1)

    desired_top_y = int(h * DESIRED_TOP_Y_RATIO)
    cv2.line(debug, (0, desired_top_y), (w, desired_top_y), (255, 180, 0), 1)

    # Raw detections with stable IDs.
    for det in detections:
        x1, y1, x2, y2 = det.box
        label = f"beer #{det.id} {det.conf:.2f}"
        cv2.rectangle(debug, (x1, y1), (x2, y2), (120, 120, 120), 1)
        cv2.putText(debug, label, (x1, max(18, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

    # Selected target.
    if manager.last_box is not None and manager.lost_frames <= MAX_LOST_FRAMES:
        x1, y1, x2, y2 = manager.last_box
        cx, cy = manager.last_center
        color = (0, 255, 0) if manager.locked else (0, 180, 255)

        cv2.rectangle(debug, (x1, y1), (x2, y2), color, 2)
        cv2.circle(debug, (cx, cy), 4, color, -1)
        cv2.putText(debug, f"SELECTED {manager.target_name()} {manager.last_conf:.2f}",
                    (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        error_x = cx - center_x
    else:
        error_x = 0

    # Compact overlay.
    lines = [
        f"frame: {frame_id}  detect_every: {DETECT_EVERY}",
        f"loop/detect FPS: {fps_loop:.2f}/{fps_detect:.2f}",
        f"pre/inf/post ms: {timings['pre_ms']:.1f}/{timings['infer_ms']:.1f}/{timings['post_ms']:.1f}",
        f"CMD: {manager.command_text}",
        f"LOCKED: {manager.locked}  LOST: {manager.lost_frames}  STABLE: {manager.stable_frames}",
        f"ERR_X: {error_x}  BBOX_H: {manager.box_height_ratio:.2f}",
        f"L: {manager.left_speed:.2f}  R: {manager.right_speed:.2f}  FWD: {manager.forward_speed:.2f}",
        f"TILT: {manager.tilt_command} {manager.camera_tilt_angle:.1f}  TOP_ERR: {manager.top_error}",
    ]

    y = 18
    for line in lines:
        cv2.putText(debug, line, (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 180), 1)
        y += 17

    return debug
