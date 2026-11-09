"""Print the bow-related bones (parents, rest positions in the Bow bone frame) and the bow attachment mesh extents in
its own frame. Usage: blender -b -P bow_probe.py -- <master.blend>"""
import bpy, sys
from mathutils import Vector
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
rig = bpy.data.objects['Rig']; bones = rig.data.bones
B = bones['Bow'].matrix_local
for n in ('Bow', 'StringNock', 'StringTop', 'StringBottom', 'Arrow', 'LHand', 'Quiver'):
    if n in bones:
        b = bones[n]; h = B.inverted() @ b.head_local; t = B.inverted() @ b.tail_local
        print('BONE', n, 'parent', b.parent.name if b.parent else None, 'head_in_bow', [round(x, 3) for x in h],
              'tail_in_bow', [round(x, 3) for x in t])
for o in bpy.data.objects:
    if o.type == 'MESH':
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        print('MESH', o.name, len(vs), 'parent', o.parent.name if o.parent else None, o.parent_bone,
              'groups', [g.name for g in o.vertex_groups][:6] if len(o.vertex_groups) < 8 else len(o.vertex_groups))
        if 'bow' in o.name.lower() or 'string' in o.name.lower():
            loc = [B.inverted() @ v for v in vs]
            print('  extents_in_bow_frame', [(round(min(p[i] for p in loc), 3), round(max(p[i] for p in loc), 3)) for i in range(3)])
