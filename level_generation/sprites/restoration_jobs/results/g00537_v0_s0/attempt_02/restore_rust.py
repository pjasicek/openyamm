"""Selective native chroma restoration; preserves generated detail, alpha and registration."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

out = Path(__file__).resolve().parent
root = out.parents[2]
key = 'a_0060aa54fc97d6578780'
target = out / (key + '.png')
backup = out / (key + '.before_rust.png')
if not backup.exists():
    backup.write_bytes(target.read_bytes())
im = np.array(Image.open(backup).convert('RGBA'))
native = Image.open(root / 'native' / (key + '.png')).convert('RGBA')
n = np.asarray(native.resize((im.shape[1], im.shape[0]), Image.Resampling.BILINEAR), dtype=float) / 255
rgb = im[..., :3].astype(float) / 255
weights = np.array([.2126, .7152, .0722])
a = n[..., 3]
# The native red/orange material alone owns this correction. Neutral rubble and blue faces stay intact.
red = np.clip((n[..., 0] / (n[..., 1] + .015) - 1.35) / .65, 0, 1) * a
mask = gaussian_filter(red, 1.4)
smooth = np.stack([gaussian_filter(n[..., c] * a, 1.4) for c in range(3)], axis=-1)
smooth /= np.maximum(gaussian_filter(a, 1.4)[..., None], 1e-5)
chroma = smooth / np.maximum((smooth @ weights)[..., None], 1e-5)
colored = (rgb @ weights)[..., None] * chroma * .80
rgb = rgb * (1 - mask[..., None]) + colored * mask[..., None]
im[..., :3] = np.uint8(np.clip(rgb * 255, 0, 255).round())
Image.fromarray(im).save(target)
(out / 'color_correction.json').write_text(json.dumps({'method':'native red-orange chroma on smoothed native red-material mask; generated luminance detail retained with 0.80 red-region exposure; alpha unchanged','source':str(root / 'native' / (key + '.png')),'script':'restore_rust.py','input_backup':backup.name,'reprocess_note':'After process, rerun this correction from a fresh ungraded final backup; check validates final pixels without resampling.'}, indent=2) + '\n')
