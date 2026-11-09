"""Close PeasantM2's mouth slot (face pre-screen 2026-11-02: lit from above, the closed mouth read as a slightly open slot with a
pale plate behind the lips: Meshy's mouth was closed far back by PeasantM2's face_fix.py, so a 2-3 mm tall recess with a back wall
1-4 cm deep sits between the lips; painted as lip it is the 'pink plate / second lip layer' of the wave-2 lessons).
Positions only (faces, UVs, weights unchanged; the paid paints stay valid): face-shell vertices (part 20) in the mouth box (|x| <
XW, ZLO < z < ZHI, y < -0.03) lying more than DEEP behind the lips' front surface near them (the frontmost shell vertex within 2 mm in x and 3 mm
in z) are the pocket and move forward to GROOVE behind it, heights unchanged (a first try that also squeezed heights and took the
frontmost vertex over the whole box crumpled the upper lip). Rest pose; vertices keep their head weights. Args (Blender): <in blend> <out blend> [key=value: groove 0.0015,
squeeze 0.6, xw 0.031, zlo 0.708, zhi 0.738]"""
import bpy, bmesh, sys, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[:2]; opt = dict(x.split('=', 1) for x in a[2:])
GR = float(opt.get('groove', 0.0015)); SQ = float(opt.get('squeeze', 0.0)); XW = float(opt.get('xw', 0.031))
ZLO, ZHI = float(opt.get('zlo', 0.708)), float(opt.get('zhi', 0.738))
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
P = np.array([v.co[:] for v in me.vertices])
sh = np.zeros(len(P), bool)
for p in me.polygons:
    if part[p.index] == 20: sh[list(p.vertices)] = True
box = sh & (np.abs(P[:, 0]) < XW + 0.004) & (P[:, 2] > ZLO - 0.004) & (P[:, 2] < ZHI + 0.004) & (P[:, 1] < -0.03)
idx = np.where(box)[0]
# the lips' front surface near each vertex: the frontmost shell vertex within 2 mm in x and 3 mm in z; a vertex more than DEEP behind
# it is the pocket (Meshy's mouth closed 1-5 cm back), moved forward to GROOVE behind that surface, its height unchanged
DEEP = float(opt.get('deep', 0.004))
Q = P[idx]
front = np.array([Q[(np.abs(Q[:, 0] - q[0]) < 0.002) & (np.abs(Q[:, 2] - q[2]) < 0.003), 1].min() for q in Q])
behind = Q[:, 1] - front
inb = (np.abs(Q[:, 0]) < XW) & (Q[:, 2] > ZLO) & (Q[:, 2] < ZHI)
sel = inb & (behind > DEEP)
mv = idx[sel]; fr = front[sel]
newP = P.copy()
newP[mv, 1] = fr + GR
if SQ > 0:      # collapse the slot's walls toward the slot's middle height at their x (the lips meet at a crease)
    zc = np.array([P[mv][np.abs(P[mv, 0] - P[i, 0]) < 0.003, 2].mean() for i in mv])
    newP[mv, 2] = zc + (P[mv, 2] - zc) * (1 - SQ)
NS = int(opt.get('smooth', 0)); SMX = opt.get('smoothx', '0') == '1'
if NS:          # even the crease: Laplacian smoothing (y and z only) of the shell vertices within 4 mm of the collapsed line
    zcm = float(np.median(newP[mv, 2]))
    nb = {}
    for p in me.polygons:
        if part[p.index] != 20: continue
        vs = list(p.vertices)
        for v_ in vs: nb.setdefault(v_, set()).update(u for u in vs if u != v_)
    zone = [v_ for v_ in np.where(sh)[0] if abs(newP[v_, 0]) < XW - 0.002 and abs(newP[v_, 2] - zcm) < 0.0045 and newP[v_, 1] < -0.03]
    w = {v_: float(np.clip(1 - abs(newP[v_, 2] - zcm) / 0.0045, 0, 1)) for v_ in zone}
    for _ in range(NS):
        cur = newP.copy()
        for v_ in zone:
            avg = cur[list(nb[v_])].mean(0)
            k0 = 0 if SMX else 1            # smoothx=1: x too (the slot's corner ends stuck out sideways as spikes)
            newP[v_, k0:] = cur[v_, k0:] + (avg[k0:] - cur[v_, k0:]) * 0.5 * w[v_]
    print('MOUTHCLOSE smoothed', len(zone))
me.vertices.foreach_set('co', newP.ravel()); me.update()
# the small hole in the face shell at the lower lip's centre (a 4-edge diamond; the front saw the back of the hair through it as a pale
# speck): face-shell boundary loops of at most 8 edges inside the mouth box are filled (holes_fill + triangulate), attributes and the
# UVs of each new corner copied from an existing face corner of the same vertex
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
lp = bm.faces.layers.int['part']
bnd = [e for e in bm.edges if sum(1 for f in e.link_faces if f[lp] == 20) == 1 and all(f[lp] == 20 for f in e.link_faces)
       and abs((e.verts[0].co.x + e.verts[1].co.x) / 2) < 0.04 and 0.69 < (e.verts[0].co.z + e.verts[1].co.z) / 2 < 0.76
       and (e.verts[0].co.y + e.verts[1].co.y) / 2 < -0.05]
nf0 = len(bm.faces)
r = bmesh.ops.holes_fill(bm, edges=bnd, sides=8)
new = r['faces']
tr = bmesh.ops.triangulate(bm, faces=new)
new = [f for f in tr['faces']] if tr['faces'] else new
ref = next(f for f in bm.faces if f[lp] == 20 and f not in new)
for f in new:
    for lay in bm.faces.layers.int.values():
        f[lay] = ref[lay]
    f.material_index = ref.material_index; f.smooth = True
    for l in f.loops:
        src = next((ll for ll in l.vert.link_loops if ll.face is not f and ll.face[lp] == 20), None)
        if src is not None:
            for uvl in bm.loops.layers.uv.values(): l[uvl].uv = src[uvl].uv
bm.normal_update()
for f in new:
    if f.normal.y > 0: f.normal_flip()            # face forward like the lip around it
bm.to_mesh(me); bm.free(); me.update()
print('MOUTHCLOSE hole edges', len(bnd), 'new faces', len(new))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('MOUTHCLOSE', json.dumps(dict(moved=int(len(mv)), max_forward_mm=round(float((newP[mv, 1] - P[mv, 1]).min() * -1000), 1))))
