"""
Заглушка ИИ-модели распознавания лиц.
Когда появится реальная модель — заменить только этот файл.
Интерфейс остаётся тем же:
  detect_face(image_bytes, employee) -> int   (confidence 0–100)
  get_face_hash(image_bytes)         -> str   (хэш для хранения в BiometricData)
"""

import hashlib
import random


def detect_face(image_bytes: bytes, employee) -> int:
    """
    Возвращает уверенность распознавания лица (0–100).
    Заглушка: если у сотрудника зарегистрирован face_hash — симулируем
    высокую уверенность (70–95), иначе низкую (20–55).
    """
    try:
        bio = employee.biometricdata
        if bio.face_hash and bio.status:
            return random.randint(70, 95)
    except Exception:
        pass
    return random.randint(20, 55)


def get_face_hash(image_bytes: bytes) -> str:
    """
    Возвращает псевдохэш изображения для хранения в BiometricData.face_hash.
    Заглушка: SHA-256 от байтов изображения.
    """
    return hashlib.sha256(image_bytes).hexdigest()
