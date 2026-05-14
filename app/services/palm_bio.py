import os
import requests

VEIN_SERVICE_URL = os.environ.get('VEIN_SERVICE_URL', 'http://vein-service:8001')


def detect_face(image_bytes: bytes, employee) -> int:
    try:
        bio = employee.biometricdata
        if not bio.palm_hash:
            return 0
        resp = requests.post(
            f'{VEIN_SERVICE_URL}/compare',
            files={'image': ('palm.jpg', image_bytes, 'image/jpeg')},
            data={'stored_hash': bio.palm_hash},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get('confidence', 0)
    except Exception:
        return 0


def get_face_hash(image_bytes: bytes) -> str:
    resp = requests.post(
        f'{VEIN_SERVICE_URL}/embed',
        files={'image': ('palm.jpg', image_bytes, 'image/jpeg')},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()['hash']
