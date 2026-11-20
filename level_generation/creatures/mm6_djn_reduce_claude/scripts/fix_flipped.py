"""Flipped faces of a texture-aware candidate (djn r62: a black shard under the goatee): a candidate face whose normal
points against the nearest source face's normal (dot < -0.3) is reversed. In/out: work/ladder.blend
(REA_CAND, default Cand_62). Usage: blender -b -P fix_flipped.py"""
import os
import bmesh
import bpy
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; cand = bpy.data.objects[os.environ.get('REA_CAND', 'Cand_62')]
sb = bmesh.new(); sb.from_mesh(src.data); sb.faces.ensure_lookup_table(); tree = BVHTree.FromBMesh(sb)
cb = bmesh.new(); cb.from_mesh(cand.data); cb.faces.ensure_lookup_table()
flip = []
for f in cb.faces:
    loc, n, i, d = tree.find_nearest(f.calc_center_median())
    if i is not None and f.normal.dot(sb.faces[i].normal) < -.3 and d < .01:
        flip.append(f)
print('FLIPPED', len(flip), [tuple(round(x, 3) for x in f.calc_center_median()) for f in flip if f.calc_center_median().z > 1.55])
if flip and os.environ.get('FF_APPLY') == '1':
    bmesh.ops.reverse_faces(cb, faces=flip)
    cb.to_mesh(cand.data); cand.data.update()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
