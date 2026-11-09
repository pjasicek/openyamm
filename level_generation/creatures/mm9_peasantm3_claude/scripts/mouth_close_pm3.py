"""Close PeasantM3's mouth slot (orchestrator review 2026-11-02: "a pale band sits between the lips - the second lip / open
slot fault"). Two causes: a loose 40-vertex Meshy lip piece floating in front of the face (removed by loose_parts.py 40 0.045
-> work/mouth_t1.blend) and, behind it, a mouth pocket in the face shell itself: mouth_probe.py found shell vertices between
z 0.740 and 0.758 lying 2-3 cm behind the lips' front surface (front y -0.069, back to -0.036), a recess whose walls the
viewer's light shows as a pale band. PeasantM2d's mouth_close.py, adapted (head-set faces instead of its part number, no
hole fill: the shell has no hole at the mouth):
head-set vertices in the mouth box (|x| < XW, ZLO < z < ZHI, y < -0.03) lying more than DEEP behind the frontmost vertex
within 2 mm in x and 3 mm in z move forward to GROOVE behind it; with SQUEEZE their heights collapse toward the slot's middle
at their x (the lips meet at a crease); SMOOTH Laplacian passes (x too) within 4.5 mm of the crease even it out.
Positions only (faces, UVs, weights unchanged; the paid paints stay valid). Rest pose.
Args (Blender): <in blend> <out blend> [key=value: groove 0.0025, squeeze 1.0, deep 0.001, xw 0.03, zlo 0.738, zhi 0.760,
smooth 30]"""
import bpy, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[:2]; opt = dict(x.split('=', 1) for x in a[2:])
GR = float(opt.get('groove', 0.0025)); SQ = float(opt.get('squeeze', 1.0)); XW = float(opt.get('xw', 0.03))
ZLO, ZHI = float(opt.get('zlo', 0.738)), float(opt.get('zhi', 0.760)); DEEP = float(opt.get('deep', 0.001))
NS = int(opt.get('smooth', 30))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig is not None and rig.animation_data:
    rig.animation_data.action = None
hf = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', hf)
P = np.array([v.co[:] for v in me.vertices])
sh = np.zeros(len(P), bool)
for p in me.polygons:
    if hf[p.index]:
        sh[list(p.vertices)] = True
box = sh & (np.abs(P[:, 0]) < XW + 0.004) & (P[:, 2] > ZLO - 0.004) & (P[:, 2] < ZHI + 0.004) & (P[:, 1] < -0.03)
idx = np.where(box)[0]
Q = P[idx]
DZ = float(opt.get('dz', 0.003))   # r4: 0.0015 - the lip surface at the SAME height (with 3 mm the upper lip's overhang made
#     part of the lower lip 'pocket' and it was moved, uncovering a skin-painted wall: user note 'part of lip missing')
front = np.array([Q[(np.abs(Q[:, 0] - q[0]) < 0.002) & (np.abs(Q[:, 2] - q[2]) < DZ), 1].min() for q in Q])
behind = Q[:, 1] - front
inb = (np.abs(Q[:, 0]) < XW) & (Q[:, 2] > ZLO) & (Q[:, 2] < ZHI)
sel = inb & (behind > DEEP)
mv = idx[sel]; fr = front[sel]
newP = P.copy()
newP[mv, 1] = fr + GR
if SQ > 0:
    zc = np.array([P[mv][np.abs(P[mv, 0] - P[i, 0]) < 0.003, 2].mean() for i in mv])
    newP[mv, 2] = zc + (P[mv, 2] - zc) * (1 - SQ)
# r3: the inner lip edges (unmoved shell vertices sharing an edge with a moved one, in the box) move RIM of the way toward the
# slot's middle height at their x, so the upper and lower lip meet (the opening read as parted lips in the viewer's light)
RIM = float(opt.get('rim', 0.0))
nrim = 0
if RIM > 0 and len(mv):
    mvset = set(mv.tolist())
    adj = {}
    for e in me.edges:
        a_, b_ = e.vertices
        adj.setdefault(a_, set()).add(b_); adj.setdefault(b_, set()).add(a_)
    rim = [v_ for v_ in idx[inb].tolist() if v_ not in mvset and adj.get(v_, set()) & mvset]
    for v_ in rim:
        near = mv[np.abs(P[mv, 0] - P[v_, 0]) < 0.004]
        if len(near) == 0:
            continue
        zc_ = newP[near, 2].mean()
        newP[v_, 2] = zc_ + (P[v_, 2] - zc_) * (1 - RIM)
        nrim += 1
    # r4 (user note: "the slit is a dark jagged line"): the meeting-line vertices alone (no lip front surface) get height
    # and depth regularised along the line (Gaussian in x, sigma LINE_SIG), so the slit is one smooth curve, not a sawtooth
    LS = float(opt.get('line_sig', 0.0))
    if LS > 0 and rim:
        R = np.array(rim); X = newP[R, 0]
        Wm = np.exp(-0.5 * ((X[:, None] - X[None, :]) / LS) ** 2)
        Wm /= Wm.sum(1, keepdims=True)
        sm = Wm @ newP[R][:, 1:3]
        newP[R, 1:3] = sm
nsm = 0
if NS and len(mv):
    zcm = float(np.median(newP[mv, 2]))
    nb = {}
    for p in me.polygons:
        if not hf[p.index]:
            continue
        vs = list(p.vertices)
        for v_ in vs:
            nb.setdefault(v_, set()).update(u for u in vs if u != v_)
    zone = [v_ for v_ in np.where(sh)[0] if abs(newP[v_, 0]) < XW - 0.002 and abs(newP[v_, 2] - zcm) < 0.0045
            and newP[v_, 1] < -0.03]
    w = {v_: float(np.clip(1 - abs(newP[v_, 2] - zcm) / 0.0045, 0, 1)) for v_ in zone}
    for _ in range(NS):
        cur = newP.copy()
        for v_ in zone:
            avg = cur[list(nb[v_])].mean(0)
            newP[v_] = cur[v_] + (avg - cur[v_]) * 0.5 * w[v_]
    nsm = len(zone)
me.vertices.foreach_set('co', newP.ravel()); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOUTHCLOSE ' + json.dumps({'box': int(len(idx)), 'moved': int(len(mv)), 'max_forward_mm': round(float((Q[sel, 1] - fr - GR).max()) * 1000, 1)
                                  if len(mv) else 0, 'smoothed': nsm, 'rim_moved': nrim}))
