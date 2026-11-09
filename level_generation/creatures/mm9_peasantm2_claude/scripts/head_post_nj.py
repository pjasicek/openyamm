"""Head pass (coordinator, 2026-10-31): vertex moves only, after the UV freeze and neck_fix_nj.py, so faces, UVs and weights stay.
- Face sharpened: the balloon head (head_fix_nj.py) came out soft (heavy low-pass, a last projection at 0.8). Every face-skin vertex in front
  of the hair is projected once more onto Meshy's own skin and eye caps (head_v1.blend, at the graft offset), nearest point within 5 mm,
  full strength, then folds are despiked.
- Hair rim tapered: the helmet stood 0.6-2 cm off the skin to its very edge, so its inner lip read as a dark band under the fringe and a
  pale strip beside each cheek. The thickness over the skin swells 12 % about 1.2 cm above the rim and rolls in to 55 % at the edge (a
  pageboy roll; a plain taper to 30 % made a bathing cap), and the lip under the rim lies 1.5 mm off the skin.
Args: <in blend> <out blend> <head_v1 blend>"""
import bpy, bmesh, sys
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT, HEADSRC = sys.argv[sys.argv.index('--') + 1:]
OFF = Vector((0.0, 0.0604, 0.8022))           # graft_nj.py's offset (head-local -> body)
CH = Vector((0.0, 0.0104, 0.8222))            # head_fix_nj.py's hair centre C, at the graft offset
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; me = body.data
with bpy.data.libraries.load(HEADSRC) as (src, dst):
    dst.objects = [n for n in src.objects if n in ('Face', 'Eyes')]
tb = bmesh.new()
for o in dst.objects:
    tb.from_mesh(o.data)
for v in tb.verts: v.co += OFF
tbvh = BVHTree.FromBMesh(tb)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
part = bm.faces.layers.int['part']
vparts = {}
for f in bm.faces:
    for v in f.verts: vparts.setdefault(v, set()).add(f[part])
# ---- face sharpen
face_v = [v for v, ps in vparts.items() if ps == {20} and v.co.z > 0.715 and not any(e.is_boundary for e in v.link_edges)]
moved = []
for v in face_v:
    loc, nrm, idx, dist = tbvh.find_nearest(v.co)
    if loc is not None and dist < 0.005:
        moved.append(dist); v.co = loc
fv = set(face_v)
desp = []
for r in range(4):
    bm.normal_update(); bad = []
    for v in fv:
        c = sum((e.other_vert(v).co for e in v.link_edges), Vector()) / len(v.link_edges)
        L = sum(e.calc_length() for e in v.link_edges) / len(v.link_edges)
        if (v.co - c).length > 0.5 * L or min(f.normal.dot(v.normal) for f in v.link_faces) < 0.2: bad.append((v, c))
    for v, c in bad: v.co = v.co * 0.4 + c * 0.6
    desp.append(len(bad))
print('HEADPOST face verts projected', len(moved), 'mean move mm', round(float(np.mean(moved)) * 1000, 2) if moved else 0, 'despike', desp)
# ---- hair rim taper
fb = bmesh.new()
for f in bm.faces:
    pass
skin = [f for f in bm.faces if f[part] == 20]
sk = bmesh.new()
vm = {}
for f in skin:
    vs = []
    for v in f.verts:
        if v not in vm: vm[v] = sk.verts.new(v.co)
        vs.append(vm[v])
    try: sk.faces.new(vs)
    except ValueError: pass
sbvh = BVHTree.FromBMesh(sk)
rim = [v for v, ps in vparts.items() if 21 in ps and 23 in ps]
lip = [v for v, ps in vparts.items() if ps == {23}]
outer = [v for v, ps in vparts.items() if ps == {21}] + rim
R = np.array([v.co[:] for v in rim])
def skin_r(p):
    d = (p - CH); n = d.length; d = d / n
    loc, nrm, idx, dist = sbvh.ray_cast(CH + d * 0.4, -d, 0.4)
    return (0.4 - dist) if idx is not None else None, n, d
t_old, t_new = [], []
for v in outer:
    sr, n, d = skin_r(v.co)
    if sr is None: continue
    t = n - sr
    if t <= 0.003: continue
    e = float(np.min(np.linalg.norm(R - np.array(v.co[:]), axis=1))) if len(R) else 1.0
    sm = lambda x: (lambda c: c * c * (3 - 2 * c))(min(max(x, 0.0), 1.0))
    # a rolled pageboy rim: the hair swells 12 % about 1.2 cm above its edge, then rolls in to 55 % at the edge (first try, a plain taper
    # to 30 % over 3 cm, made a bathing cap)
    k = 0.55 + 0.57 * sm(e / 0.012) if e < 0.012 else 1.12 - 0.12 * sm((e - 0.012) / 0.018)
    t2 = max(t * k, 0.003)
    v.co = CH + d * (sr + t2); t_old.append(t); t_new.append(t2)
for v in lip:
    sr, n, d = skin_r(v.co)
    if sr is None: continue
    v.co = CH + d * (sr + 0.0015)
print('HEADPOST hair verts tapered', len(t_new), 'rim', len(rim), 'lip', len(lip), 'thickness at rim cm', round(float(np.median([b for a, b, v in zip(t_old, t_new, outer) if v in set(rim)] or [0])) * 100, 2))
bm.normal_update()
bm.to_mesh(me); bm.free(); tb.free(); sk.free()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('HEADPOST done')
