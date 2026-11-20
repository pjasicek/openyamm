from pathlib import Path
import json
import numpy as np
from PIL import Image

p = Path(__file__).resolve().parent
gain = 0.9071001916205912
checks = json.loads((p / 'checks.json').read_text())
for key in checks['frames']:
    target = p / f'{key}.png'
    backup = p / f'{key}.before_tone.png'
    if not backup.exists():
        backup.write_bytes(target.read_bytes())
    pixels = np.array(Image.open(backup).convert('RGBA'))
    rgb = pixels[:, :, :3].astype(float)
    weight = np.clip((rgb[:, :, 0] - rgb[:, :, 2] - 35) / 60, 0, 1)
    weight *= np.clip((rgb[:, :, 1] - rgb[:, :, 2] - 15) / 40, 0, 1)
    pixels[:, :, :3] = np.rint(rgb * (1 + weight[:, :, None] * (gain - 1))).astype(np.uint8)
    Image.fromarray(pixels).save(target)
(p / 'flame_grade.json').write_text(json.dumps({
    'gain': gain, 'gain_source': 'g08012_v0_s0/attempt_02/flame_grade.json',
    'selection': 'smooth red-blue and green-blue differences', 'alpha_unchanged': True
}, indent=2) + '\n')
