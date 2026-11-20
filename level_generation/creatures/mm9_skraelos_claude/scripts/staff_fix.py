#!/usr/bin/env python3
"""Staff clearance per clip (orchestrator pre-screen 2026-11-04: the staff ran 1.5-4.3 cm into the sleeve cuff / robe beside the grip in
Fidget, Talk, Running and Death). The staff rides on its own bone `FHP R Staff` (child of the right Hand at the grip, build_glb_sk.py); here
each listed clip gets a rotation channel on it, solved on the clip's 30 fps keys and low-passed, so the shaft turns in the fist the least
that keeps it out of the cloth:
- per key: the posed staff against the posed outer cloth (prop_gate.py's test: body-set vertices off the hands whose rest normal points away
  from the body axis, signed distance along the nearest outer vertex's normal); while a staff vertex is deeper than CLEAR behind the cloth
  (within 6 cm of it), turn the staff about the grip by the least angle that moves the deepest one out along the cloth normal (+MARGIN);
- the per-key turns (rotation vectors in the Hand's frame) are widened by a running maximum over WIDEN s and Gaussian-smoothed (SIGMA s),
  loops wrapped; one-shots eased in and out over EASE s (>= 0.3) unless the need reaches the clip's end; capped at CAP degrees.
Args: <in glb> <out glb> <clip,...>"""
import sys, os
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from scipy.ndimage import gaussian_filter1d, maximum_filter1d
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared' / 'floor'))
from glb_pose import Glb, Model, quaternion_matrix, matrix_quaternion
E = lambda k, d: float(os.environ.get(k, d))
IN, OUT, CLIPS = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
CLEAR, MARGIN, WIDEN, SIGMA, EASE, CAP = E('CLEAR', '0.003'), E('MARGIN', '0.006'), E('WIDEN', '0.2'), E('SIGMA', '0.1'), E('EASE', '0.3'), E('CAP', '25')
LOOPS = {'Running', 'Walking', 'Standing'}
g = Glb(IN); m = Model(g); doc = g.json; nn = [n.get('name') for n in doc['nodes']]; jn = [nn[j] for j in m.joints]
SN = nn.index('FHP R Staff'); HN = nn.index('FHP R Hand')
mesh = doc['meshes'][[n.get('mesh') for n in doc['nodes'] if 'mesh' in n][0]]
mats = [doc['materials'][p['material']]['name'] for p in mesh['primitives']]
body, head = m.primitives[mats.index('Skraelos')], m.primitives[mats.index('SkraelosHead')]
bi, hi = mats.index('Skraelos'), mats.index('SkraelosHead')
staff = (head['joints'][:, 0] == jn.index('FHP R Staff')) & (head['weights'][:, 0] > 0.99)
handj = [i for i, n in enumerate(jn) if any(k in n for k in ('Hand', 'Finger', 'Thumb', 'Index', 'Middle', 'Ring', 'Pinky', 'Staff'))]
P0, T0 = body['positions'], body['triangles']
fn = np.cross(P0[T0[:, 1]] - P0[T0[:, 0]], P0[T0[:, 2]] - P0[T0[:, 0]]); N0 = np.zeros_like(P0)
for c in range(3): np.add.at(N0, T0[:, c], fn)
N0 /= np.maximum(np.linalg.norm(N0, axis=1, keepdims=True), 1e-12)
radial = P0.copy(); radial[:, 1] = 0
outer = np.where(~np.isin(body['joints'][:, 0], handj) & (np.sum(N0 * radial, 1) > 0))[0]
def rotm(v):
    th = np.linalg.norm(v)
    if th < 1e-12: return np.eye(3)
    k = v / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + np.sin(th) * K + (1 - np.cos(th)) * K @ K
def logm(R):
    c = np.clip((np.trace(R) - 1) / 2, -1, 1); th = np.arccos(c)
    if th < 1e-9: return np.zeros(3)
    return th / (2 * np.sin(th)) * np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
