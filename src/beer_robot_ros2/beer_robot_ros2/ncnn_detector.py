import time
import cv2
import ncnn
import numpy as np

from .config import INPUT_SIZE, CONF_THRES, NMS_THRES
from .types import Detection


def preprocess(frame):
    img = cv2.resize(frame, (INPUT_SIZE, INPUT_SIZE), interpolation=cv2.INTER_LINEAR)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    x = img.astype(np.float32) * (1.0 / 255.0)
    x = np.transpose(x, (2, 0, 1))
    x = np.ascontiguousarray(x)

    return ncnn.Mat(x).clone()


def flatten_nms_indices(indices):
    if indices is None or len(indices) == 0:
        return []
    return [int(i) for i in np.array(indices).reshape(-1)]


def postprocess(out, orig_w, orig_h):
    """
    Expected YOLO one-class output:
    either (5, N) or (N, 5), with cx, cy, w, h, conf.
    """
    arr = np.array(out)

    if arr.ndim == 3:
        arr = np.squeeze(arr)

    if arr.shape[0] == 5:
        preds = arr.T
    else:
        preds = arr

    boxes = []
    scores = []

    scale_x = orig_w / INPUT_SIZE
    scale_y = orig_h / INPUT_SIZE

    for det in preds:
        cx, cy, bw, bh, conf = det[:5]
        conf = float(conf)

        if conf < CONF_THRES:
            continue

        x1 = int((cx - bw / 2) * scale_x)
        y1 = int((cy - bh / 2) * scale_y)
        x2 = int((cx + bw / 2) * scale_x)
        y2 = int((cy + bh / 2) * scale_y)

        x1 = max(0, min(x1, orig_w - 1))
        y1 = max(0, min(y1, orig_h - 1))
        x2 = max(0, min(x2, orig_w - 1))
        y2 = max(0, min(y2, orig_h - 1))

        w = max(1, x2 - x1)
        h = max(1, y2 - y1)

        boxes.append([x1, y1, w, h])
        scores.append(conf)

    detections = []

    if not boxes:
        return detections

    keep = flatten_nms_indices(cv2.dnn.NMSBoxes(boxes, scores, CONF_THRES, NMS_THRES))

    for i in keep:
        x, y, w, h = boxes[i]
        x1, y1, x2, y2 = x, y, x + w, y + h
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        detections.append(
            Detection(
                id=None,
                box=(x1, y1, x2, y2),
                center=(cx, cy),
                conf=float(scores[i]),
            )
        )

    return detections


def run_inference(net, frame):
    orig_h, orig_w = frame.shape[:2]

    t0 = time.perf_counter()
    mat = preprocess(frame)
    t1 = time.perf_counter()

    ex = net.create_extractor()
    ex.input("in0", mat)

    ret, out = ex.extract("out0")
    t2 = time.perf_counter()

    if ret != 0:
        print(f"NCNN extract failed with code: {ret}")
        return [], {"pre_ms": (t1 - t0) * 1000, "infer_ms": 0.0, "post_ms": 0.0}

    detections = postprocess(out, orig_w, orig_h)
    t3 = time.perf_counter()

    timings = {
        "pre_ms": (t1 - t0) * 1000,
        "infer_ms": (t2 - t1) * 1000,
        "post_ms": (t3 - t2) * 1000,
    }

    return detections, timings
