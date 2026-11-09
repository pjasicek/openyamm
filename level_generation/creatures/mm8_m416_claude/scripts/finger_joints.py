"""G5: finger joints from the mesh centrelines (fit_fingers.py, connectivity split). Each chain (thumb included) is
split at the source's relative phalanx lengths: knuckle -> 1st -> 2nd joint -> tip (stored as <distal>_tip).
Writes work/finger_joints.json {side: {bone: [x,y,z], ...}} (heads of B_<s>_Finger<i>, <i>1, <i>2 / R thumb quirk
names) and prints the shift from the carried source joints. Args: -- <rig blend>"""
import bpy, sys, os, json
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
FIT = json.load(open(os.path.join(HERE, 'work', 'fingers_fit.json')))
SRC = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
B = lambda n: np.array(rig.data.bones[n].head_local)


def chain(side, f):
    names = [f'B_{side}_Finger{f}']
    while True:
        k = [b.name for b in rig.data.bones if b.parent and b.parent.name == names[-1]]
        if not k:
            return names
        names.append(k[0])


def resample(poly, fractions):
    seg = np.linalg.norm(np.diff(poly, axis=0), axis=1); cum = np.r_[0, np.cumsum(seg)]
    out = []
    for f in fractions:
        d = f * cum[-1]; i = min(np.searchsorted(cum, d) - 1, len(seg) - 1); i = max(i, 0)
        t = (d - cum[i]) / max(seg[i], 1e-9)
        out.append(poly[i] + (poly[i + 1] - poly[i]) * t)
    return np.array(out)


out = {}
for side in ('R', 'L'):
    res = {}
    for f, name in ((0, 'thumb'), (1, 'index'), (2, 'middle'), (3, 'ring'), (4, 'pinky')):
        names = chain(side, f)
        poly = np.array(FIT[side][name])
        sp = [np.array(SRC[n]['head']) for n in names]; sp.append(sp[-1] + (sp[-1] - sp[-2]))
        L = np.linalg.norm(np.diff(sp, axis=0), axis=1); fr = np.r_[0, np.cumsum(L)] / L.sum()
        joints = resample(poly, fr)                      # 3 heads + the tip
        if f == 0:
            # The separated thumb starts at MCP; the first source thumb bone is the metacarpal inside the palm.
            wrist = B(f'B_{side}_Hand')
            mcp = joints[0].copy(); ip = (joints[1] + joints[2]) * 0.5
            joints[:3] = [wrist + (mcp - wrist) * 0.45, mcp, ip]
            assert np.linalg.norm(joints[1] - joints[0]) > 0.015
        for n, p in zip(names, joints[:3]):
            res[n] = p.tolist()
        res[names[-1] + '_tip'] = joints[3].tolist()
        shift = [round(float(np.linalg.norm(joints[i] - B(names[i]))) * 100, 1) for i in range(3)]
        print('FJ', side, name, 'length cm', round(float(np.linalg.norm(np.diff(poly, axis=0), axis=1).sum()) * 100, 1),
              'shift from carried source (cm)', shift)
    out[side] = res
json.dump(out, open(os.path.join(HERE, 'work', 'finger_joints.json'), 'w'), indent=1)
