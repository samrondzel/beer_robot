from dataclasses import dataclass
from typing import Optional, Tuple, List
import json

@dataclass
class Detection:
    id: Optional[int]
    box: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    conf: float


def detection_to_dict(det: Detection) -> dict:
    return {
        "id": det.id,
        "box": list(det.box),
        "center": list(det.center),
        "conf": float(det.conf),
    }


def detection_from_dict(data: dict) -> Detection:
    return Detection(
        id=data.get("id"),
        box=tuple(int(v) for v in data["box"]),
        center=tuple(int(v) for v in data["center"]),
        conf=float(data["conf"]),
    )


def detections_to_dicts(detections: List[Detection]) -> list:
    return [detection_to_dict(det) for det in detections]


def detections_from_dicts(items: list) -> List[Detection]:
    return [detection_from_dict(item) for item in items]
