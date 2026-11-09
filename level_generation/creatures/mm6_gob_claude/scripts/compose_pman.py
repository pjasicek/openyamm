#!/usr/bin/env python3
"""Final A/B/C texture sets for the male peasant from the Meshy retexture (retexture_v1).

Reuses compose_textures_v2 helpers: island padding, inpainting, painted eyes, soft lip shading, knife,
roughness classes + baked AO, and the B/C tunic recolour through palette fits 798 -> 799 / 800.
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_textures_v2 as C

ROOT = Path(__file__).resolve().parents[1]
PAL = ROOT.parent / 'new_sorpigal_3d_stage1_20261006/pman/source/palettes'
SRC = ROOT / 'meshy/retexture_v1/texture_urls_0'
OUT = ROOT / 'textures'
SIZE = C.SIZE


def palette(pid):
    raw = (PAL / f'pal{pid}.act').read_bytes()
    return np.array([tuple(raw[i * 3:i * 3 + 3]) for i in range(256)], dtype=np.float32) / 255.0


def fit_palette(target):
    src = palette(798); dst = palette(target)
    differ = np.abs(src - dst).sum(1) > 0.02
    M, *_ = np.linalg.lstsq(np.c_[src[differ], np.ones(differ.sum())], dst[differ], rcond=None)
    return M


def main():
    OUT.mkdir(exist_ok=True)
    data = np.load(ROOT / 'work/uv3d.npz')
    parts = [str(p) for p in data['parts']]
    P = {n: i for i, n in enumerate(parts)}
    part_map, xyz = C.rasterise(data)
    strict, _ = C.rasterise(data, tol=0.0)
    interior = ndimage.binary_erosion(strict >= 0, iterations=2)
    _, (iy, ix) = ndimage.distance_transform_edt(~interior, return_indices=True)

    def pad(arr):
        out = arr[iy, ix]; out[interior] = arr[interior]; return out

    base = pad(C.load(str(SRC) + '_base_color.png'))
    normal = pad(C.load(str(SRC) + '_normal.png'))
    rough = pad(C.load(str(SRC) + '_roughness.png', 'L'))
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    body = part_map == P['Body']; hair = part_map == P['Hair']; tunic = part_map == P['Tunic']
    legs = part_map == P['Legs']; belt = part_map == P['Belt']; buckle = part_map == P['Buckle']
    knife = part_map == P['Knife']
    h, s, v = C.hsv(base)
    fixed = base.copy()
    # hair: skin-coloured texels (projection spill at the hairline) take neighbouring hair colour
    skin_like = (h > 8) & (h < 38) & (s > 0.18) & (s < 0.55) & (v > 0.62)
    bad_hair = ndimage.binary_dilation(hair & skin_like, iterations=2) & hair
    fixed = C.inpaint(fixed, bad_hair, hair, keep_detail=False)
    # V-neck: tunic-green/dark texels on the chest skin inside the neck opening
    neck_skin = body & (z > 1.22) & (z < 1.36) & (y < 0.0)
    green = (h > 65) & (h < 180) & (s > 0.15)
    bad_neck = ndimage.binary_dilation(neck_skin & (green | (v < 0.35)), iterations=2) & neck_skin
    fixed = C.inpaint(fixed, bad_neck, neck_skin, keep_detail=False)
    # tunic: skin-coloured and near-black projection patches (collar, shoulders) take neighbouring cloth
    th, ts, tv = C.hsv(fixed)
    tunic_med = np.median(tv[tunic])
    bad_tunic = tunic & ((((th > 8) & (th < 45) & (ts > 0.15) & (tv > 0.45))) | (tv < tunic_med * 0.55))
    bad_tunic = ndimage.binary_dilation(bad_tunic, iterations=3) & tunic
    fixed = C.inpaint(fixed, bad_tunic, tunic, keep_detail=False)
    normal[bad_tunic] = (0.5, 0.5, 1.0)
    # eyes: inpaint Meshy's painted eyes, paint clean ones centred on the sockets (same as the female)
    eyes = json.loads(str(data['eyes'])) if 'eyes' in data.files else {}
    for eye in eyes.values():
        cx, cy, cz = eye['centre']
        sgn = 1.0 if cx > -0.0075 else -1.0
        du = (x - cx) * sgn; dv = z - cz
        front = body & (y < cy + 0.02)
        erase = front & ((du / 0.020) ** 2 + (dv / 0.013) ** 2 < 1.0)
        ring = front & ~erase & ((du / 0.030) ** 2 + (dv / 0.020) ** 2 < 1.0)
        fixed = C.inpaint(fixed, erase, erase | ring, keep_detail=False)
        lid = erase & ~((du / 0.0125) ** 2 + (dv / 0.0055) ** 2 < 1.0)
        shade = np.clip(1 - ((du / 0.020) ** 2 + (dv / 0.013) ** 2), 0, 1)[..., None]
        fixed = np.where(lid[..., None], fixed * (1 - 0.12 * shade), fixed)
        a_w = 0.0115
        dv_t = dv - 0.06 * du
        t = np.clip(1 - (du / a_w) ** 2, 0, 1)
        up = 0.0042 * t ** 0.75; lo = -0.0030 * t ** 0.95
        inside = front & (np.abs(du) < a_w) & (dv_t < up) & (dv_t > lo)
        r = np.hypot(du + 0.0006, dv - 0.0003)
        col = np.where((r < 0.0016)[..., None], [0.04, 0.04, 0.04],
              np.where((r < 0.0045)[..., None], np.array([0.33, 0.26, 0.18]) * (0.7 + 0.3 * (r / 0.0045))[..., None],
              np.where((r < 0.0050)[..., None], [0.18, 0.14, 0.10], [0.80, 0.76, 0.72])))
        col = col * (1 - 0.35 * np.clip((dv_t - (up - 0.0022)) / 0.0022, 0, 1)[..., None])
        edge = np.clip(np.minimum(up - dv_t, dv_t - lo) / 0.0005, 0, 1)[..., None]
        fixed = np.where(inside[..., None], fixed * (1 - edge) + col * edge, fixed)
        lash = front & (np.abs(du) < a_w * 1.08) & (np.abs(dv_t - up - 0.0004) < 0.0007 + 0.0003 * t)
        fixed = np.where(lash[..., None], fixed * 0.3 + np.array([0.12, 0.07, 0.05]) * 0.7, fixed)
        rough[inside] = 0.25
    # lips: soft shading along the lip line and corners
    mx = x + 0.0075
    mouth = body & (np.abs(mx) < 0.024) & (y < -0.06) & (np.abs(z - 1.418) < 0.012)
    seam_z = 1.4175 + 0.003 * (mx / 0.020) ** 2
    fall = np.exp(-((z - seam_z) / 0.0011) ** 2) * np.clip(1 - (np.abs(mx) / 0.022) ** 4, 0, 1)
    corner = np.exp(-((np.abs(mx) - 0.019) / 0.0025) ** 2 - ((z - seam_z) / 0.002) ** 2)
    fixed = np.where(mouth[..., None], fixed * (1 - (0.18 * fall + 0.15 * corner)[..., None]), fixed)
    # knife
    rough_out = rough.copy(); metal_out = np.zeros_like(rough)
    along = ((xyz - data['grip']) * data['blade']).sum(-1)
    for mask, rgb, rr, mm in ((knife & (along < 0.049), (0.28, 0.17, 0.10), 0.75, 0.0),
                              (knife & (along >= 0.049) & (along < 0.061), (0.30, 0.30, 0.32), 0.45, 0.85),
                              (knife & (along >= 0.061), (0.70, 0.71, 0.73), 0.28, 1.0)):
        fixed[mask] = rgb; rough_out[mask] = rr; metal_out[mask] = mm; normal[mask] = (0.5, 0.5, 1.0)
    # roughness classes, metallic buckle, AO
    hh, ss, vv = C.hsv(fixed)
    skin_c = (hh > 5) & (hh < 40) & (ss > 0.18) & (ss < 0.65) & (vv > 0.45)
    leather = belt | (legs & (z < 0.14)) | (body & (hh > 10) & (hh < 40) & (ss > 0.5) & (vv < 0.55))
    rough_out = np.where(body & skin_c, 0.52, rough_out)
    rough_out = np.where(tunic, 0.86, rough_out)
    rough_out = np.where(legs & (z >= 0.14), 0.93, rough_out)
    rough_out = np.where(leather, 0.55, rough_out)
    rough_out = np.where(hair, 0.58, rough_out)
    rough_out[buckle] = 0.32; metal_out[buckle] = 0.9
    ao = np.asarray(Image.open(ROOT / 'work/ao.png').convert('L'), dtype=np.float32) / 255.0
    ao = pad(np.repeat(ao[..., None], 3, -1))[..., 0]
    ao_k = np.where(body & skin_c, 0.45, 0.55)
    ao_k = np.where(knife | buckle, 0.0, ao_k)
    fixed = fixed * (1 - ao_k[..., None] * (1 - np.clip(ao, 0, 1) ** 0.8)[..., None])
    fixed = pad(fixed)

    def save(arr, name):
        Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8)).save(OUT / name, optimize=True)

    save(fixed, 'pman_a_basecolor.png')
    save(normal, 'pman_normal.png')
    save(np.stack([np.ones_like(rough_out), rough_out, metal_out], -1), 'pman_metal_rough.png')
    for name, size in (('pman_normal', 1024), ('pman_metal_rough', 1024)):
        Image.open(OUT / f'{name}.png').resize((size, size), Image.LANCZOS).save(OUT / f'{name}_1k.png', optimize=True)
    # B/C: only the tunic changes between the native palettes
    w = (tunic * np.clip((C.hsv(fixed)[1] - 0.08) / 0.12, 0, 1))[..., None]
    for skin, pid in (('b', 799), ('c', 800)):
        M = fit_palette(pid)
        mapped = np.clip(np.c_[fixed.reshape(-1, 3), np.ones(SIZE * SIZE)] @ M, 0, 1).reshape(SIZE, SIZE, 3)
        save(fixed * (1 - w) + mapped * w, f'pman_{skin}_basecolor.png')
    print(json.dumps({'hair_fixed': int(bad_hair.sum()), 'neck_fixed': int(bad_neck.sum()), 'tunic_fixed': int(bad_tunic.sum())}))


if __name__ == '__main__':
    main()
