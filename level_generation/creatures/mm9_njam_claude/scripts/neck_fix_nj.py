"""The grafted neck's lower rim is jagged (the balloon's last rows), and graft_nj.py's per-vertex stretch turned its lowest points
into long straps under the collar. Run on the UV blend (or a re-rig after carry_uv.py), head faces only, body faces and UVs untouched:
the face skin below z = CUT goes, and the cut rim is bridged straight down to a level ring at BASE (flared FLARE x round the neck
centre), two rows. New vertices copy the weights of their rim vertex, faded to Spine3 at the bottom; their HeadUV/PartUV are one plain neck-skin
texel (the front-most rim vertex's).
Args: <in blend> <out blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
CUT, BASE, FLARE = 0.705, 0.62, 0.8     # narrowing down: a flared (1.45) or straight tube met the shirt V at the throat in a jagged line
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
part = bm.faces.layers.int['part']; mat = bm.faces.layers.int['mat']
uvl = {n: bm.loops.layers.uv[n] for n in ('UVMap', 'HeadUV', 'PartUV') if n in bm.loops.layers.uv}
dv = bm.verts.layers.deform.verify()
dead = [f for f in bm.faces if f[part] == 20 and any(v.co.z < CUT for v in f.verts)]
bmesh.ops.delete(bm, geom=dead, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
# the head skin's lowest boundary loop
rim_e = [e for e in bm.edges if e.is_boundary and e.link_faces[0][part] == 20]
rv = {v for e in rim_e for v in e.verts}
low = [v for v in rv if v.co.z < CUT + 0.03]
start = min(low, key=lambda v: v.co.z)
loop = [start]; used = set()
while True:
    nx = [e for e in loop[-1].link_edges if e.is_boundary and e not in used and e.link_faces[0][part] == 20]
    if not nx: break
    used.add(nx[0]); w = nx[0].other_vert(loop[-1])
    if w is loop[0]: break
    loop.append(w)
P = np.array([v.co[:] for v in loop])
print('NECK cut faces', len(dead), 'rim verts', len(loop), 'rim z', P[:, 2].min().round(3), P[:, 2].max().round(3))
c = Vector((0.0, float(0.5 * (P[:, 1].min() + P[:, 1].max())), 0.0))
sp3 = body.vertex_groups['Bip01 Spine3'].index
# uv of each rim vertex (from any of its faces)
def uv_of(v):
    l = v.link_loops[0]
    return {n: l[L].uv.copy() for n, L in uvl.items()}
# one skin texel for every new face: the front-most rim vertex's (plain neck skin, project_head.py paints the neck below the jaw
# as one tone); a stretched rim UV drew stripes down the neck above the collar
UV0 = uv_of(min(loop, key=lambda v: v.co.y))
rings = [loop]
for k, (zf, fl) in enumerate(((0.5, 1.12), (1.0, FLARE))):
    ring = []
    for v in loop:
        z = v.co.z + (BASE - v.co.z) * zf
        nv = bm.verts.new(Vector((v.co.x * fl, c.y + (v.co.y - c.y) * fl, z)))
        w = dict(v[dv].items()); s = sum(w.values()) or 1.0
        fade = zf
        nw = {g: x / s * (1 - fade) for g, x in w.items()}
        nw[sp3] = nw.get(sp3, 0.0) + fade
        for g, x in nw.items():
            if x > 1e-4: nv[dv][g] = x
        ring.append(nv)
    rings.append(ring)
new = []
n = len(loop)
for r in range(2):
    a, b = rings[r], rings[r + 1]
    for i in range(n):
        j = (i + 1) % n
        for tri, src in (((a[i], b[i], b[j]), (loop[i], loop[i], loop[j])), ((a[i], b[j], a[j]), (loop[i], loop[j], loop[j]))):
            try:
                f = bm.faces.new(tri)
            except ValueError:
                continue
            f[part] = 20; f[mat] = 2; f.smooth = True
            for l in f.loops:
                for nme, L in uvl.items(): l[L].uv = UV0[nme]
            new.append(f)
# outward: the new faces agree with the neck above them
bm.normal_update()
out = sum((f.calc_center_median() - Vector((0, c.y, f.calc_center_median().z))).dot(f.normal) for f in new)
if out < 0: bmesh.ops.reverse_faces(bm, faces=new)
print('NECK new faces', len(new), 'flipped' if out < 0 else 'kept')
# the hair helmet's lip (its inward-facing rows under the rim) becomes part 23: project_head.py fills it from the outer hair, so the
# front view's skin no longer lands on it (a pale strip beside each cheek, a dark band under the fringe)
hc = Vector((0.0, 0.063, 0.80)); lip = 0
for f in bm.faces:
    if f[part] == 21 and f.normal.dot(f.calc_center_median() - hc) < 0:
        f[part] = 23; lip += 1
print('NECK hair lip faces', lip)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('NECKFIX', len(me.polygons))
