"""Fit the v2 rig to the native MM7 m182 frames by silhouette (system Python).

For each native frame (restored x2 `level_generation/creatures/mm7_m182/aligned_2x/<frame>.png`, five views: 0 front,
1 front three-quarter, 2 side, 3 back three-quarter, 4 back; the creature faces image-right in views 1-3, so the
camera orbits the dragon's right side) the model is posed with `dragon_pose.ops`, skinned in numpy, projected
orthographically at the shared camera elevation and scale, splatted to a 256 px mask (vertices, triangle centres and
edge midpoints, closed by 3x3) and compared with the native alpha mask after the best integer translation (FFT
correlation). Objective: 1 - mean soft IoU (both masks blurred by sigma 1 px) + a small pull toward a prior pose.

`calibrate`: camera elevation and scale on the standing frame sa (all views) together with its pose.
`fit <clip>`: every frame of a clip in native order, each started from the previous fitted pose.
Writes work/v2/fit/<clip>.json and review/motion_fit/<clip>_<frame>.png."""
import json, sys, time
import numpy as np
from pathlib import Path
from PIL import Image
from scipy import ndimage
from scipy.optimize import minimize
sys.path.insert(0, str(Path(__file__).resolve().parent))
import dragon_pose as DP

P = Path(__file__).resolve().parents[1]; NATIVE = P.parent / 'mm7_m182/aligned_2x'
FIT = P / 'work/v2/fit'; FIT.mkdir(parents=True, exist_ok=True); SHOTS = P / 'review/motion_fit'; SHOTS.mkdir(parents=True, exist_ok=True)
RES = 288

CLIPS = {
    'flight': [('sa', 0.), ('wa', .125), ('wb', .25), ('wc', .4375), ('wd', .625), ('we', .75), ('wf', .875)],
    'attack': [('sa', 0.), ('aa', .125), ('ab', .25), ('ac', .375), ('ad', .5), ('ae', .625), ('af', .75)],
    'hit': [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('nd', .5), ('ne', .625), ('nf', .75)],
    'death': [('sa', 0.), ('na', .125), ('nb', .25), ('nc', .375), ('da', .5), ('db', .625), ('dc', .8125), ('xa', .9375), ('dd', 1.125)],
}
DEATH_FRONT_ONLY = {'da', 'db', 'dc', 'xa', 'dd'}


def native_mask(frame):
    a = np.asarray(Image.open(NATIVE / f'm182{frame}.png').convert('RGBA'))[..., 3].astype(float) / 255
    h, w = a.shape; canvas = np.zeros((2 * RES, 2 * RES)); oy, ox = (2 * RES - h) // 2, (2 * RES - w) // 2
    canvas[oy:oy + h, ox:ox + w] = a
    return canvas.reshape(RES, 2, RES, 2).mean((1, 3)) > .5


class Model:
    def __init__(self):
        self.sk = DP.Skinner(P / 'work/v2/rig_v2.npz')
        t = self.sk.tris; self.tris = t
        e = np.r_[t[:, [0, 1]], t[:, [1, 2]], t[:, [2, 0]]]; self.edges = np.unique(np.sort(e, 1), axis=0)

    def points(self, p):
        v = self.sk.pose(p)
        return np.r_[v, v[self.tris].mean(1), v[self.edges].mean(1)], v


def camera(view, elev):
    th = np.radians(45. * view); d = np.array([-np.sin(th) * np.cos(elev), -np.cos(th) * np.cos(elev), np.sin(elev)])
    f = -d; r = np.cross(f, [0, 0, 1.]); r /= np.linalg.norm(r); u = np.cross(r, f); return r, u


def splat(pts, view, elev, scale):
    r, u = camera(view, elev); X = pts @ r * scale + RES / 2; Yy = -(pts @ u) * scale + RES * .75
    m = np.zeros((RES, RES), bool); xi = np.round(X).astype(int); yi = np.round(Yy).astype(int)
    ok = (xi >= 0) & (xi < RES) & (yi >= 0) & (yi < RES); m[yi[ok], xi[ok]] = True
    return ndimage.binary_closing(m, np.ones((3, 3)), border_value=0) | m


