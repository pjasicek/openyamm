#!/usr/bin/env python3
"""Silhouette and proportion gate of the posed model against the native standing frames.

Inputs: front/side dumps from dump_posed.py (Standing frame 0, the axe joined as piece 1000). The posed mesh is
projected orthographically onto the native x2 canvas at the native scale (H = sole to skull top = the native H px,
soles on the native sole row; front centred on the pelvis, side on the chest), triangles filled with PIL.
Model landmarks: skull top = highest head-skin vertex (horns and crown cards excluded), chin = lowest head-skin
vertex, acromion = highest arm-skin vertex (the deltoid top), crotch = first row below the waist where the body
column under the pelvis is empty (as on the native: legs separate below the kilt), fist bottom = lowest left-hand
vertex. Widths are measured at the native landmark rows: full silhouette (shoulders), body without arms (chest, waist,
kilt, legs), arm silhouette (upper arm, forearm band), head skin (head width); side: torso depth at the armpit row,
head-skin length. IoU: the whole silhouette with the axe against the native alpha (> 100).
Writes review/model_proportions.json, review/shots/front_vs_native.png, review/shots/side_vs_native.png.
Args: <front npz> <side npz> [tag]"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

P = Path(__file__).resolve().parents[1]
X2 = P.parent / 'mm7_m286/aligned_2x'


def raster(shape, pts, tris):
    im = Image.new('L', (shape[1], shape[0]), 0)
    d = ImageDraw.Draw(im)
    for t in tris:
        d.polygon([tuple(pts[i]) for i in t], fill=255)
    return np.array(im) > 0


def runs(mask, y):
    row = np.r_[0, mask[int(round(y))].astype(int), 0]
    xs = np.flatnonzero(np.diff(row))
    return [(int(a), int(b) - 1) for a, b in zip(xs[::2], xs[1::2])]


def central(mask, y, cx):
    for a, b in runs(mask, y):
        if a - 1 <= cx <= b + 1:
            return b - a + 1
    return float('nan')


def font(size):
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def horns(d):
    """The fused horns of the v2 body shell (rest rule of weights_fix.py): skin above the skull's sides."""
    r, g = d['rest'], d['garment']
    sk = (g == 0) & (d['piece'] < 1000)
    skull = r[sk & (np.abs(r[:, 0]) < 0.04), 2].max()
    return sk & ((((r[:, 2] > skull - 0.10) & (np.abs(r[:, 0]) > 0.125)) | (r[:, 2] > skull + 0.025)))


def project(d, nat, view):
    rows = nat['landmark_rows_px']
    co, tris, piece, garment, cls = d['co'], d['tris'], d['piece'], d['garment'], d['cls']
    body = piece < 1000
    headskin = (cls == 2) & (garment == 0) & body & ~horns(d)
    sole_z = co[body, 2].min()
    skull_z = co[headskin, 2].max()
    Hm = skull_z - sole_z
    s = nat['H_px'] / Hm
    jn = list(d['joint_names'])
    pel = d['joint_co'][jn.index('B_Pelvis')]
    if view == 'front':
        u = co[:, 0]
        u0 = pel[0]
        ncx = 257.5
    else:
        u = -co[:, 1]                                                  # faces image right (native sa2)
        arm_z = sole_z + nat['landmark_heights_over_H']['armpit'] * Hm
        sel = body & (cls == 0) & (garment == 0) & (np.abs(co[:, 2] - arm_z) < 0.02 * Hm)
        u0 = (u[sel].max() + u[sel].min()) / 2
        ncx = 258.0
    pts = np.stack([(u - u0) * s + ncx, rows['sole'] - (co[:, 2] - sole_z) * s], 1)
    return pts, s, Hm, sole_z, skull_z


def masks(d, pts, shape):
    tris, piece, garment, cls = d['tris'], d['piece'], d['garment'], d['cls']
    tb = (piece[tris] < 1000).all(1)
    tarm = ((cls[tris] == 1) | np.isin(garment[tris], [5, 8])).any(1) & tb
    hn = horns(d)
    thead = ((cls[tris] == 2) & (garment[tris] == 0) & ~hn[tris]).all(1) & tb
    tskin = (garment[tris] == 0).all(1) & tb & ~tarm
    tarm_ns = tarm & ~(garment[tris] == 8).any(1)                     # arms without the band spikes
    return {'all': raster(shape, pts, tris), 'body': raster(shape, pts, tris[tb]), 'skin': raster(shape, pts, tris[tskin]),
            'arms_nospike': raster(shape, pts, tris[tarm_ns]),
            'torso': raster(shape, pts, tris[tb & ~tarm]), 'arms': raster(shape, pts, tris[tarm]),
            'head': raster(shape, pts, tris[thead])}


