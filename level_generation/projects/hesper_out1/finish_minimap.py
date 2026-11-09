"""Grade the rendered minimap with the approved recipe (level_generation/minimaps/approved_recipe.json: contrast,
saturation, unsharp mask) and export it at the recipe's size as runtime/worlds/hesper/icons_x2/hes_out1.bmp
(PNG bytes under the .bmp name, as the other worlds' minimaps)."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

PROJECT = Path(__file__).resolve().parent
ROOT = PROJECT.parents[2]
recipe = json.loads((ROOT / 'level_generation/minimaps/approved_recipe.json').read_text())
image = Image.open(PROJECT / 'work/minimap_raw.png').convert('RGB')
grade = recipe['global_grade']
pixels = np.asarray(image, dtype=np.float32) / 255
pixels = np.clip((pixels - grade['contrast_pivot']) * grade['contrast'] + grade['contrast_pivot'], 0, 1)
image = Image.fromarray((pixels * 255 + 0.5).astype(np.uint8), 'RGB')
image = ImageEnhance.Color(image).enhance(grade['saturation'])
sharp = recipe['unsharp']
image = image.filter(ImageFilter.UnsharpMask(radius=sharp['radius_master_pixels'], percent=int(sharp['amount'] * 100),
                                             threshold=sharp['threshold_255']))
image.save(PROJECT / 'work/minimap_master.png')
target = PROJECT / 'runtime/worlds/hesper/icons_x2/hes_out1.bmp'
target.parent.mkdir(parents=True, exist_ok=True)
size = recipe['export_size']
image.resize((size, size), Image.LANCZOS).save(target, format='PNG')
target.chmod(0o644)
print(target)
