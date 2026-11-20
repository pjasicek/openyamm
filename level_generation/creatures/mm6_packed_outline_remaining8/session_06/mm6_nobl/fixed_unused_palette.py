"""Restore the twelve unused, fixed-palette native poses to palette 777."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fixed_unused_materials', ROOT / 'materials.py')
materials = importlib.util.module_from_spec(spec)
spec.loader.exec_module(materials)
config = json.loads((ROOT / 'config.json').read_text())
vectors = {int(key): value for key, value in json.loads((ROOT / 'recolor_vectors.json').read_text()).items()}


def correct(image):
    return materials.recolor(image, materials.coverage(image), 777, config, vectors)
