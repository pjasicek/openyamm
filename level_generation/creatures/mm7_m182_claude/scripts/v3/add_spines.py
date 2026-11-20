"""MM7 dorsal spine row (Blender): remove the cdr1 dorsal spikes (small separate pieces on the midline) and add
procedural swept blades along the dorsal midline from behind the head frill to the tail tip, sized by the native
side frame profile (work/v3/spine_params.json: height by arc fraction). Each blade is a closed shell (lens cross-
sections, sunk root, curved tip) bound rigidly to the skin weights of its root point on the body surface.
Vertex attribute v3part = 3 on blade vertices. Usage: blender -b <in.blend> -P add_spines.py -- <out.blend>"""
import bpy, bmesh, json, math, sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[2]; prm = json.loads((P / 'work/v3/spine_params.json').read_text())
out = sys.argv[sys.argv.index('--') + 1]
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
dl = bm.verts.layers.deform.verify(); part = bm.verts.layers.int.get('v3part')
# components
comp = {}; cid = 0
for v in bm.verts:
    if v in comp: continue
    st = [v]; comp[v] = cid
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in comp: comp[y] = cid; st.append(y)
    cid += 1
groups = {}
for v, c in comp.items(): groups.setdefault(c, []).append(v)
main = max(groups, key=lambda c: len(groups[c]))
dead = []
for c, vs in groups.items():
    if c == main or len(vs) > 80: continue
    cen = sum((v.co for v in vs), Vector()) / len(vs)
    if abs(cen.x) < 0.012 and all(v[part] == 0 for v in vs) and cen.y > -1.2: dead += vs
bmesh.ops.delete(bm, geom=dead, context='VERTS')
n_removed = len(dead)
# BVH of the main body surface (no wings): faces of material 0/2 belonging to the main component, wings excluded
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
wing_slot = [i for i, m in enumerate(me.materials) if 'Wing' in m.name][0]
faces = [f for f in bm.faces if f.material_index != wing_slot and comp.get(f.verts[0]) == main]
bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in faces])
# chain polyline (head side -> tail tip)
names = [prm['start_bone'], 'Neck2', 'Neck1', 'Spine2', 'Spine1'] + [f'Tail{i}' for i in range(1, 10)]
bones = rig.data.bones
pts = [bones[n].head_local.copy() for n in names]
pts.insert(0, bones[prm['start_bone']].tail_local.copy())
pts[-1:] = [bones['Tail9'].head_local.copy(), bones['Tail9'].tail_local.copy()]
# Spine1 head = Root (hips); Spine2 head -> Spine1 head goes backwards along the trunk
seg = [(pts[i], pts[i + 1]) for i in range(len(pts) - 1) if (pts[i + 1] - pts[i]).length > 1e-4]
L = sum((b - a).length for a, b in seg)
def at(s):
    for a, b in seg:
        l = (b - a).length
        if s <= l: return a + (b - a) * (s / l), (b - a).normalized()
        s -= l
    a, b = seg[-1]; return b, (b - a).normalized()
prof = prm['profile']
def height(f):
    for (f0, h0), (f1, h1) in zip(prof, prof[1:]):
        if f <= f1: return h0 + (h1 - h0) * (f - f0) / (f1 - f0)
    return prof[-1][1]
Z = Vector((0, 0, 1)); blades = []; s = prm['start_offset']
while s < L - 0.02:
    c, t = at(s); d = (Z - Z.dot(t) * t)
    if d.length < 1e-3: d = Vector((0, 0, 1))
    d.normalize()
    hit = bvh.ray_cast(c + d * 0.6, -d, 1.2)
    if hit[0] is not None:
        f = s / L; h = height(f)
        blades.append((hit[0], hit[1], t, h, hit[2], s))
        s += prm['spacing'] * (0.6 + 0.4 * h / max(p[1] for p in prof))
    else:
        s += 0.02
# build blades
new_verts = []
def lens(n=6):
    return [(math.cos(2 * math.pi * k / n), math.sin(2 * math.pi * k / n)) for k in range(n)]
for (p, nrm, t, h, fi, s) in blades:
    up = (nrm - nrm.dot(t) * t).normalized(); side = t.cross(up).normalized()
    if side.x < 0: side = -side
    b = h * prm['length_ratio']; w = h * prm['thickness_ratio']; sw = math.radians(prm['sweep_deg'])
    def ring(hf, scale, back):
        base = p + up * (hf * h) + t * back
        return [base + t * (cx * b / 2 * scale) + side * (sy * w / 2 * scale) for cx, sy in lens()]
    r0 = ring(-prm['sink'] / h, 1.0, 0)
    r1 = ring(0.5, 0.5, math.tan(sw) * 0.5 * h)
    tip = p + up * h * 0.97 + t * (math.tan(sw * 1.25) * h)
    vs0 = [bm.verts.new(x) for x in r0]; vs1 = [bm.verts.new(x) for x in r1]; vt = bm.verts.new(tip)
    fs = []; n = len(vs0)
    for k in range(n):
        k1 = (k + 1) % n
        fs.append(bm.faces.new((vs0[k], vs0[k1], vs1[k1]))); fs.append(bm.faces.new((vs0[k], vs1[k1], vs1[k])))
        fs.append(bm.faces.new((vs1[k], vs1[k1], vt)))
    fs.append(bm.faces.new(vs0[::-1]))           # root cap (inside the body), triangulated below
    vs2 = []; vb = None
    # weights of the root point: barycentric blend of the hit face's vertices
    face = faces[fi]; fv = list(face.verts)
    wsum = {}
    for v in fv:
        wgt = 1.0 / max((v.co - p).length, 1e-4)
        for g, x in v[dl].items(): wsum[g] = wsum.get(g, 0) + wgt * x
    top = sorted(wsum.items(), key=lambda kv: -kv[1])[:4]; tot = sum(x for _, x in top)
    allv = vs0 + vs1 + [vt]
    for v in allv:
        for g, x in top: v[dl][g] = x / tot
        v[part] = 3
    for f_ in fs: f_.material_index = 0; f_.smooth = True
    # outward winding check on the first side face
    f0 = fs[0]; f0.normal_update()
    if f0.normal.dot(f0.calc_center_median() - (p + up * 0.2 * h)) < 0:
        for f_ in fs: f_.normal_flip()
bm.normal_update()
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3 and all(v[part] == 3 for v in f.verts)])
bm.to_mesh(me); bm.free(); me.update()
print('SPINES removed cdr1 dorsal verts', n_removed, 'added blades', len(blades), 'arc', round(L, 3),
      'heights', [round(b[3], 3) for b in blades])
bpy.ops.wm.save_as_mainfile(filepath=out)
