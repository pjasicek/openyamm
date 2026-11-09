#!/usr/bin/env python3
"""Retexture check, part 1: texture-drift summary of the picked step (work/drift_r55.npy, texture_drift.py) per
region (dominant bone of each face, work/r55_dominant_bone.npy; base = faces below 3 cm), UV validity and texel density
(base colour 2048) of source and reduced LOD0 meshes. Writes work/retex_regions.json."""
import json
import numpy as np
d = np.load('work/mesh_r55.npz'); s = np.load('work/mesh_in.npz')
drift = np.load('work/drift_r55.npy'); bone = np.load('work/r55_dominant_bone.npy')
v, f, uv = d['verts'], d['faces'], d['wuv'].reshape(-1, 3, 2)
tri = v[f]; cen = tri.mean(1)
area = np.linalg.norm(np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]), axis=1) / 2


def region(b, z):
    if z < .03:
        return 'base'
    if b.startswith(('JawFront', 'FrontTop')):
        return 'mouth_front'
    if b.startswith(('NeckL', 'JawL')):
        return 'mouth_left_stalk'
    if b.startswith(('NeckR', 'JawR')):
        return 'mouth_right_stalk'
    if b.startswith('EmbeddedEye'):
        return 'embedded_eyes'
    if b.startswith('Eye'):
        return 'eye_stalks'
    return 'lumps_body'


reg = np.array([region(b, z) for b, z in zip(bone, cen[:, 2])])
kept = d['group'] == -1
out = {'regions': {}}
for r in sorted(set(reg)):
    m = reg == r
    out['regions'][r] = {'faces': int(m.sum()), 'kept_exact': int((m & kept).sum()),
                         'drift_p50': round(float(np.median(drift[m])), 1),
                         'drift_p99': round(float(np.percentile(drift[m], 99)), 1),
                         'faces_over_40': int((m & (drift > 40)).sum()),
                         'area_over_40_cm2': round(float(area[m & (drift > 40)].sum() * 1e4), 2)}


def density(verts, faces, wuv):
    t = verts[faces]; a3 = np.linalg.norm(np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]), axis=1) / 2
    u = wuv.reshape(-1, 3, 2); au = np.abs(np.cross(u[:, 1] - u[:, 0], u[:, 2] - u[:, 0])) / 2
    return float(np.sqrt(au.sum() * 2048 ** 2 / a3.sum())), au, a3


ds, aus, _ = density(s['verts'], s['faces'], s['wuv']); dr, aur, _ = density(v, f, d['wuv'])
# UV coverage: every reduced face's UV centroid must fall on texels the source covers (512 raster)
N = 512; cov = np.zeros((N, N), bool)
su = s['wuv'].reshape(-1, 3, 2)
for t in su:
    lo = np.floor(t.min(0) * N).astype(int).clip(0, N - 1); hi = np.ceil(t.max(0) * N).astype(int).clip(0, N - 1)
    cov[lo[1]:hi[1] + 1, lo[0]:hi[0] + 1] = True  # bounding-box raster (conservative)
uc = uv.mean(1); ix = (uc * N).astype(int).clip(0, N - 1)
on = cov[ix[:, 1], ix[:, 0]]
flipped_src = int((np.cross(su[:, 1] - su[:, 0], su[:, 2] - su[:, 0]) < 0).sum())
flipped_red = int((np.cross(uv[:, 1] - uv[:, 0], uv[:, 2] - uv[:, 0]) < 0).sum())
out['uv'] = {'range_reduced': [np.round(uv.reshape(-1, 2).min(0), 4).tolist(), np.round(uv.reshape(-1, 2).max(0), 4).tolist()],
             'faces_off_source_charts': int((~on).sum()), 'uv_area_source': round(float(aus.sum()), 4),
             'uv_area_reduced': round(float(aur.sum()), 4), 'mirrored_faces_source': flipped_src,
             'mirrored_faces_reduced': flipped_red, 'zero_uv_area_reduced': int((aur < 1e-12).sum())}
out['texel_density_px_per_m'] = {'source': round(ds, 1), 'reduced': round(dr, 1)}
open('work/retex_regions.json', 'w').write(json.dumps(out, indent=1) + '\n'); print(json.dumps(out, indent=1))
