#!/usr/bin/env python3
"""Final A/B/C texture sets for the goblin from the Meshy retexture (retexture_v1).

- Gold spikes, ear hoops and claw tips, procedural scimitar (steel blade, gold guard, leather grip).
- Armor plates metallic, leather/skin roughness classes, baked AO, island padding.
- B/C tiers: skin recoloured through affine fits of the original palettes 745 -> 746 (blue) / 747 (red).
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
PAL = ROOT.parents[2] / 'assets_dev/worlds/mm6/textures'
SRC = ROOT / 'meshy/retexture_v3/texture_urls_0'
OUT = ROOT / 'textures'
SIZE = C.SIZE
GOLD = np.array([0.80, 0.60, 0.26])


def palette(pid):
    raw = (PAL / f'pal{pid}.act').read_bytes()
    return np.array([tuple(raw[i * 3:i * 3 + 3]) for i in range(256)], dtype=np.float32) / 255.0


def fit_palette(target, select):
    src = palette(745); dst = palette(target)
    h, s, _ = C.hsv(src[None])
    keep = (np.abs(src - dst).sum(1) > 0.02) & select(h[0], s[0])
    M, *_ = np.linalg.lstsq(np.c_[src[keep], np.ones(keep.sum())], dst[keep], rcond=None)
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
    metal = np.zeros_like(rough)
    x, y, z = xyz[..., 0], xyz[..., 1], xyz[..., 2]
    body = part_map == P['Body']; armor = part_map == P['Armor']; leather = part_map == P['Leather']
    spikes = part_map == P['Spikes']; hoops = part_map == P['Hoops']; teeth = part_map == P['Teeth']
    sword = part_map == P['Sword']
    fixed = base.copy()
    lum = base.mean(-1, keepdims=True)
    # gold hardware: keep Meshy's shading, replace its washed-out colour
    shade = np.clip(lum / np.median(lum[spikes | hoops]), 0.6, 1.3) if (spikes | hoops).any() else 1.0
    gold = np.clip(GOLD * shade, 0, 1)
    for m in (spikes, hoops):
        fixed[m] = gold[m]; rough[m] = 0.32; metal[m] = 1.0; normal[m] = (0.5, 0.5, 1.0)
    # claws: hand/foot tips far from the limb root, painted gold-horn (bone-like, not metallic)
    h, s, v = C.hsv(base)
    # hand claws: only the last ~2 cm of each finger (fingertips from refit_hands.py), blended into the skin;
    # the rest of the finger keeps the forearm skin tone (Meshy painted whole fingers yellowish)
    tips = np.array([f['tip'] for side in json.load(open(ROOT / 'work/hand_fit.json')).values() for f in side.values()])
    tip_d = np.full(x.shape, 9.0, dtype=np.float32)
    for t in tips:
        tip_d = np.minimum(tip_d, np.linalg.norm(xyz - t.astype(np.float32), axis=-1))
    hand = body & (np.abs(x) > 0.40) & (z < 0.95)
    claw_w = np.clip((0.030 - tip_d) / 0.010, 0, 1) * hand
    arm_skin = body & (np.abs(x) > 0.30) & (np.abs(x) < 0.40) & (z > 0.95) & (s > 0.2)
    arm_med = np.median(base[arm_skin], axis=0); arm_lum = np.median(lum[arm_skin])
    yellowish = hand & (claw_w < 1) & (h > 30) & (h < 70) & (v > 0.5)
    fixed[yellowish] = np.clip(arm_med * np.clip(lum[yellowish] / arm_lum, 0.6, 1.25), 0, 1)
    horn = np.clip(np.array([0.80, 0.66, 0.38]) * np.clip(lum / max(arm_lum, 1e-3), 0.7, 1.25), 0, 1)
    fixed = fixed * (1 - claw_w[..., None]) + horn * claw_w[..., None]
    rough = np.where(claw_w > 0.5, 0.35, rough)
    claw = (claw_w > 0.5) | (body & (z < 0.05) & (y < -0.15) & (v > 0.45) & (s < 0.55) & (h < 60))
    foot_claw = claw & (z < 0.05)
    fixed[foot_claw] = np.clip(np.array([0.78, 0.62, 0.32]) * shade[foot_claw] if np.ndim(shade) else np.array([0.78, 0.62, 0.32]), 0, 1)
    rough[foot_claw] = 0.35
    # feet: Meshy painted the bare feet like dark boots; recolour to the leg skin tone, keep shading
    leg_skin = body & (z > 0.45) & (z < 0.62) & (s > 0.25)
    skin_med = np.median(base[leg_skin], axis=0)
    lum_med = np.median(lum[leg_skin])
    feet = body & (z < 0.13) & ~claw
    fixed[feet] = np.clip(skin_med * np.clip(lum[feet] / lum_med, 0.55, 1.2), 0, 1)
    # sword
    along = ((xyz - data['grip']) * data['blade']).sum(-1)
    grip_m = sword & (along < 0.056)
    guard_m = sword & (along >= 0.056) & (along < 0.074)
    blade_m = sword & (along >= 0.074)
    pommel = sword & (along < -0.05)
    fixed[grip_m] = (0.24, 0.14, 0.08); rough[grip_m] = 0.7
    fixed[guard_m | pommel] = GOLD; rough[guard_m | pommel] = 0.3; metal[guard_m | pommel] = 1.0
    edge_t = np.clip((along - 0.074) / 0.62, 0, 1)
    fixed[blade_m] = (np.array([0.70, 0.70, 0.72]) * (0.92 + 0.08 * np.sin(edge_t * 40))[..., None])[blade_m]
    rough[blade_m] = 0.25; metal[blade_m] = 1.0
    normal[sword] = (0.5, 0.5, 1.0)
    # armor: grey plates metallic, brass studs gold; leather and skin dielectric
    ah, as_, av = C.hsv(fixed)
    plate = armor & (as_ < 0.20)
    local = ndimage.median_filter(av, size=15)
    stud = armor & (ah > 30) & (ah < 60) & (as_ > 0.45) & (av > local + 0.12)
    metal[plate] = 0.5; rough[plate] = 0.58
    fixed[stud] = np.clip(GOLD * (av[stud, None] / 0.7), 0, 1); metal[stud] = 1.0; rough[stud] = 0.3
    rough[leather & ~stud] = 0.62
    skin = body & ~claw
    rough[skin] = 0.62
    rough[teeth] = 0.5
    # Colour grade toward the native MM6 goblin (sprite medians: skin H65 S0.64, leather H25 S0.69, neutral iron):
    # saturation scaled around luminance, then channel gains (demon material touch-up approach).
    def grade(mask, saturation, gains):
        if not mask.any():
            return
        rgb = fixed[mask]
        lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
        rgb = np.maximum(lum[:, None] + (rgb - lum[:, None]) * saturation, 0) * np.array(gains)
        fixed[mask] = np.clip(rgb, 0, 1)

    skin_grade = body & ~claw
    grade(skin_grade, 1.35, (0.86, 0.98, 0.85))
    grade(leather & ~stud, 1.25, (0.85, 0.85, 0.85))
    grade(plate, 0.40, (0.86, 0.86, 0.88))
    # Form contrast: in game the graded skin read as flat as the grass behind it (p90/p10 luminance 2.1 vs the
    # demon's 3.1). Boost the large-scale shading Meshy painted (muscles, creases) on skin and leather, measured
    # within each material so seams/other parts do not bleed in.
    def local_contrast(mask, amount, sigma=10.0):
        if not mask.any():
            return
        lum = fixed @ np.array([0.2126, 0.7152, 0.0722])
        w = mask.astype(np.float32)
        blur = ndimage.gaussian_filter(lum * w, sigma) / np.maximum(ndimage.gaussian_filter(w, sigma), 1e-4)
        gain = np.clip((blur + (lum - blur) * amount) / np.maximum(lum, 1e-4), 0.55, 1.6)
        fixed[mask] = np.clip(fixed[mask] * gain[mask][:, None], 0, 1)

    local_contrast(skin_grade, 1.8)
    local_contrast(leather & ~stud, 1.5)
    rough[skin_grade] = 0.58
    rough[leather & ~stud] = 0.70
    # AO
    ao = np.asarray(Image.open(ROOT / 'work/ao.png').convert('L'), dtype=np.float32) / 255.0
    ao = pad(np.repeat(ao[..., None], 3, -1))[..., 0]
    ao_k = np.where(skin, 0.75, 0.75)
    ao_k = np.where(sword | hoops, 0.0, ao_k)
    fixed = fixed * (1 - ao_k[..., None] * (1 - np.clip(ao, 0, 1) ** 0.8)[..., None])
    fixed = pad(fixed)

    def save(arr, name, mode='RGB'):
        Image.fromarray(np.clip(arr * 255 + 0.5, 0, 255).astype(np.uint8), mode).save(OUT / name, optimize=True)

    save(fixed, 'gob_a_basecolor.png')
    save(normal, 'gob_normal.png')
    save(np.stack([np.ones_like(rough), rough, metal], -1), 'gob_metal_rough.png')
    for name in ('gob_normal', 'gob_metal_rough'):
        Image.open(OUT / f'{name}.png').resize((1024, 1024), Image.LANCZOS).save(OUT / f'{name}_1k.png', optimize=True)
    # tiers recolour only the green-olive skin
    fh, fs, fv = C.hsv(fixed)
    w = ((skin | (armor & ~plate & (fh > 40) & (fh < 120))) * np.clip((fs - 0.06) / 0.12, 0, 1) * ((fh > 30) & (fh < 130)))[..., None]
    skin_sel = lambda hh, ss: (hh > 35) & (hh < 120) & (ss > 0.15)
    for tier, pid in (('b', 746), ('c', 747)):
        M = fit_palette(pid, skin_sel)
        mapped = np.clip(np.c_[fixed.reshape(-1, 3), np.ones(SIZE * SIZE)] @ M, 0, 1).reshape(SIZE, SIZE, 3)
        save(fixed * (1 - w) + mapped * w, f'gob_{tier}_basecolor.png')
    print(json.dumps({'claw_texels': int(claw.sum()), 'plate_texels': int(plate.sum()), 'stud_texels': int(stud.sum())}))


if __name__ == '__main__':
    main()