def best_shift(model, native):
    F = np.fft.rfft2(native.astype(float)); G = np.fft.rfft2(model.astype(float))
    c = np.fft.irfft2(F * np.conj(G), s=native.shape); iy, ix = np.unravel_index(np.argmax(c), c.shape)
    if iy > RES // 2: iy -= RES
    if ix > RES // 2: ix -= RES
    return iy, ix


def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))


def soft_iou(a, b):
    A = ndimage.gaussian_filter(a.astype(float), 1.); B = ndimage.gaussian_filter(b.astype(float), 1.)
    return float(np.minimum(A, B).sum() / max(np.maximum(A, B).sum(), 1e-9))


def evaluate(model, p, targets, elev, scale, detail=False):
    pts, _ = model.points(p); scores = []; info = []
    for view, nat in targets:
        m = splat(pts, view, elev, scale); dy, dx = best_shift(m, nat); m = np.roll(np.roll(m, dy, 0), dx, 1)
        scores.append(soft_iou(m, nat)); info.append((view, m, nat, (dy, dx), iou(m, nat)))
    return (float(np.mean(scores)), info) if detail else float(np.mean(scores))


def sheet(info, path, label):
    tiles = []
    for view, m, nat, sh, i in info:
        rgb = np.zeros((RES, RES, 3), np.uint8) + 40
        rgb[nat] = (60, 150, 60); rgb[m & ~nat] = (200, 60, 60); rgb[m & nat] = (230, 220, 120)
        tiles.append(rgb)
    Image.fromarray(np.concatenate(tiles, 1)).resize((RES * 2 * len(tiles), RES * 2), Image.NEAREST).save(path)


def fit_pose(model, start, prior, keys, targets, elev, scale, reg=.02, iters=2500):
    lo = np.array([DP.BOUNDS[k.replace('r_', '')][0] for k in keys]); hi = np.array([DP.BOUNDS[k.replace('r_', '')][1] for k in keys])
    x0 = np.array([start.get(k, DP.DEFAULT.get(k.replace('r_', ''), 0.)) for k in keys])
    pr = np.array([prior.get(k, DP.DEFAULT.get(k.replace('r_', ''), 0.)) for k in keys])
    def f(x):
        q = dict(start); q.update(dict(zip(keys, np.clip(x, lo, hi))))
        return 1 - evaluate(model, q, targets, elev, scale) + reg * np.sum(((x - pr) / (hi - lo)) ** 2)
    r = minimize(f, x0, method='Powell', bounds=list(zip(lo, hi)),
                 options={'maxfev': iters, 'xtol': 1e-3, 'ftol': 1e-5, 'direc': np.diag(.12 * (hi - lo))})
    q = dict(start); q.update(dict(zip(keys, np.clip(r.x, lo, hi)))); return q, r


POSE_KEYS = ['root_pitch', 'root_roll', 'spine_pitch', 'neck_pitch1', 'neck_pitch2', 'head_pitch', 'jaw', 'tail_pitch1', 'tail_pitch2',
             'fore_upper', 'fore_lower', 'hind_upper', 'hind_lower', 'w_elev', 'w_sweep', 'w_twist', 'w_elbow', 'w_hand', 'w_tip', 'w_fold']


def calibrate():
    model = Model(); targets = [(v, native_mask(f'sa{v}')) for v in range(5)]
    best = None
    for elev in np.radians([0, 8, 16, 24]):
        for scale in (200., 230., 260.):
            s = evaluate(model, {}, targets, elev, scale)
            if best is None or s > best[0]: best = (s, elev, scale)
    s0, elev, scale = best; print('grid', s0, np.degrees(elev), scale, flush=True)
    pose = {'w_elev': .9}
    for rnd in range(3):
        pose, r = fit_pose(model, pose, {}, POSE_KEYS, targets, elev, scale, iters=1500)
        def g(x): return 1 - evaluate(model, pose, targets, x[0], x[1])
        rr = minimize(g, [elev, scale], method='Powell', bounds=[(0, .6), (150, 330)], options={'maxfev': 200})
        elev, scale = rr.x; print('round', rnd, 1 - rr.fun, np.degrees(elev), scale, flush=True)
    s, info = evaluate(model, pose, targets, elev, scale, detail=True)
    sheet(info, SHOTS / 'calibrate_sa.png', 'sa')
    out = {'elevation_rad': float(elev), 'elevation_deg': float(np.degrees(elev)), 'scale_px_per_m_at_256': float(scale),
           'binding_scale_estimate': float(scale * 2 / 2 / .4 / 1.0) / 1.0, 'soft_iou': s, 'iou_per_view': [i[4] for i in info], 'pose': pose}
    # 256 px = 512 x2 px; x2 px per model metre = 2 * scale; one native px = 5 world units at tier A and 2 x2 px
    out['binding_scale_estimate'] = float(scale * 2 / 2 * 5)
    (FIT / 'calibration.json').write_text(json.dumps(out, indent=2) + '\n'); print('CALIBRATE', json.dumps(out)); return out


