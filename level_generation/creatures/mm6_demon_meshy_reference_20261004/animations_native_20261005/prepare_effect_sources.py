"""Prepare untouched native pixels for Blender's bundled NumPy, without installing dependencies."""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image

stage = Path(__file__).resolve().parent
native = stage.parent.parent / 'mm6_dmn/native'
names = [f'dmndth{letter}0' for letter in 'abcdefghi'] + ['m496xa0']
arrays = {name: np.array(Image.open(native / (name+'.png'))) for name in names}
arrays['ash_bbox'] = np.array(Image.open(native / 'm496xa0.png').getbbox())
np.savez_compressed(stage / 'native_effect_pixels.npz', **arrays)
(stage / 'native_effect_sources.json').write_text(json.dumps({
    name: {'path': str((native/(name+'.png')).relative_to(stage.parents[3])),
           'sha256': hashlib.sha256((native/(name+'.png')).read_bytes()).hexdigest()}
    for name in names}, indent=2)+'\n')
