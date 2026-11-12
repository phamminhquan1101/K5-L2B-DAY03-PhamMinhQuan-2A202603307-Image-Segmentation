"""One MobileSAM predictor and one cached image per Nuclio worker."""

import hashlib
import io
import os
import threading
import time

import numpy as np
from PIL import Image
import torch
from mobile_sam import SamPredictor, sam_model_registry

from mask_protocol import mask_to_cvat_rle, validate_prompts


class ModelHandler:
    def __init__(self):
        torch.set_num_threads(int(os.getenv("MOBILESAM_CPU_THREADS", "2")))
        requested = os.getenv("MOBILESAM_DEVICE", "auto")
        if requested not in {"auto", "cpu", "cuda"}:
            raise ValueError("MOBILESAM_DEVICE must be auto, cpu, or cuda")
        if requested == "cuda" and not torch.cuda.is_available():
            raise RuntimeError("CUDA is unavailable; deploy with -Device cpu or fix GPU access")
        self.device = "cuda" if requested == "cuda" or (
            requested == "auto" and torch.cuda.is_available()
        ) else "cpu"
        checkpoint = os.getenv("MOBILESAM_CHECKPOINT", "/opt/models/mobile_sam.pt")
        model = sam_model_registry["vit_t"](checkpoint=checkpoint)
        model.to(self.device).eval()
        self.predictor = SamPredictor(model)
        self.image_key = None
        self.lock = threading.Lock()
        self.info = {
            "model": "MobileSAM vit_t",
            "device": self.device,
            "torch": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "gpu": torch.cuda.get_device_name(0) if self.device == "cuda" else None,
            "checkpoint_sha256": hashlib.sha256(open(checkpoint, "rb").read()).hexdigest(),
        }

    def synchronize(self):
        if self.device == "cuda":
            torch.cuda.synchronize()

    @torch.inference_mode()
    def handle(self, image_bytes, pos_points, neg_points, obj_bbox=None):
        started = time.perf_counter()
        with Image.open(io.BytesIO(image_bytes)) as source:
            if source.width * source.height > 40_000_000:
                raise ValueError("Images above 40 megapixels are not supported")
            image = np.asarray(source.convert("RGB"))
        height, width = image.shape[:2]
        positive, negative, box = validate_prompts(
            pos_points, neg_points, obj_bbox, width, height
        )
        image_key = hashlib.sha256(image_bytes).digest()
        with self.lock:
            cache_hit = image_key == self.image_key
            self.synchronize()
            encoding_start = time.perf_counter()
            if not cache_hit:
                self.image_key = None
                self.predictor.set_image(image)
                self.image_key = image_key
            self.synchronize()
            encode_ms = (time.perf_counter() - encoding_start) * 1000
            coords = np.concatenate((positive, negative))
            labels = np.r_[np.ones(len(positive)), np.zeros(len(negative))].astype(np.int32)
            decode_start = time.perf_counter()
            masks, scores, _ = self.predictor.predict(
                point_coords=coords if len(coords) else None,
                point_labels=labels if len(coords) else None,
                box=box,
                multimask_output=True,
            )
            self.synchronize()
            decode_ms = (time.perf_counter() - decode_start) * 1000
            best = int(np.argmax(scores))
            rle = mask_to_cvat_rle(masks[best])
            meta = {
                **self.info,
                "width": width,
                "height": height,
                "embedding_cache_hit": cache_hit,
                "encode_ms": round(encode_ms, 2),
                "decode_ms": round(decode_ms, 2),
                "score": round(float(scores[best]), 4),
                "foreground_pixels": int(masks[best].sum()),
            }
            if self.device == "cuda":
                meta["cuda_peak_allocated_mib"] = round(torch.cuda.max_memory_allocated() / 2**20, 2)
                meta["cuda_peak_reserved_mib"] = round(torch.cuda.max_memory_reserved() / 2**20, 2)
        meta["handler_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return {
            "shapes": [] if rle is None else [{
                "type": "mask", "points": rle, "attributes": [],
                "group": 0, "source": "semi-auto", "occluded": False, "rotation": 0,
            }],
            "meta": meta,
        }