def panel(native_png, M, lines, title, iou):
    nim = Image.open(native_png).convert('RGBA')
    W, Hh = nim.size
    bg = Image.new('RGBA', (W, Hh), (95, 95, 95, 255))
    a = bg.copy(); a.alpha_composite(nim)
    sil = np.zeros((Hh, W, 3), np.uint8) + 95
    sil[M['all']] = (200, 200, 200)
    sil[M['arms']] = (170, 185, 215)
    sil[M['all'] & ~M['body']] = (215, 190, 120)
    b = Image.fromarray(sil)
    na = np.array(nim)[..., 3] > 100
    ov = np.zeros((Hh, W, 3), np.uint8) + 40
    ov[na & ~M['all']] = (230, 50, 50)
    ov[M['all'] & ~na] = (40, 200, 230)
    ov[na & M['all']] = (235, 235, 235)
    c = Image.fromarray(ov)
    out = Image.new('RGB', (W * 3, Hh + 40), (30, 30, 30))
    out.paste(a.convert('RGB'), (0, 40)); out.paste(b, (W, 40)); out.paste(c, (2 * W, 40))
    dr = ImageDraw.Draw(out)
    f = font(16)
    dr.text((8, 8), 'native x2', fill=(255, 255, 255), font=f)
    dr.text((W + 8, 8), 'model (Standing f0)', fill=(255, 255, 255), font=f)
    dr.text((2 * W + 8, 8), f'overlay IoU {iou:.3f}  red native only / cyan model only', fill=(255, 255, 255),
            font=font(13))
    for y, colour in lines:
        for k in range(3):
            dr.line([(k * W, y + 40), (k * W + W, y + 40)], fill=colour, width=1)
    dr.text((8, Hh + 18), title, fill=(255, 220, 0), font=font(13))
    return out


