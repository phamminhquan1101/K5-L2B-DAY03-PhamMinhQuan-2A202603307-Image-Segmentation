"""Run with `docker exec -i cvat_server python manage.py shell`.

Uses Django's in-process test client as the existing task owner. No password,
token, account or annotation is created. The actual CVAT view, permissions,
image provider, Nuclio gateway and model execute normally.
"""

import hashlib
import json
from pathlib import Path
import time

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from cvat.apps.engine.models import Job, Task

FUNCTION = 'pth-mobilesam-local'
task = Task.objects.filter(name='easy_semantic', data__isnull=False).first()
if task is None:
    raise RuntimeError('Create an easy_semantic task with images before running this verification.')
job = Job.objects.filter(segment__task_id=task.id, type='annotation').order_by('id').first()
if job is None:
    raise RuntimeError('The selected task has no annotation job.')
user = task.owner or get_user_model().objects.filter(is_superuser=True, is_active=True).first()
if user is None:
    raise RuntimeError('No task owner is available for this integration test.')
client = APIClient()
client.force_authenticate(user=user)


def request(method, path, data=None):
    response = getattr(client, method)(path, data, format='json', HTTP_HOST='localhost')
    if response.status_code != 200:
        raise RuntimeError(f'{method.upper()} {path}: {response.status_code}: {response.content[:1000]!r}')
    return response.json()


functions = request('get', '/api/lambda/functions')
registered = next((item for item in functions if item['id'] == FUNCTION), None)
if not registered:
    raise RuntimeError('MobileSAM is not listed by the CVAT API.')
meta = request('get', f'/api/tasks/{task.id}/data/meta')
frame = meta['frames'][0]
width, height = frame['width'], frame['height']
annotation_path = f'/api/tasks/{task.id}/annotations'
before = request('get', annotation_path)
before_hash = hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest()
positive = [[round(width * .50), round(height * .84)]]
negative = [[round(width * .50), round(height * .16)]]
calls = []
for name, negatives, roi in [
    ('positive_point', [], None),
    ('positive_and_negative', negative, None),
    ('repeat_cached_image', negative, None),
    ('region_of_interest', [], [round(width * .20), round(height * .50), round(width * .80), height]),
]:
    data = {'task': task.id, 'job': job.id, 'frame': 0, 'pos_points': positive, 'neg_points': negatives}
    if roi is not None:
        data['roi'] = roi
    started = time.perf_counter()
    result = request('post', f'/api/lambda/functions/{FUNCTION}', data)
    if not result.get('shapes') or result['shapes'][0]['type'] != 'mask':
        raise RuntimeError(f'{name}: no editable CVAT mask returned')
    bounds = result['shapes'][0]['points'][-4:]
    if not (0 <= bounds[0] <= bounds[2] < width and 0 <= bounds[1] <= bounds[3] < height):
        raise RuntimeError(f'{name}: mask bounds do not match full-image coordinates: {bounds}')
    if roi is not None and not (bounds[0] >= roi[0] and bounds[1] >= roi[1]):
        raise RuntimeError('ROI mask was not translated back to full-image coordinates')
    calls.append({'case': name, 'http_status': 200,
                  'cvat_view_ms': round((time.perf_counter() - started) * 1000, 2),
                  'bounds': bounds, 'roi': roi, 'meta': result.get('meta', {})})
after = request('get', annotation_path)
after_hash = hashlib.sha256(json.dumps(after, sort_keys=True).encode()).hexdigest()
if before_hash != after_hash:
    raise RuntimeError('Task annotations changed during read-only inference verification')
report = {
    'verification': 'CVAT APIClient -> actual view/OPA -> Nuclio -> MobileSAM -> editable mask',
    'authentication': 'in-process test client as the existing owner; no token created',
    'task_id': task.id, 'job_id': job.id, 'task_name': task.name, 'frame': 0,
    'frame_name': frame['name'], 'frame_size': [width, height],
    'registered_function': registered, 'positive_points': positive, 'negative_points': negative,
    'calls': calls, 'annotation_sha256_before': before_hash,
    'annotation_sha256_after': after_hash, 'annotations_unchanged': True,
    'browser_click_verification': False,
}
Path('/tmp/mobilesam-cvat-verification.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
