import numpy as np
from sensor_msgs.msg import Image


def frame_to_image_msg(frame, frame_id: int) -> Image:
    msg = Image()
    msg.header.frame_id = str(frame_id)
    msg.height = int(frame.shape[0])
    msg.width = int(frame.shape[1])
    msg.encoding = "bgr8"
    msg.is_bigendian = False
    msg.step = int(frame.shape[1] * frame.shape[2])
    msg.data = frame.tobytes()
    return msg


def image_msg_to_frame(msg: Image):
    frame = np.frombuffer(msg.data, dtype=np.uint8)
    return frame.reshape((msg.height, msg.width, 3)).copy()