def main():
    nat = json.loads((P / 'review/native_proportions.json').read_text())
    G = nat['gate_ratios']
    rows = nat['landmark_rows_px']
    tag = sys.argv[3] if len(sys.argv) > 3 else 'final'
    res = {'tag': tag, 'pose': 'Standing frame 0 (axe in hand)', 'ratios': {}}
    for view, path in (('front', sys.argv[1]), ('side', sys.argv[2])):
        d = np.load(path)
        native_png = X2 / ('m286sa0.png' if view == 'front' else 'm286sa2.png')
        shape = np.array(Image.open(native_png)).shape[:2]
        pts, s, Hm, sole_z, skull_z = project(d, nat, view)
        M = masks(d, pts, shape)
        na = np.array(Image.open(native_png))[..., 3] > 100
        iou = float((na & M['all']).sum() / (na | M['all']).sum())
        iou_body = float((na & M['body']).sum() / (na | M['body']).sum())
        res[f'{view}_iou'] = round(iou, 3)
        res[f'{view}_iou_without_axe'] = round(iou_body, 3)
        co, cls, garment, piece = d['co'], d['cls'], d['garment'], d['piece']
        H = nat['H_px']
        row = lambda z: rows['sole'] - (z - sole_z) * s
        got = {}
        headskin = (cls == 2) & (garment == 0) & (piece < 1000) & ~horns(d)
        armskin = (cls == 1) & (garment == 0) & (piece < 1000)
        lm = {'skull_top': row(skull_z), 'chin': row(co[headskin, 2].min()), 'acromion': row(co[armskin, 2].max())}
        if True:
            lm['horn_tip'] = row(co[piece < 1000, 2].max())
        got['head_height'] = (lm['chin'] - lm['skull_top']) / H
        got['skull_top_to_acromion'] = (lm['acromion'] - lm['skull_top']) / H
        got['horn_rise'] = (lm['skull_top'] - lm['horn_tip']) / H
        if view == 'front':
            jn = list(d['joint_names'])
            cx = (d['joint_co'][jn.index('B_Pelvis')][0] - d['joint_co'][jn.index('B_Pelvis')][0]) * s + 257.5
            got['shoulder_width'] = (runs(M['body'], rows['deltoid'])[-1][1] - runs(M['body'], rows['deltoid'])[0][0] + 1) / H
            got['chest_width'] = central(M['torso'], rows['armpit'], cx) / H
            got['waist_width'] = central(M['torso'], rows['waist'], cx) / H
            got['kilt_hip_width'] = central(M['torso'], rows['kilt_hip'], cx) / H
            crotch = next(y for y in range(rows['waist'], rows['sole']) if not M['torso'][y, int(round(cx))])
            lm['crotch'] = crotch
            got['leg_crotch_height'] = (rows['sole'] - crotch) / H
            legs = [r for r in runs(M['torso'], rows['thigh']) if r[1] - r[0] > 4]
            got['leg_outer_span_thigh'] = (legs[-1][1] - legs[0][0] + 1) / H
            got['thigh_width_single'] = float(np.mean([b - a + 1 for a, b in (legs[0], legs[-1])] if len(legs) > 1
                                                      else [(legs[0][1] - legs[0][0] + 1) / 2])) / H
            shins = [r for r in runs(M['torso'], rows['shin']) if r[1] - r[0] > 2]
            got['shin_width_single'] = float(np.mean([b - a + 1 for a, b in (shins[0], shins[-1])])) / H
            # arms: the creature's left arm (image right, +x), as measured on the native
            ar = runs(M['arms'], 270)
            got['upper_arm_width'] = (ar[-1][1] - ar[-1][0] + 1) / H
            ar = runs(M['arms_nospike'], 310)                        # the native band was measured without spikes
            got['forearm_band_width'] = (ar[-1][1] - ar[-1][0] + 1) / H
            left = (cls == 1) & (co[:, 0] > 0) & (piece < 1000)
            lm['fist_bottom'] = row(co[left, 2].min())
            got['arm_acromion_to_fist_bottom'] = (lm['fist_bottom'] - lm['acromion']) / H
            # the narrowest silhouette width of the face between the eye row and the chin (native: 57 px at row 184,
            # below the ears)
            got['head_width_no_ears'] = min(central(M['body'], y, cx) for y in range(int(lm['skull_top'] + 0.09 * H),
                                                                                   int(lm['chin']) - 5)) / H
        else:
            # skin only (the native depth runs to the back skin under the mane)
            got['chest_depth_side'] = central(M['skin'], rows['armpit'], 258.0) / H
            # eye centre (eye pieces P10/P11) to the snout tip (the most forward head skin below the eyes); the native
            # occiput is hidden by the mane, so the head length itself is not gated
            ey = co[np.isin(piece, [10, 11])].mean(0)
            band = headskin & (co[:, 2] < ey[2] + 0.01 * Hm)
            got['eye_to_snout_side'] = (ey[1] - co[band, 1].min()) * s / H
        for k, v in got.items():
            if k in G and np.isfinite(v) and (view == 'front' or k not in res['ratios']):
                res['ratios'][k] = {
                    'native': G[k], 'model': round(float(v), 4), 'dev_pct': round(100 * (v / G[k] - 1), 1)}
        res[f'{view}_landmarks_px'] = {k: round(float(v), 1) for k, v in lm.items()}
        lines = [(rows[k], (255, 80, 80)) for k in ('skull_top', 'chin', 'acromion', 'crotch', 'sole') if k in rows]
        lines += [(lm[k], (60, 220, 255)) for k in ('skull_top', 'chin', 'acromion', 'crotch') if k in lm]
        title = f'{view}: red = native landmarks, cyan = model landmarks; IoU {iou:.3f} (without axe {iou_body:.3f})'
        (P / 'review/shots').mkdir(parents=True, exist_ok=True)
        panel(native_png, M, lines, title, iou).save(P / f'review/shots/{view}_vs_native.png')
    worst = max(abs(v['dev_pct']) for v in res['ratios'].values())
    res['worst_dev_pct'] = worst
    res['within_10pct'] = int(sum(abs(v['dev_pct']) <= 10 for v in res['ratios'].values()))
    res['count'] = len(res['ratios'])
    (P / 'review/model_proportions.json').write_text(json.dumps(res, indent=1) + '\n')
    for k, v in res['ratios'].items():
        flag = '' if abs(v['dev_pct']) <= 10 else '  <-- off'
        print(f"MODELGATE {k:28s} native {v['native']:.3f} model {v['model']:.3f} {v['dev_pct']:+6.1f} %{flag}")
    print('MODELGATE IoU front', res['front_iou'], 'side', res['side_iou'], 'within 10 %', res['within_10pct'], '/',
          res['count'])


if __name__ == '__main__':
    main()