for clip in CLIPS:
    ai = m.clips[clip]; times = np.array(m.clip_times(clip)); dur = times[-1]
    ts = np.arange(0, dur + 1e-6, 1 / 30.0)
    need = np.zeros((len(ts), 3)); worst0 = 0.0
    for k, t in enumerate(ts):
        w = m.world(m.sample(clip, t)); posed = m.skinned_positions(w)
        Pb = posed[bi][0]; Ps = posed[hi][0][staff]
        fnp = np.cross(Pb[T0[:, 1]] - Pb[T0[:, 0]], Pb[T0[:, 2]] - Pb[T0[:, 0]]); Nb = np.zeros_like(Pb)
        for c in range(3): np.add.at(Nb, T0[:, c], fnp)
        Nb /= np.maximum(np.linalg.norm(Nb, axis=1, keepdims=True), 1e-12)
        kd = cKDTree(Pb[outer]); gp = w[SN][:3, 3]; Rh = w[HN][:3, :3]; R = np.eye(3)
        def worst(Rm):
            q = (Ps - gp) @ Rm.T + gp; d, i = kd.query(q); s_ = np.sum((q - Pb[outer[i]]) * Nb[outer[i]], 1)
            s_ = np.where(d < 0.06, s_, 1.0); return float(-s_.min())
        w0 = worst(R)
        if w0 > CLEAR:
            worst0 = max(worst0, w0)
            u = Ps.mean(0) - gp; u = np.linalg.svd(Ps - Ps.mean(0))[2][0]; e1 = np.cross(u, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(u, e1)
            best = (w0, np.eye(3))
            for th in np.radians(np.arange(1, CAP + 0.5, 1.0)):
                for ph in np.linspace(0, 2 * np.pi, 16, endpoint=False):
                    Rm = rotm((np.cos(ph) * e1 + np.sin(ph) * e2) * th); ww = worst(Rm)
                    if ww < best[0]: best = (ww, Rm)
                if best[0] <= CLEAR - MARGIN * 0.5: break
            R = best[1]
        need[k] = logm(Rh.T @ R @ Rh)            # in the Hand's frame
    mag = np.linalg.norm(need, axis=1); mode = 'wrap' if clip in LOOPS else 'nearest'
    wide = int(round(WIDEN * 30)); idx = np.arange(len(ts))
    if wide > 0:
        mm = maximum_filter1d(mag, 2 * wide + 1, mode=mode)
        pick = np.array([max(range(max(0, k - wide), min(len(ts), k + wide + 1)), key=lambda j_: mag[j_]) for k in idx])
        wv = need[pick] * (mm / np.maximum(mag[pick], 1e-9))[:, None]
    else: wv = need
    sm = gaussian_filter1d(wv, SIGMA * 30, axis=0, mode=mode)
    ang = np.linalg.norm(sm, axis=1); cap = np.radians(CAP); sm *= np.minimum(1, cap / np.maximum(ang, 1e-9))[:, None]
    if clip not in LOOPS:
        e = int(round(EASE * 30)); f = np.ones(len(ts))
        if mag[:e].max() < 1e-6 or True:
            u = np.clip(ts / EASE, 0, 1); f *= u * u * (3 - 2 * u)
        if clip not in ('Death',):
            u = np.clip((dur - ts) / EASE, 0, 1); f *= u * u * (3 - 2 * u)
        sm *= f[:, None]
    Q = np.array([matrix_quaternion(rotm(v)) for v in sm], np.float32)
    for k in range(1, len(Q)):
        if np.dot(Q[k], Q[k - 1]) < 0: Q[k] = -Q[k]
    anim = doc['animations'][ai]
    anim['channels'] = [c for c in anim['channels'] if not (c['target']['node'] == SN and c['target']['path'] == 'rotation')]
    ia = g.append_accessor(ts.astype(np.float32).reshape(-1, 1), 'SCALAR'); oa = g.append_accessor(Q, 'VEC4')
    anim['samplers'].append({'input': ia, 'output': oa, 'interpolation': 'LINEAR'})
    anim['channels'].append({'sampler': len(anim['samplers']) - 1, 'target': {'node': SN, 'path': 'rotation'}})
    print('STAFF', clip, 'worst before %.1f cm' % (worst0 * 100), 'keys needing a turn', int((mag > 1e-6).sum()), 'of', len(ts),
          'max turn %.1f deg' % np.degrees(np.linalg.norm(sm, axis=1).max()))
g.write(OUT)
