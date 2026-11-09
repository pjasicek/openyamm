"""Tier-A scale from silhouette area (flyer rule of the quadruped playbook): mean front and side alpha area of the
model's Standing flight cycle (review/scale/*.png, ortho 1.6 m at 600 px) against the native m182 flight frames
(review/scale/native_measure.json, frame scale 5.0). Writes review/scale/measurement.json."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
P = Path(__file__).resolve().parents[1]; S = P / 'review/scale'
native = json.loads((S / 'native_measure.json').read_text()); px_per_m = 600 / 1.6
out = {}
for view, key in (('front', 'view0'), ('side', 'view2')):
    areas = [float((np.asarray(Image.open(S / f'{view}_{i:02d}.png'))[..., 3] > 127).sum()) / px_per_m ** 2 for i in range(11)]
    model = float(np.mean(areas)); world = native[key]['mean_area'] * 5.0 ** 2
    out[view] = {'model_area_m2': model, 'native_area_px2': native[key]['mean_area'], 'native_area_world': world, 'scale': (world / model) ** .5}
out['scale_tier_a'] = float(np.mean([out['front']['scale'], out['side']['scale']]))
out['tier_scales'] = {'ADragon A': out['scale_tier_a'], 'ADragon B': out['scale_tier_a'] * 5.099991 / 5.0, 'ADragon C': out['scale_tier_a'] * 5.25 / 5.0}
(S / 'measurement.json').write_text(json.dumps(out, indent=2) + '\n'); print(json.dumps(out, indent=1))
