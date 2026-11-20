"""MM8 project paths and reviewed terrain colour/filter helpers."""
import hashlib
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

P = Path(__file__).resolve().parent
T = P.parent
ROOT = P.parents[2]
OUT = P / 'runtime_x2/worlds/mm8/terrain_x2'
M = P / 'masters/v1'
STAGE = Path('/tmp/openyamm-mm8-terrain-review')
spec = importlib.util.spec_from_file_location('terrain_seams', T / 'seam_repair/build.py')
seams = importlib.util.module_from_spec(spec)
spec.loader.exec_module(seams)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path, size=None):
    image = Image.open(path).convert('RGB')
    if size:
        image = image.resize((size, size), Image.Resampling.LANCZOS)
    return np.asarray(image, float)


def save(path, pixels):
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(seams.byte(pixels)).save(path)