# hand-read starting guesses for the big rotations (Powell stays near its start): hit rears up and twists, death
# rolls and lies across the view (the death frames are the front view only, shown from every direction in game)
INIT = {
    ('hit', 'na'): {'root_pitch': -.6, 'neck_pitch1': -.3, 'head_pitch': -.4},
    ('hit', 'nb'): {'root_pitch': -1.2, 'neck_pitch1': -.4, 'head_pitch': -.5},
    ('hit', 'nc'): {'root_pitch': -1.3, 'root_roll': .4, 'neck_pitch1': .4},
    ('hit', 'nd'): {'root_pitch': -1.2, 'root_roll': .3},
    ('hit', 'ne'): {'root_pitch': -.7},
    ('hit', 'nf'): {'root_pitch': -.2},
    ('death', 'na'): {'root_pitch': -.6, 'neck_pitch1': -.3, 'head_pitch': -.4},
    ('death', 'nb'): {'root_pitch': -1.2, 'neck_pitch1': -.4, 'head_pitch': -.5},
    ('death', 'nc'): {'root_pitch': -1.3, 'root_roll': .4, 'neck_pitch1': .4},
    ('death', 'da'): {'root_pitch': -.6, 'root_roll': 1.0, 'root_yaw': .6},
    ('death', 'db'): {'root_pitch': 0., 'root_roll': 1.4, 'root_yaw': 1.2},
    ('death', 'dc'): {'root_pitch': 0., 'root_roll': .9, 'root_yaw': 1.4},
    ('death', 'xa'): {'root_pitch': 0., 'root_roll': .2, 'root_yaw': 1.57, 'w_elev': -.2, 'r_w_elev': -.2},
    ('death', 'dd'): {'root_pitch': 0., 'root_roll': .2, 'root_yaw': 1.57, 'w_elev': -.2, 'r_w_elev': -.2},
}
ASYM_KEYS = ['root_yaw', 'spine_yaw', 'neck_yaw', 'neck_roll', 'head_yaw', 'tail_yaw1', 'tail_yaw2'] + ['r_' + k for k in DP.WING_KEYS]


def fit_clip(clip, reg=.05, iters=2500):
    cal = json.loads((FIT / 'calibration.json').read_text()); elev, scale = cal['elevation_rad'], cal['scale_px_per_m_at_256']
    model = Model(); prev = dict(cal['pose']); out = {'clip': clip, 'elevation_rad': elev, 'scale': scale, 'frames': []}
    asym = clip in ('hit', 'death')
    for frame, t in CLIPS[clip]:
        views = [0] if frame in DEATH_FRONT_ONLY else range(5)
        targets = [(v, native_mask(f'{frame}{v}')) for v in views]
        keys = POSE_KEYS + (ASYM_KEYS if asym else [])
        if frame == 'sa':
            pose = dict(cal['pose'])
        else:
            start = dict(prev)
            for k in DP.WING_KEYS: start.setdefault('r_' + k, start.get(k, 0.)) if asym else None
            best = None
            for e_ in np.arange(-1.3, 1.45, .2):
                for h_ in np.arange(-.6, 1.25, .3):
                    q = dict(start); q.update({'w_elev': e_, 'w_hand': h_, 'w_tip': h_ * .5})
                    if asym: q.update({'r_w_elev': e_, 'r_w_hand': h_, 'r_w_tip': h_ * .5})
                    sc_ = evaluate(model, q, targets, elev, scale)
                    if best is None or sc_ > best[0]: best = (sc_, q)
            start = best[1]
            pose, r = fit_pose(model, start, prev, keys, targets, elev, scale, reg=reg, iters=iters)
            if (clip, frame) in INIT:
                s2 = dict(start); s2.update(INIT[(clip, frame)])
                pose2, r2 = fit_pose(model, s2, s2, keys, targets, elev, scale, reg=reg, iters=iters)
                if r2.fun < r.fun: pose, r = pose2, r2
            if not asym: pose = {k: v for k, v in pose.items() if not k.startswith('r_')}
        s, info = evaluate(model, pose, targets, elev, scale, detail=True)
        sheet(info, SHOTS / f'{clip}_{frame}.png', frame)
        out['frames'].append({'frame': frame, 'time': t, 'soft_iou': s, 'iou_per_view': {int(i[0]): i[4] for i in info},
                              'shift_px': {int(i[0]): [int(i[3][0]), int(i[3][1])] for i in info}, 'pose': pose})
        print(clip, frame, round(s, 3), [round(i[4], 3) for i in info], flush=True)
        prev = pose
    (FIT / f'{clip}.json').write_text(json.dumps(out, indent=1) + '\n'); return out


