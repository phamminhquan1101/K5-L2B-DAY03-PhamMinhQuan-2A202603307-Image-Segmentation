"""CVAT's row-major RLE, including inclusive bounding-box coordinates."""

import numpy as np


def mask_to_cvat_rle(mask):
    mask = np.asarray(mask, dtype=np.bool_)
    if mask.ndim != 2:
        raise ValueError("Mask must have two dimensions")
    ys, xs = np.nonzero(mask)
    if not len(xs):
        return None
    left, top, right, bottom = map(int, (xs.min(), ys.min(), xs.max(), ys.max()))
    pixels = mask[top:bottom + 1, left:right + 1].reshape(-1)
    boundaries = np.flatnonzero(pixels[1:] != pixels[:-1]) + 1
    runs = np.diff(np.r_[0, boundaries, pixels.size]).astype(int).tolist()
    if pixels[0]:
        runs.insert(0, 0)
    return runs + [left, top, right, bottom]


def validate_prompts(pos_points, neg_points, obj_bbox, width, height):
    def points(value, name):
        array = np.asarray(value, dtype=np.float32)
        if not array.size:
            return np.empty((0, 2), dtype=np.float32)
        if array.ndim != 2 or array.shape[1] != 2 or not np.isfinite(array).all():
            raise ValueError(f"{name} must contain finite [x, y] pairs")
        if len(array) > 256:
            raise ValueError("At most 256 points of each type are supported")
        if (array < 0).any() or (array[:, 0] >= width).any() or (array[:, 1] >= height).any():
            raise ValueError(f"{name} are outside the image")
        return array

    positive = points(pos_points, "pos_points")
    negative = points(neg_points, "neg_points")
    box = None
    if obj_bbox is not None and len(obj_bbox):
        candidate = np.asarray(obj_bbox, dtype=np.float32)
        if candidate.size != 4 or not np.isfinite(candidate).all():
            raise ValueError("obj_bbox must contain [x1, y1, x2, y2]")
        box = candidate.reshape(4)
        if not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height):
            raise ValueError("obj_bbox is outside the image or has zero area")
    if not len(positive) and box is None:
        raise ValueError("At least one positive point or a bounding box is required")
    return positive, negative, box
