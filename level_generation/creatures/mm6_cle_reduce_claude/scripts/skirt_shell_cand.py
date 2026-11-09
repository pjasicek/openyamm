"""Skirt lining onto the reduced candidate (../mm6_cle_claude/scripts/skirt_shell.py; user review 2026-10-14 (3)):
each candidate face (work/ladder.blend, REA_CAND) takes the label of the master surface under it at rest
(../mm6_cle_claude/work/skirt_faces.npz): the nearest master triangle when its normal agrees, else the first agreeing
surface along the face's normal (a ray from 1.5 cm out, inward). Nearest face centres mislabelled a third of the
reduced front panel (its large faces' centres lay nearer the body under the skirt). Then skirt_shell.apply pins the
lining. In place; build_pick.sh runs it before export_cand.py."""
import os, sys, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'mm6_cle_claude', 'scripts'))
import skirt_shell
path = os.path.join(HERE, 'work', 'ladder.blend')
bpy.ops.wm.open_mainfile(filepath=path)
rig = bpy.data.objects['Rig']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_55')]
M = np.load(os.path.join(HERE, '..', 'mm6_cle_claude', 'work', 'skirt_faces.npz'))
V = [Vector(v) for v in M['verts']]
bvh = BVHTree.FromPolygons(V, [tuple(int(i) for i in t) for t in M['tris']])
poly = M['tri_poly']; label = M['label']
mw = cand.matrix_world


def master_label(c, n):
    loc, nrm, ti, d = bvh.find_nearest(c)
    if ti is not None and d < 0.02 and nrm.dot(n) > 0.3:
        return int(label[poly[ti]])
    o = c + n * 0.015
    for _ in range(4):                               # along the normal, inward, skipping disagreeing layers
        hit, nrm, ti, d = bvh.ray_cast(o, -n, 0.05)
        if hit is None:
            return None
        if nrm.dot(n) > 0.3:
            return int(label[poly[ti]])
        o = hit - n * 1e-4
    return None


skirt, inner, none = set(), [], 0
for p in cand.data.polygons:
    lab = master_label(mw @ p.center, (mw.to_3x3() @ p.normal).normalized())
    if lab is None:
        none += 1
    elif lab:
        skirt.add(p.index)
        if lab == 2:
            inner.append(p.index)
rep = skirt_shell.apply(cand, skirt, inner, {b.name for b in rig.data.bones if b.use_deform})
# the lining faces go, as at the master's export (export_runtime.py): the double-sided outside shows its own back
# and the exact inner copy of the outside replaces it (skirt_shell.add_inside, the dark inside swatch)
import bmesh, json
bm = bmesh.new(); bm.from_mesh(cand.data); bm.faces.ensure_lookup_table()
drop = set(inner)
SWL = json.load(open(os.path.join(HERE, '..', 'mm6_cle_claude', 'textures', 'cle_staff_swatches.json')))['lining']
ins = set(skirt_shell.add_inside(bm, [f for f in bm.faces if f.index in skirt - drop], bm.loops.layers.uv.active,
                                 (SWL[0], SWL[1])))
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f not in ins and f.index in drop], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(cand.data); bm.free()
print('SKIRT_SHELL_CAND', cand.name, len(skirt), 'skirt faces,', len(inner), 'lining (removed), inside copy', len(ins),
      'unlabelled', none, rep)
bpy.ops.wm.save_mainfile(filepath=path)