SIDE_LIE = {   # lying on the right side, belly toward the front view, head left (native corpse xa); falling frames between
    'da': {'root_yaw': -.7, 'root_pitch': -1.1, 'r_w_elev': .9, 'w_elev': .4},
    'db': {'root_yaw': -1.2, 'root_pitch': -1.4, 'r_w_elev': 1.2, 'w_elev': .2},
    'dc': {'root_yaw': -1.5, 'root_pitch': -1.55, 'r_w_elev': 1.4, 'w_elev': -.2, 'w_fold': .3},
    'xa': {'root_yaw': -1.57, 'root_pitch': -1.57, 'r_w_elev': 1.45, 'w_elev': -.6, 'w_fold': .5, 'neck_pitch1': .4, 'head_pitch': .2},
    'dd': {'root_yaw': -1.57, 'root_pitch': -1.57, 'r_w_elev': 1.45, 'w_elev': -.6, 'w_fold': .5, 'neck_pitch1': .4, 'head_pitch': .2},
}


def refit_death(reg=.08, iters=3000):
    """Late death frames (front view only) refitted in the side-lying family, with a floor-consistency penalty: no wing
    or head vertex may sink more than 1 cm below the lowest trunk vertex (the corpse lies on the trunk)."""
    cal = json.loads((FIT / 'calibration.json').read_text()); elev, scale = cal['elevation_rad'], cal['scale_px_per_m_at_256']
    model = Model(); d = json.loads((FIT / 'death.json').read_text())
    wing = np.load(P / 'work/v2/rig_v2.npz')['wing']
    keys = POSE_KEYS + ASYM_KEYS + ['root_yaw']
    for fr in d['frames']:
        if fr['frame'] not in SIDE_LIE: continue
        targets = [(0, native_mask(f"{fr['frame']}0"))]
        start = DP.full(fr['pose']); [start.setdefault('r_' + k, start[k]) for k in DP.WING_KEYS]; start.update(SIDE_LIE[fr['frame']])
        lo = np.array([DP.BOUNDS[k.replace('r_', '')][0] for k in keys]); hi = np.array([DP.BOUNDS[k.replace('r_', '')][1] for k in keys])
        x0 = np.array([start.get(k, 0.) for k in keys]); pr = x0.copy()
        def f(x):
            q = dict(start); q.update(dict(zip(keys, np.clip(x, lo, hi))))
            v = model.sk.pose(q); body_min = v[~wing, 2].min(); pen = max(0., body_min - v[:, 2].min() - .01) * 20
            return 1 - evaluate(model, q, targets, elev, scale) + reg * np.sum(((x - pr) / (hi - lo)) ** 2) + pen
        r = minimize(f, x0, method='Powell', bounds=list(zip(lo, hi)), options={'maxfev': iters, 'xtol': 1e-3, 'ftol': 1e-5, 'direc': np.diag(.08 * (hi - lo))})
        pose = dict(start); pose.update(dict(zip(keys, np.clip(r.x, lo, hi))))
        s_, info = evaluate(model, pose, targets, elev, scale, detail=True); sheet(info, SHOTS / f"death_{fr['frame']}.png", fr['frame'])
        fr.update({'soft_iou': s_, 'iou_per_view': {0: info[0][4]}, 'shift_px': {0: [int(info[0][3][0]), int(info[0][3][1])]}, 'pose': pose, 'family': 'side-lie'})
        print('death', fr['frame'], round(s_, 3), round(info[0][4], 3), flush=True)
    (FIT / 'death.json').write_text(json.dumps(d, indent=1) + '\n')


