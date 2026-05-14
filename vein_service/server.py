import os
import sys
import base64
import tempfile
import numpy as np
from flask import Flask, request, jsonify

VEIN_REPO = '/opt/vein_recognition'
MODEL_PATH = os.path.join(VEIN_REPO, 'results', 'best', 'huita.pt')

sys.path.insert(0, os.path.join(VEIN_REPO, 'src'))

import torch
from identify_person import Identifier

device = 'cuda' if torch.cuda.is_available() else 'cpu'
identifier = None
_load_error = None
print(f'Loading model on {device}...')
try:
    identifier = Identifier(MODEL_PATH, device=device)
    print('Model ready.')
except Exception as e:
    _load_error = str(e)
    print(f'WARNING: model not loaded — {e}')

app = Flask(__name__)


def _get_embedding(image_bytes: bytes) -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    try:
        return identifier.get_embedding(tmp_path)  # type: ignore[union-attr]
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _vec_to_str(vec: np.ndarray) -> str:
    return base64.b64encode(vec.astype(np.float32).tobytes()).decode()


def _str_to_vec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.float32)


@app.route('/health', methods=['GET'])
def health():
    if identifier is None:
        return jsonify({'status': 'degraded', 'error': _load_error}), 503
    return jsonify({'status': 'ok'})


@app.route('/embed', methods=['POST'])
def embed():
    if identifier is None:
        return jsonify({'error': f'Model not loaded: {_load_error}'}), 503
    if 'image' not in request.files:
        return jsonify({'error': 'image required'}), 400
    image_bytes = request.files['image'].read()
    try:
        embedding = _get_embedding(image_bytes)
        return jsonify({'hash': _vec_to_str(embedding)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/compare', methods=['POST'])
def compare():
    if identifier is None:
        return jsonify({'error': f'Model not loaded: {_load_error}'}), 503
    if 'image' not in request.files:
        return jsonify({'error': 'image required'}), 400
    stored_hash = request.form.get('stored_hash', '')
    if not stored_hash:
        return jsonify({'error': 'stored_hash required'}), 400

    image_bytes = request.files['image'].read()
    try:
        embedding = _get_embedding(image_bytes)
        stored = _str_to_vec(stored_hash)
        # Both vectors are L2-normalized → dot product = cosine similarity
        sim = float(np.dot(embedding, stored))
        confidence = int(max(0, min(100, sim * 100)))
        return jsonify({'confidence': confidence})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)
