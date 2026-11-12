"""Nuclio interactor: standard CVAT prompts in, editable CVAT masks out."""

import base64
import binascii
import json

from PIL import UnidentifiedImageError
from model_handler import ModelHandler


def init_context(context):
    context.user_data.model = ModelHandler()
    context.logger.info("MobileSAM ready: " + json.dumps(context.user_data.model.info))


def handler(context, event):
    status = 200
    if event.method == "GET":
        result = {"status": "ready", **context.user_data.model.info}
    else:
        try:
            data = event.body
            if isinstance(data, (bytes, str)):
                data = json.loads(data)
            if not isinstance(data, dict) or not isinstance(data.get("image"), str):
                raise ValueError("Request must contain a base64 image")
            image_bytes = base64.b64decode(data["image"], validate=True)
            result = context.user_data.model.handle(
                image_bytes, data.get("pos_points", []), data.get("neg_points", []),
                data.get("obj_bbox"),
            )
        except (ValueError, TypeError, binascii.Error, UnidentifiedImageError) as error:
            result = {"error": str(error)}
            status = 400
    return context.Response(
        body=json.dumps(result, separators=(",", ":")),
        headers={}, content_type="application/json", status_code=status,
    )