CORPSE = {'root_yaw': -1.57, 'root_pitch': -1.57, 'w_elev': 1.5, 'w_fold': .7, 'w_hand': .2, 'r_w_elev': 1.22, 'r_w_fold': .2,
          'r_w_hand': -.1, 'neck_pitch1': .3, 'neck_pitch2': .3, 'head_pitch': .1, 'fore_upper': .2, 'hind_upper': .3, 'jaw': .25}


def refit_corpse(reg=.1, iters=2500):
    """Corpse (xa, dd: front view only) lying on its right side, belly to the view, head left as in the native corpse;
    the wing elevations are fixed (top wing draped over the back, bottom wing sloping to the ground behind it), the
    rest is fitted with a floor-consistency penalty."""
    cal = json.loads((FIT / 'calibration.json').read_text()); elev, scale = cal['elevation_rad'], cal['scale_px_per_m_at_256']
    model = Model(); d = json.loads((FIT / 'death.json').read_text()); wing = np.load(P / 'work/v2/rig_v2.npz')['wing']
    keys = ['root_roll', 'spine_pitch', 'spine_yaw', 'neck_pitch1', 'neck_pitch2', 'neck_yaw', 'head_pitch', 'head_yaw', 'jaw', 'tail_pitch1', 'tail_pitch2',
            'tail_yaw1', 'tail_yaw2', 'fore_upper', 'fore_lower', 'hind_upper', 'hind_lower', 'w_fold', 'w_hand', 'w_tip', 'w_sweep', 'r_w_fold', 'r_w_hand', 'r_w_tip', 'r_w_sweep']
    for fr in d['frames']:
        if fr['frame'] not in ('xa', 'dd'): continue
        targets = [(0, native_mask(f"{fr['frame']}0"))]; start = DP.full(CORPSE); [start.setdefault('r_' + k, start[k]) for k in DP.WING_KEYS]
        lo = np.array([DP.BOUNDS[k.replace('r_', '')][0] for k in keys]); hi = np.array([DP.BOUNDS[k.replace('r_', '')][1] for k in keys])
        x0 = np.array([start.get(k, 0.) for k in keys]); pr = x0.copy()
        def f(x):
            q = dict(start); q.update(dict(zip(keys, np.clip(x, lo, hi))))
            v = model.sk.pose(q); pen = max(0., v[~wing, 2].min() - v[:, 2].min() - .01) * 20
            return 1 - evaluate(model, q, targets, elev, scale) + reg * np.sum(((x - pr) / (hi - lo)) ** 2) + pen
        r = minimize(f, x0, method='Powell', bounds=list(zip(lo, hi)), options={'maxfev': iters, 'xtol': 1e-3, 'ftol': 1e-5, 'direc': np.diag(.08 * (hi - lo))})
        pose = dict(start); pose.update(dict(zip(keys, np.clip(r.x, lo, hi))))
        s_, info = evaluate(model, pose, targets, elev, scale, detail=True); sheet(info, SHOTS / f"death_{fr['frame']}.png", fr['frame'])
        fr.update({'soft_iou': s_, 'iou_per_view': {0: info[0][4]}, 'shift_px': {0: [int(info[0][3][0]), int(info[0][3][1])]}, 'pose': pose, 'family': 'corpse side-lie'})
        print('corpse', fr['frame'], round(s_, 3), round(info[0][4], 3), flush=True)
    (FIT / 'death.json').write_text(json.dumps(d, indent=1) + '\n')


if __name__ == '__main__':
    if sys.argv[1] == 'calibrate': calibrate()
    if sys.argv[1] == 'fit': fit_clip(sys.argv[2])
    if sys.argv[1] == 'refit_death': refit_death()
    if sys.argv[1] == 'refit_corpse': refit_corpse()
