"""Pass 2 tone (coordinator review 2026-10-31: MM9's demon is a deep red-black hide with heavy dark gunmetal; ours read bright
red with pale silver bracers and skirt). One shared set, a region mask and one grade per region; no tiers.
Region mask (textures/ldemon_region_mask.png, body set 2K): R hide (red paint), G dark armour (the gauntlets and greaves,
MM9's near-black bracers and boots: armour shells by bind position, rasterised from work/faces.npz), B steel (neutral grey
paint elsewhere: plates, skirt, collar, spikes). Grades: hide value curve compressed above KNEE (the orange highlight
speckles), saturation x HS, value x HV; steel value x SV, saturation x 0.5 (gunmetal); dark armour value x DV.
Usage: grade_regions.py [HV HS SV DV]   (project folder; reads *_basecolor_graded.png, writes *_basecolor_final.png)"""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
HV, HS, SV, DV = [float(x) for x in sys.argv[1:5]] if len(sys.argv) > 4 else (0.75, 0.8, 0.55, 0.38)
KNEE = 0.32
z = np.load('work/faces.npz'); co, uv, head, part = z['co'], z['uvb'], z['head'], z['part']
S = 2048
ctr = co.mean(1); ax = np.abs(ctr[:, 0])
gaunt = np.isin(part, (1, 2)) & (ax > 0.6) & (ax < 1.12) & (ctr[:, 2] > -0.2) & (ctr[:, 2] < 0.45)
greave = np.isin(part, (1, 2)) & (ax > 0.1) & (ax < 0.55) & (ctr[:, 2] > -1.32) & (ctr[:, 2] < -0.62)
# pass 2: the knee cops and the knee pits (greave tops, any part but the tail) were smudged grey-beige paint: same treatment
knee = (part != 4) & (ax > 0.1) & (ax < 0.55) & (ctr[:, 2] > -0.9) & (ctr[:, 2] < -0.52)
greave = greave | knee
dark = Image.new('L', (S, S), 0); d = ImageDraw.Draw(dark)
for f in np.nonzero((gaunt | greave) & (head == 0))[0]:
    d.polygon([(float(u * S), float((1 - v) * S)) for u, v in uv[f]], fill=255)
dark = np.asarray(dark.filter(ImageFilter.MaxFilter(5)), np.float32) / 255


def classify(a):
    mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    hue = np.degrees(np.arctan2(np.sqrt(3) * (g - b), 2 * r - g - b)) % 360
    hide = np.clip((sat - 0.35) / 0.15, 0, 1) * (((hue < 40) | (hue > 330)).astype(np.float32))
    steel = np.clip((0.2 - sat) / 0.08, 0, 1)
    return mx, sat, hide, steel


def grade(src, dst, body):
    a = np.asarray(Image.open(src).convert('RGB'), np.float32) / 255
    if a.shape[0] != S: raise SystemExit('size')
    mx, sat, hide, steel = classify(a)
    dk = dark * (1 - hide) if body else np.zeros_like(mx)
    steel = steel * (1 - dk) if body else steel * 0
    gray = a.mean(2, keepdims=True)
    # hide: value curve (compress the bright orange speckles), desaturate, darken
    v = mx; v2 = np.where(v > KNEE, KNEE + (v - KNEE) * 0.45, v) * HV
    h = (gray + (a - gray) * HS) * (v2 / np.maximum(v, 1e-4))[..., None]
    # steel: gunmetal
    st = (gray + (a - gray) * 0.5) * SV
    out = a * (1 - hide[..., None]) + h * hide[..., None]
    out = out * (1 - steel[..., None]) + st * steel[..., None]
    out = out * (1 - dk[..., None]) + (gray + (out - gray) * 0.5) * DV * dk[..., None]
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(dst)
    if body:
        m = np.stack([hide, dk, steel], -1)
        Image.fromarray((m * 255).astype(np.uint8)).resize((1024, 1024), Image.BILINEAR).save('textures/ldemon_region_mask.png')
    print('GRADED', dst, 'hide %.2f steel %.2f dark %.2f' % ((hide > 0.5).mean(), (steel > 0.5).mean(), (dk > 0.5).mean()))


grade('textures/ldemon_basecolor_graded.png', 'textures/ldemon_basecolor_final.png', True)
grade('textures/ldemon_head_basecolor_graded.png', 'textures/ldemon_head_basecolor_final.png', False)
