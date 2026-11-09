"""G5: finger joints from the mesh centrelines (fit_fingers.py, connectivity split). Each chain (thumb included) is
split at the source's relative phalanx lengths: knuckle -> 1st -> 2nd joint -> tip (stored as <distal>_tip).
Writes work/finger_joints.json {side: {bone: [x,y,z], ...}} (heads of B_<s>_Finger<i>, <i>1, <i>2 / R thumb quirk
names) and prints the shift from the carried source joints. Args: -- <rig blend>"""
import bpy, sys, os, json
BODY_KIND = os.environ['KEPT_BODY']
assert BODY_KIND in ('male', 'female')
BODY_ID = 'm' if BODY_KIND == 'male' else 'f'
BODY_VERSION = 'v2' if BODY_ID == 'm' else 'v1'
import numpy as np
blend = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']
FIT = json.load(open(os.path.join(HERE, 'work', BODY_KIND, 'fingers_fit.json')))
SRC = json.load(open(os.path.join(HERE, 'work', BODY_KIND, 'source_rest.json')))
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


from mathutils import Vector
from mathutils.bvhtree import BVHTree
body=bpy.data.objects['Body'];pc=[v.value for v in body.data.attributes['piece'].data]
co=[v.co.copy() for v in body.data.vertices];corrections=[]
out = {}
for side in ('R', 'L'):
    res = {}
    part=(4 if side=='L' else 3) if BODY_KIND=='male' else (3 if side=='L' else 4)
    tree=BVHTree.FromPolygons(co,[list(p.vertices) for p in body.data.polygons if pc[p.vertices[0]]==part])
    for f, name in ((0, 'thumb'), (1, 'index'), (2, 'middle'), (3, 'ring'), (4, 'pinky')):
        names = chain(side, f)
        poly = np.array(FIT[side][name])
        sp = [np.array(SRC[n]['head']) for n in names]; sp.append(sp[-1] + (sp[-1] - sp[-2]))
        L = np.linalg.norm(np.diff(sp, axis=0), axis=1); fr = np.r_[0, np.cumsum(L)] / L.sum()
        joints = resample(poly, fr)                      # 3 heads + the tip
        # A connectivity slice through a splayed knuckle can average just outside the web.
        for k in range(3):
            loc,normal,_,distance=tree.find_nearest(Vector(joints[k]))
            if (Vector(joints[k])-loc).dot(normal)>0 and distance>.0001:
                original=joints[k].copy();joints[k]=np.array(loc-normal*.004)
                corrections.append({'bone':names[k],'from':original.tolist(),'to':joints[k].tolist(),'shift_m':float(np.linalg.norm(joints[k]-original))})
        for n, p in zip(names, joints[:3]):
            res[n] = p.tolist()
        res[names[-1] + '_tip'] = joints[3].tolist()
        shift = [round(float(np.linalg.norm(joints[i] - B(names[i]))) * 100, 1) for i in range(3)]
        print('FJ', side, name, 'length cm', round(float(np.linalg.norm(np.diff(poly, axis=0), axis=1).sum()) * 100, 1),
              'shift from carried source (cm)', shift)
    out[side] = res
json.dump(corrections,open(os.path.join(HERE,'review',BODY_KIND,'joint_projection.json'),'w'),indent=2)
json.dump(out, open(os.path.join(HERE, 'work', BODY_KIND, 'finger_joints.json'), 'w'), indent=1)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
