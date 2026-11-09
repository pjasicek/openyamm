"""Step 1 cleanup of the Smart Topology return (work/st_v1_parts.blend, loose parts P00..):
- the left boot piece (P03) carries a thin strand up to the left hand: drop its vertices outside the boot
  (x > 0.33 or z > 0.53), then delete loose fragments under 40 faces left by the cut;
- the eye shells (P16, P17: a green blob over the left eye only) are removed; eyes are painted later.
Joins the rest into 'Body' with a 'piece' point attribute (part index). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}
DROP = {'P16', 'P17'}
boot = P['P03']
bm = bmesh.new(); bm.from_mesh(boot.data)
cut = [v for v in bm.verts if v.co.x > 0.318 or v.co.z > 0.53]   # mirror of the right boot: x <= 0.314
bmesh.ops.delete(bm, geom=cut, context='VERTS')
# remove small loose islands
seen, comps = set(), []
for f in bm.faces:
    if f in seen:
        continue
    comp, stack = [], [f]
    while stack:
        x = stack.pop()
        if x in seen:
            continue
        seen.add(x); comp.append(x)
        for e in x.edges:
            stack.extend(e.link_faces)
    comps.append(comp)
small = [f for c in comps if len(c) < 40 for f in c]
bmesh.ops.delete(bm, geom=small, context='FACES')
print('BOOT cut verts', len(cut), 'islands', len(comps), 'small faces removed', len(small))
bm.to_mesh(boot.data); bm.free()
for n in DROP:
    bpy.data.objects.remove(P.pop(n), do_unlink=True)
# triangle budget (<= 10k LOD0 for a humanoid): collapse per shell; the skin keeps full density on the head
# (z > 1.42) and the hands (|x| > 0.33, z < 1.02) through an inverted protection group
TARGET = {'P00': 4300, 'P01': 800, 'P02': 700, 'P03': 480, 'P04': 480, 'P05': 450, 'P06': 300, 'P07': 160,
          'P08': 170, 'P09': 170, 'P10': 120, 'P12': 120}
for n, tgt in (TARGET.items() if os.environ.get('REDUCE_EARLY') else []):   # moved after the weights: reduce_rigged.py
    o = P[n]; tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if tris <= tgt:
        continue
    m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'
    if n == 'P00':
        g = o.vertex_groups.new(name='protect')
        keep = [v.index for v in o.data.vertices if v.co.z > 1.42 or (abs(v.co.x) > 0.33 and v.co.z < 1.02)]
        g.add(keep, 1.0, 'REPLACE')
        m.vertex_group = 'protect'; m.invert_vertex_group = True
        free = tris - sum(1 for p in o.data.polygons if all(i in set(keep) for i in p.vertices))
        prot = tris - free
        m.ratio = 1.0                                                 # collapse acts only on the unprotected part:
        m.ratio = max(0.05, min(1.0, tgt / tris))                     # ratio is of the whole; protected faces stay
    else:
        m.ratio = tgt / tris
    bpy.context.view_layer.objects.active = o
    for x in bpy.data.objects:
        x.select_set(x == o)
    bpy.ops.object.modifier_apply(modifier='dec')
    for g in list(o.vertex_groups):
        o.vertex_groups.remove(g)
    print('REDUCE', n, tris, '->', sum(len(p.vertices) - 2 for p in o.data.polygons))
for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
body.data.materials.clear()
print('TRIS', sum(len(p.vertices) - 2 for p in body.data.polygons))
# the original positions, for the weight transfer from Meshy's rigged copy of the unmodified mesh (build_rig.py)
import numpy as np
me = body.data
orig = me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT')
co = np.array([tuple(v.co) for v in me.vertices]); orig.data.foreach_set('vector', co.ravel())
# G6: the loincloth's back flap (piece 6, behind the hips, below the belt) hangs ~4 cm off the body and the walk's
# swinging forearms pass 5 cm through it: pull it toward the body under it, to a 1.2 cm gap, with a smooth falloff
from mathutils.bvhtree import BVHTree
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
under = [p for p in me.polygons if pv[p.vertices[0]] in (0, 2)]
tree = BVHTree.FromPolygons([tuple(c) for c in co], [tuple(p.vertices) for p in under])
flap = np.where((pv == 6) & (co[:, 1] > 0.03) & (co[:, 2] < 0.97))[0]
if not os.environ.get('FLAP_SWING'):
    flap = flap[:0]          # off by default: the walk contact it was meant to fix was a G6 metric false positive
# swing the flap toward the body about a hinge on the belt line (X axis through its top), as far as it can go with
# every flap vertex >= 1 cm off the body (closest-point test); straight pulls kinked the tip (TEST_DRIVE.md)
if len(flap) == 0:
    me.vertices.foreach_set('co', co.ravel()); bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out)); raise SystemExit
top = co[flap][co[flap][:, 2] > co[flap][:, 2].max() - 0.02]
hinge = np.array([0.0, top[:, 1].mean(), top[:, 2].mean()])
def swung(theta):
    c_, s_ = np.cos(theta), np.sin(theta)
    r = co[flap] - hinge
    y = r[:, 1] * c_ + r[:, 2] * s_; z = -r[:, 1] * s_ + r[:, 2] * c_     # positive theta moves the lower flap forward
    return np.c_[co[flap][:, 0], hinge[1] + y, hinge[2] + z]
wbelt = np.clip((0.97 - co[flap][:, 2]) / 0.04, 0, 1)             # keep the belt edge in place
rest_gap = []
for p_ in co[flap]:
    loc, nrm, idx, dist = tree.find_nearest(p_.tolist(), 0.2)
    rest_gap.append(dist if loc is not None else 0.2)
rest_gap = np.array(rest_gap)
best = 0.0
for deg in np.arange(1, 40, 1.0):
    pts = co[flap] + (swung(np.radians(deg)) - co[flap]) * wbelt[:, None]; ok = True
    for p_, g0 in zip(pts, rest_gap):
        loc, nrm, idx, dist = tree.find_nearest(p_.tolist(), 0.05)
        if loc is not None and ((p_ - np.array(loc)) @ np.array(nrm) < 0 or dist < min(0.6 * g0, 0.008)):
            ok = False; break
    if not ok:
        if deg == 1:
            bad = [(round(float(g0) * 100, 2), round(float(p_[2]), 3)) for p_, g0 in zip(pts, rest_gap)
                   if (lambda r: r[0] is not None and ((p_ - np.array(r[0])) @ np.array(r[1]) < 0 or r[3] < min(0.6 * g0, 0.008)))(tree.find_nearest(p_.tolist(), 0.05))]
            print('FLAPDBG failing at 1 deg (rest gap cm, z):', bad[:8], 'count', len(bad))
        break
    best = deg
disp = np.zeros_like(co)
disp[flap] = swung(np.radians(best)) - co[flap]
disp[flap] *= wbelt[:, None]
print('FLAP hinge swing deg', best)
co += disp
me.vertices.foreach_set('co', co.ravel())
print('FLAP pulled', len(flap), 'vertices; mean move cm', round(float(np.linalg.norm(disp[flap], axis=1).mean()) * 100, 2),
      'max', round(float(np.linalg.norm(disp[flap], axis=1).max()) * 100, 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
