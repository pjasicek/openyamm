"""Joints of the Meshy body, from plane sections: same names as MM9's rig, positions on our mesh (Blender frame: faces -Y, z up, feet at 0).
Writes work/joints.json + prints against MM9. Args: <npz> <out json>"""
import sys, json
import numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from meshlib import section, nearest_loop
npz, out = sys.argv[1:3]
D = np.load(npz); co, tri = D['co'], D['tri']
X, Y, Z = np.eye(3)
# crotch: going down, where one torso loop becomes two leg loops
zs = np.arange(1.2, 0.6, -0.005)
crotch = None
for z in zs:
    L = [l for l in section(co, tri, np.array([0, 0, z]), Z) if l['per'] > 0.1 and abs(l['c'][0]) < 0.45]
    if len(L) == 2 and L[0]['c'][0] * L[1]['c'][0] < 0:
        crotch = z; break
print('crotch', crotch)
# neck: smallest perimeter between shoulders and chin
best = None
for z in np.arange(1.45, 1.72, 0.005):
    L = nearest_loop([l for l in section(co, tri, np.array([0, 0, z]), Z)], np.array([0, 0, z]))
    if L is not None and (best is None or L['per'] < best[1]): best = (z, L['per'], L['c'])
neck_z, neck_per, neck_c = best
print('neck', neck_z, neck_per, neck_c)
J = {}
hip_z = crotch + 0.085
pel = nearest_loop(section(co, tri, np.array([0, 0, hip_z]), Z), np.array([0, 0, hip_z]))['c']
head_z = neck_z - 0.02
ratios = dict(Pelvis=0, Spine=.161, Spine1=.345, Spine2=.528, Spine3=.711, Neck=.894, Head=1.0)
for k, r in ratios.items():
    z = hip_z + (head_z - hip_z) * r
    L = nearest_loop(section(co, tri, np.array([0, 0, z]), Z), np.array([0, pel[1], z]))
    J['Bip01 ' + k if k != 'Pelvis' else 'Bip01 Pelvis'] = [0.0, float(L['c'][1]), float(z)]
for sn, sx in (('L', -1), ('R', 1)):
    # raw MM9: L at -x. Leg axis
    pts = []
    for z in np.arange(crotch - 0.03, 0.12, -0.02):
        L = nearest_loop([l for l in section(co, tri, np.array([0, 0, z]), Z) if l['c'][0] * sx > 0], np.array([sx * (0.1 + (crotch - z) * .3), 0, z]))
        pts.append(L['c'])
    pts = np.array(pts)
    hip = np.array([sx * max(0.075, abs(pts[0][0]) * .75), pel[1], hip_z])
    # ankle: the leg axis at MM9's ankle height
    ank_z = 0.105
    fit = np.polyfit(pts[-8:, 2], pts[-8:, :2], 1)
    ank = np.array([*(fit[0] * ank_z + fit[1]), ank_z])
    poly = np.vstack([hip, pts, ank])
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    knee = np.array([np.interp(s[-1] / 2, s, poly[:, i]) for i in range(3)])
    # foot: forward extent on the sole
    fv = co[(co[:, 2] < 0.1) & (co[:, 0] * sx > 0)]
    tip_y = fv[:, 1].min(); heel_y = fv[:, 1].max()
    ball_y = heel_y + (tip_y - heel_y) * 0.70
    bv = fv[np.abs(fv[:, 1] - ball_y) < 0.02]
    toe = np.array([bv[:, 0].mean(), ball_y, 0.02])
    print(sn, 'hip', hip.round(3), 'knee', knee.round(3), 'ankle', ank.round(3), 'toe', toe.round(3), 'leg len', s[-1].round(3), 'heel', heel_y.round(3), 'tip', tip_y.round(3))
    J[f'Bip01 {sn} Thigh'] = hip.tolist(); J[f'Bip01 {sn} Calf'] = knee.tolist(); J[f'Bip01 {sn} Foot'] = ank.tolist(); J[f'Bip01 {sn} Toe0'] = toe.tolist()
    # arm: sections by x planes outward from where the loop stops being the torso
    pts = []; pers = []
    for x in np.arange(0.70 * 0 + 0.22, 0.56, 0.01):
        L = [l for l in section(co, tri, np.array([sx * x, 0, 0]), X)]
        L = [l for l in L if l['c'][2] > 1.1]
        if not L: continue
        l = min(L, key=lambda l: abs(l['c'][1]) + 0 * l['per'])
        pts.append(l['c']); pers.append(l['per'])
    pts = np.array(pts); pers = np.array(pers)
    # torso while the perimeter is large
    i0 = int(np.argmax(pers < 0.42))
    arm = pts[i0:]
    print(sn, 'arm first', arm[0].round(3), 'per', pers[i0].round(3), 'last', arm[-1].round(3))
    d = (arm[-5] - arm[3]); d /= np.linalg.norm(d)
    # wrist: smallest perimeter section perpendicular to the axis in the outer third
    best = None
    fitp = arm[len(arm) // 3:]
    c0 = fitp.mean(0); dd = np.linalg.svd(fitp - c0)[2][0]; dd = dd * np.sign(dd @ d)
    for t in np.arange(0.0, 0.5, 0.005):
        p = arm[len(arm) // 2] + dd * t
        l = nearest_loop(section(co, tri, p, dd), p)
        if l is None or np.linalg.norm(l['c'] - p) > 0.06: continue
        print('   w', round(float(t), 3), l['c'].round(3), round(l['per'], 3), l['n']) if int(t * 1000) % 40 == 0 else None
        if best is None or l['per'] < best[0]:
            if p[0] * sx > 0.40: best = (l['per'], l['c'])
    wrist = best[1]
    sh = arm[0] + (arm[0] - arm[4]) / np.linalg.norm(arm[0] - arm[4]) * 0.03
    sh = np.array([sh[0], sh[1], sh[2]])
    poly = np.vstack([sh, arm[(np.abs(arm[:, 0]) > abs(sh[0])) & (np.abs(arm[:, 0]) < abs(wrist[0]))], wrist])
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); s = np.r_[0, np.cumsum(seg)]
    el = np.array([np.interp(s[-1] * .559, s, poly[:, i]) for i in range(3)])
    print(sn, 'shoulder', sh.round(3), 'elbow', el.round(3), 'wrist', wrist.round(3), 'arm len', s[-1].round(3))
    J[f'Bip01 {sn} UpperArm'] = sh.tolist(); J[f'Bip01 {sn} Forearm'] = el.tolist(); J[f'Bip01 {sn} Hand'] = wrist.tolist()
    nb = np.array(J['Bip01 Neck'])
    J[f'Bip01 {sn} Clavicle'] = [sx * 0.035, nb[1], nb[2]]
json.dump(J, open(out, 'w'), indent=1)
