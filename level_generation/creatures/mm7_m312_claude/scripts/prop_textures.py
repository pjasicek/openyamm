"""Cut the prop textures from the HD prop references (references_hd/spear.png side view, buckler.png front/back) and
write the silhouette profiles the mesh builder needs. Spear: columns 250..390 of the left (broad side) view, rows
0..1536 -> textures/props/spear.png (128 x 1024); per-row half-width of the blade/shaft (alpha) and of the feather
tassels -> textures/props/spear_profile.json. Buckler: front oval (x 145..710, y 40..990) and back oval
(x 830..1422, y 40..988) -> textures/props/buckler_front.png / buckler_back.png (512 x 512 each, stretched to fill).
Transparent pixels are filled with the nearest opaque colour so filtering never pulls in the background."""
import json, os
import numpy as np
from PIL import Image, ImageFilter
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda *p: os.path.join(HERE, *p)


def bleed(im, rounds=40):
    a = np.array(im.convert('RGBA')).astype(np.float32)
    rgb, al = a[:, :, :3], a[:, :, 3] > 128
    for _ in range(rounds):
        if al.all():
            break
        acc = np.zeros_like(rgb); cnt = np.zeros(al.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            m = np.roll(np.roll(al, dy, 0), dx, 1); c = np.roll(np.roll(rgb, dy, 0), dx, 1)
            acc += c * m[:, :, None]; cnt += m
        new = (~al) & (cnt > 0)
        rgb[new] = acc[new] / cnt[new][:, None]; al = al | new
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))


sp = Image.open(R('references_hd', 'spear.png')).convert('RGBA')
A = np.array(sp)[:, :, 3]
crop = sp.crop((250, 0, 390, 1536))
bleed(crop).resize((128, 1024), Image.LANCZOS).save(R('textures', 'props', 'spear.png'))
prof = {'crop_x0': 250, 'crop_w': 140, 'img_h': 1536, 'axis_col': 289, 'rows': {}, 'feathers': {}}
for y in range(0, 1536):
    xs = np.where(A[y, 250:330] > 128)[0] + 250                 # shaft/blade band (left of the tassels)
    if len(xs):
        prof['rows'][y] = [int(xs.min()), int(xs.max())]
    fx = np.where(A[y, 318:390] > 128)[0] + 318                 # tassels hang right of the shaft
    if len(fx) and y > 240:
        prof['feathers'][y] = [int(fx.min()), int(fx.max())]
json.dump(prof, open(R('textures', 'props', 'spear_profile.json'), 'w'))
bk = Image.open(R('references_hd', 'buckler.png')).convert('RGBA')
for name, box in (('buckler_front', (145, 40, 711, 991)), ('buckler_back', (830, 40, 1423, 989))):
    bleed(bk.crop(box)).resize((512, 512), Image.LANCZOS).save(R('textures', 'props', name + '.png'))
r = sorted(int(k) for k in prof['rows']); f = sorted(int(k) for k in prof['feathers'])
print('PROPTEX spear rows', r[0], r[-1], 'feather rows', f[0] if f else None, f[-1] if f else None)
