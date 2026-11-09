#!/usr/bin/env python3
"""Final maps from the composed Meshy paints (project folder): AO gutters padded from the charts, gentle grade (claude_shared/
grade_basecolor.py: AO 0.45 body / 0.3 head, fine 1.0, local 0.25, contrast 1.03, saturation 0.95), hair and braid lifted x1.25
(Meshy matched MM9's near-black hair; the Codex masters are a shade browner), normal maps' green flipped (Meshy writes DirectX
Y-down: measured against the paint's relief, corr -0.41 body / -0.54 head before the flip), material class maps (1K: body 9 metal = steel
plates, mail, gold trim, greaves, medallion, buckle; 8 = sleeves, fur hem, leather, gloves; head 1 skin, 2 hair, 6 eyes) and ORM
(R AO, G Meshy roughness, B 0: material_classes_to_orm.py writes metallic from the class maps on the runtime GLB)."""
import subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
T = 'textures/'; G = '/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python'
D = np.load('work/uv_dump.npz'); uvc, mat = D['uvc'], D['mat']


def hsv(rgb):
    mx = rgb.max(-1); mn = rgb.min(-1); d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-6), 0)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / np.maximum(d, 1e-6)) % 6, np.where(mx == g, (b - r) / np.maximum(d, 1e-6) + 2, (r - g) / np.maximum(d, 1e-6) + 4)) * 60
    return h, s, mx


for s, M, aos in (('body', 0, 0.45), ('head', 1, 0.3)):
    ao = np.asarray(Image.open(T + f'kira_{s}_ao_raw.png').convert('L')); H, W = ao.shape
    cv = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(cv)
    for t in uvc[mat == M]: dr.polygon([(float(u * W), float((1 - v) * H)) for u, v in t], fill=255)
    cov = ndimage.binary_erosion(np.asarray(cv) > 0, iterations=1) & (ao > 0)
    idx = ndimage.distance_transform_edt(~cov, return_distances=False, return_indices=True)
    Image.fromarray(ao[idx[0], idx[1]]).save(T + f'kira_{s}_ao.png')
    src = T + (f'kira_{s}_fix.png' if s == 'head' else f'kira_{s}_raw.png')   # head: face_fix.py (chin/forehead/nostrils)
    if s == 'head':                                   # hair lift before the grade
        pm = np.asarray(Image.open('work/part_head.png').resize((2048, 2048), Image.NEAREST))
        rgb = np.asarray(Image.open(src).convert('RGB'), np.float32)
        hair = np.isin(pm, (21, 23))
        rgb[hair] = np.clip(rgb[hair] * 1.25, 0, 255)
        Image.fromarray(rgb.astype('u1')).save(T + 'kira_head_lift.png'); src = T + 'kira_head_lift.png'
    subprocess.run([G, '-W', 'ignore', '../claude_shared/grade_basecolor.py', '--ao', T + f'kira_{s}_ao.png', '--ao-strength', str(aos),
                    '--fine', '1.0', '--local', '0.25', '--contrast', '1.03', '--saturation', '0.95', src], check=True, capture_output=True)
    graded = src.replace('.png', '_graded.png')
    Image.open(graded).save(T + f'kira_{s}_final.png')
    n = np.array(Image.open(T + f'kira_{s}_normal_dx.png').convert('RGB')); n[..., 1] = 255 - n[..., 1]
    if s == 'head':      # face skin: Meshy's normal relief drew dark marks under the lip, on the chin and round the nostrils; flat there
        pm1 = np.asarray(Image.open('work/part_head.png'))
        fw = ndimage.gaussian_filter((np.isin(pm1, (20, 22))).astype(np.float32), 2.0)[..., None]
        n = (n * (1 - fw) + np.array([128, 128, 255]) * fw).astype(np.uint8)
    Image.fromarray(n).save(T + f'kira_{s}_normal.png')
    r = np.asarray(Image.open(T + f'kira_{s}_rough.png').convert('L'), np.float32) / 255
    a1 = np.asarray(Image.open(T + f'kira_{s}_ao.png').convert('L').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    orm = np.stack([a1, np.clip(r, 0.3, 1.0), np.zeros_like(r)], -1)
    Image.fromarray((orm * 255 + 0.5).astype('u1')).save(T + f'kira_{s}_orm.png')
    # material classes (1K, nearest)
    pm = np.asarray(Image.open(f'work/part_{s}.png'))
    rgb = np.asarray(Image.open(T + f'kira_{s}_raw.png').convert('RGB').resize((1024, 1024), Image.LANCZOS), np.float32) / 255
    h, sa, v = hsv(rgb)
    cls = np.zeros(pm.shape, np.uint8)
    if s == 'body':
        blue = rgb[..., 2] > rgb[..., 0] + 0.06
        leather = (h > 10) & (h < 42) & (sa > 0.45) & (v < 0.36)
        shiny = ((sa < 0.3) & (v > 0.38)) | ((h > 28) & (h < 58) & (sa > 0.3) & (v > 0.5))
        cls[:] = 8
        cls[np.isin(pm, (10, 11, 12, 13))] = 9
        cls[(pm == 1) & ~blue & ~leather] = 9
        cls[(pm == 7) & ~blue] = 9
        cls[np.isin(pm, (5, 9)) & shiny] = 9
        cls = ndimage.median_filter(cls, 3)
    else:
        cls[pm == 20] = 1; cls[np.isin(pm, (21, 23))] = 2; cls[pm == 22] = 6
    Image.fromarray(cls).save(T + f'kira_{s}_material_classes.png')
    print('FINISH', s, {int(k): round(float((cls == k).mean()), 3) for k in np.unique(cls)})
