# composite the flame texture through flame_elem_fire.json's ramp over grey, beside the original
import sys, json, numpy as np
sys.path.insert(0, '/home/pjasicek/github/OpenYAMM/level_generation/creatures/xeen_tiers_claude')
import xeen_tiers as xt, flame_ramps as fr
from PIL import Image
spec = json.load(open(sys.argv[1])); out = sys.argv[2]
cols = np.array(fr.ramp_colors(spec['skins']['xfie_d']['stops']))
a = np.asarray(Image.open('work_s12/elementals/fie1_img1_fie1_flame.png').convert('RGBA'), float) / 255
lum = xt.srgb_to_linear(a[..., :3]) @ np.array([0.2126, 0.7152, 0.0722])
lo, hi = 0.13437, 0.82708
t = np.clip((lum - lo) / (hi - lo), 0, 1) * 15
rgb = np.stack([np.interp(t, np.arange(16), cols[:, c]) for c in range(3)], -1)
srgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * rgb ** (1 / 2.4) - 0.055)
grey = np.full_like(srgb, 0.35)
al = a[..., 3:4]
new = srgb * al + grey * (1 - al); old = a[..., :3] * al + grey * (1 - al)
im = np.concatenate([old, new], 0)
Image.fromarray((im * 255).astype(np.uint8)).resize((512, 512)).save(out)
