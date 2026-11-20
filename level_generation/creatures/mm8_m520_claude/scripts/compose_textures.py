"""Native brown/blue/red trim, matte surfaces and matched body/head skin."""
from pathlib import Path
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent/'claude_shared'))
import region_variants as R
N = 1024
T = P/'textures'
T.mkdir(exist_ok=True)


def load(path):
    return np.asarray(Image.open(path).convert('RGB').resize((N, N), Image.Resampling.LANCZOS), float)/255


def save(array, path):
    Image.fromarray(np.uint8(np.clip(array, 0, 1)*255+.5)).save(path)


def hsv(array):
    a = np.asarray(Image.fromarray(np.uint8(np.clip(array, 0, 1)*255)).convert('HSV'), float)/255
    return a[..., 0]*360, a[..., 1], a[..., 2]


def pad(array, covered):
    _, (y, x) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return array[y, x]


r = np.load(P/'work/uvraster_UVMap.npz')
hr = np.load(P/'work/uvraster_HeadUV.npz')
piece, pos = r['piece'], r['pos']
hpos = hr['pos']
covered, hcovered = piece >= 0, hr['piece'] >= 0
base = load(P/'meshy/body_retexture_v1/texture_urls_0_base_color.png')
head = load(P/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
normal = load(P/'meshy/body_retexture_v1/texture_urls_0_normal.png')
hnormal = load(P/'meshy/head_retexture_v1/texture_urls_0_normal.png')
h, sat, val = hsv(base)
hh, hs, hv = hsv(head)
classes = np.zeros((N, N), np.uint8)
classes[covered] = 1
cloth = ((piece == 1) & (pos[..., 2] < .64)) | ((piece == 0) & (abs(pos[..., 0]) < .45) & (pos[..., 2] < 1.32))
classes[cloth] = 2
belt = (piece == 0) & (abs(pos[..., 0]) < .45) & (pos[..., 2] > 1.28) & (pos[..., 2] < 1.43)
wrists = np.zeros_like(covered)
joints = json.loads((P/'work/joints_final.json').read_text())['joints']
for side in 'LR':
    elbow, wrist = [np.array(joints[f'{side}_{n}']) for n in ['Forearm', 'Hand']]
    axis = wrist-elbow
    t = ((pos-elbow)@axis)/(axis@axis)
    radius = np.linalg.norm(pos-elbow-t[..., None]*axis, axis=-1)
    wrists |= (piece == 0) & (t > .57) & (t < 1.08) & (radius < .15)
leather = belt | wrists | np.isin(piece, [2, 3, 4, 5])
classes[leather] = 3
discs = np.isin(piece, [6, 7, 8])
classes[discs] = 4
studs = belt & (sat < .22) & (val > .4)
classes[studs] = 4
hc = np.zeros_like(classes)
hc[hcovered] = 1
hair = hcovered & (hv < .32) & ((abs(hpos[..., 0]) > .07) | (hpos[..., 1] > .04) | (hpos[..., 2] > 2.23))
hc[hair] = 5
green = hcovered & (hh > 65) & (hh < 170) & (hs > .3) & (hv > .16) & (hpos[..., 1] < 0)
assert green.sum() > 20, int(green.sum())
eye_centre = np.median(hpos[green], axis=0)
delta = (hpos-eye_centre)/np.array([.070, .040, .027])
eye = hcovered & ((delta*delta).sum(-1) < 1)
hc[eye] = 6
mouth = hcovered & (abs(hpos[..., 0]) < .075) & (hpos[..., 2] > 2.055) & (hpos[..., 2] < 2.11) & (hpos[..., 1] < -.08)
hc[mouth & (hv < .4)] = 7
hc[mouth & (hv > .6) & (hs < .4)] = 8
neck_body = (classes == 1) & (pos[..., 2] > 1.96) & (pos[..., 2] < 2.02) & (abs(pos[..., 0]) < .13) & (pos[..., 1] < 0)
neck_head = (hc == 1) & (hpos[..., 2] < 2.06) & (hpos[..., 1] < 0)
assert min(neck_body.sum(), neck_head.sum()) > 40
gain = np.median(base[neck_body], axis=0)/np.maximum(np.median(head[neck_head], axis=0), .01)
assert (gain > .5).all() and (gain < 1.7).all(), gain
head[hc == 1] = np.clip(head[hc == 1]*gain, 0, 1)
seams = json.loads((P/'work/seam_samples.json').read_text())
tree = cKDTree([s['pos'] for s in seams])


def sample(image, field):
    uv = np.array([s[field] for s in seams])
    xy = np.clip(np.floor(uv*N).astype(int), 0, N-1)
    return image[N-1-xy[:, 1], xy[:, 0]]


bcol, hcol = sample(base, 'body'), sample(head, 'head')
d, ids = tree.query(hpos[hcovered], k=12)
weight = 1/np.maximum(d, .008)**2
correction = ((bcol-hcol)[ids]*weight[..., None]).sum(1)/weight.sum(1)[:, None]
u = np.clip(1-d[:, 0]/.055, 0, 1)
head[hcovered] = np.clip(head[hcovered]+correction*(u*u*(3-2*u))[:, None], 0, 1)
for coords, cov, image in [(pos, covered, normal), (hpos, hcovered, hnormal)]:
    distance, _ = tree.query(coords[cov])
    u = np.clip(distance/.008, 0, 1)
    image[cov] = image[cov]*u[:, None]+np.array([.5, .5, 1])*(1-u[:, None])
response = {0:(0, 1, 0), 1:(.025, .85, 0), 2:(.02, .95, 0), 3:(.10, .80, 0),
            4:(.55, .60, .4), 5:(.025, .88, 0), 6:(.9, .20, 0), 7:(.05, .85, 0), 8:(.15, .55, 0)}


def mr(labels):
    out = np.empty((N, N, 3))
    for cls, value in response.items():
        out[labels == cls] = value
    return out


trim = (discs | ((belt | wrists) & (sat > .32) & (h < 65) & (val < .8))) & covered
assert trim.sum() > 2000, int(trim.sum())
base, head, normal, hnormal = [pad(a, c) for a, c in [(base, covered), (head, hcovered), (normal, covered), (hnormal, hcovered)]]
palette_dir = P.parents[2]/'assets_dev/worlds/mm8/textures'
palettes = {f'm520_{tier}':np.frombuffer((palette_dir/f'Pal{index}.act').read_bytes()[:768], np.uint8).reshape(256, 3)/255
            for tier, index in zip('abc', [521, 522, 523])}
changed = np.where(np.max(abs(palettes['m520_a']-palettes['m520_c']), axis=1) > .12)[0]
order = changed[np.argsort(R.luminance(palettes['m520_a'][changed]))]
light = R.luminance(base)
lo, hi = np.percentile(light[trim], [1, 99])
ramps = {}
for tier, palette in palettes.items():
    stops = np.stack([np.interp(np.linspace(0, len(order)-1, 16), np.arange(len(order)), palette[order, c]) for c in range(3)], axis=1)
    colors = R.srgb_to_linear(np.clip(stops*1.3, 0, 1))
    ramps[tier] = [{'range':[float(lo), float(hi)], 'colors':colors.round(6).tolist()}]
mask = ndimage.gaussian_filter(pad(trim.astype(float), covered), .5)
for prefix, b, n, labels, cov in [('m520', base, normal, classes, covered), ('m520_head', head, hnormal, hc, hcovered)]:
    save(b, T/f'{prefix}_basecolor_1k.png')
    save(n, T/f'{prefix}_normal_1k.png')
    save(pad(mr(labels), cov), T/f'{prefix}_metal_rough_1k.png')
    Image.fromarray(labels).save(T/f'{prefix}_material_classes.png')
R.write_mask([mask], T/'m520_region_mask.png', size=N)
R.write_mask([np.zeros_like(mask)], T/'m520_head_region_mask.png', size=N)
config = {'variants':list(palettes), 'materials':[{'base':name, 'prefix':name.removesuffix('_A'), 'mask':maskfile,
          'regions':['native_trim'], 'ramps':ramps, 'palettes':dict(zip(palettes, [521, 522, 523]))}
          for name, maskfile in [('Cyclops_A', 'm520_region_mask.png'), ('CyclopsHead_A', 'm520_head_region_mask.png')]]}
(T/'m520_ramps.json').write_text(json.dumps(config, indent=2))
report = {'head_skin_gain':gain.tolist(), 'eye_centre':eye_centre.tolist(), 'palette_indices':order.tolist(),
          'seam_mae_before':float(abs(bcol-hcol).mean()*255), 'seam_mae_after':float(abs(bcol-sample(head, 'head')).mean()*255),
          'trim_texels':int(trim.sum()), 'body_classes':{str(i):int((classes == i).sum()) for i in np.unique(classes)},
          'specular_channel':'MR.R; openyamm_specular_mask'}
(T/'composition_report.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report))
