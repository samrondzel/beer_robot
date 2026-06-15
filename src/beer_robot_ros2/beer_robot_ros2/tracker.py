import math

from .types import Detection


class CentroidTracker:
    def __init__(self, max_distance=100, max_lost=20):
        self.next_id = 1
        self.objects = {}
        self.lost = {}
        self.max_distance = max_distance
        self.max_lost = max_lost

    def update(self, detections):
        if not detections:
            for obj_id in list(self.lost.keys()):
                self.lost[obj_id] += 1
                if self.lost[obj_id] > self.max_lost:
                    self.objects.pop(obj_id, None)
                    self.lost.pop(obj_id, None)
            return []

        if not self.objects:
            for det in detections:
                det.id = self.next_id
                self.objects[self.next_id] = det
                self.lost[self.next_id] = 0
                self.next_id += 1
            return detections

        used_detections = set()
        used_objects = set()

        # Greedy nearest-centroid matching.
        for obj_id, old_det in list(self.objects.items()):
            ox, oy = old_det.center
            best_idx = None
            best_distance = float("inf")

            for i, det in enumerate(detections):
                if i in used_detections:
                    continue

                nx, ny = det.center
                dist = math.hypot(ox - nx, oy - ny)

                if dist < best_distance:
                    best_distance = dist
                    best_idx = i

            if best_idx is not None and best_distance <= self.max_distance:
                detections[best_idx].id = obj_id
                self.objects[obj_id] = detections[best_idx]
                self.lost[obj_id] = 0
                used_objects.add(obj_id)
                used_detections.add(best_idx)

        for obj_id in list(self.objects.keys()):
            if obj_id not in used_objects:
                self.lost[obj_id] += 1
                if self.lost[obj_id] > self.max_lost:
                    self.objects.pop(obj_id, None)
                    self.lost.pop(obj_id, None)

        for i, det in enumerate(detections):
            if i not in used_detections:
                det.id = self.next_id
                self.objects[self.next_id] = det
                self.lost[self.next_id] = 0
                self.next_id += 1

        return detections
