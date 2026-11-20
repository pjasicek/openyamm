"""Teeth rows on their own bones (Treant), so the disguise can hide them: work/rig_v3.blend -> work/rig_v4.blend.
With the mouth closed (Standing) the lip corners stay a little open, and the corner teeth showed. TeethU (child of
UpperLip) and TeethL (child of Jaw) sit at the middle of each row's gum line, 6 cm behind it; every upper tooth is
100 % TeethU, every lower tooth 100 % TeethL. anim_treant.py scales both rows to 0.35 when the mouth closes, which
draws the corner teeth in behind the lips. Args: none"""
import bpy, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v3.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
pa = np.zeros(len(co), np.int32); me.attributes['part'].data.foreach_get('value', pa)
heads = {}
for name, kind, parent in (('TeethU', 1, 'UpperLip'), ('TeethL', 2, 'Jaw')):
    c = co[pa == kind]
    gum = c[:, 2].max() if kind == 1 else c[:, 2].min()
    heads[name] = (Vector((0.0, float(np.median(c[:, 1])) + 0.06, float(gum))), kind, parent)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
for name, (h, kind, parent) in heads.items():
    b = rig.data.edit_bones.new(name); b.head = h; b.tail = h + Vector((0, -0.25, 0)); b.align_roll(Vector((0, 0, 1)))
    b.parent = rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
for name, (h, kind, parent) in heads.items():
    idx = [int(i) for i in np.nonzero(pa == kind)[0]]
    for g in body.vertex_groups:
        g.remove(idx)
    (body.vertex_groups.get(name) or body.vertex_groups.new(name=name)).add(idx, 1.0, 'REPLACE')
    print('TEETH bone', name, [round(x, 3) for x in h], 'verts', len(idx))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v4.blend'))
