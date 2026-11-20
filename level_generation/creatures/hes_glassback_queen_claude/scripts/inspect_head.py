"""Rest-pose measurements of the Glassback head for the crown layout. Args: -- <blend>"""
import bpy, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
src = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
for b in ('Spine3', 'Neck1', 'Head', 'Socket_Beak'):
    pb = rig.pose.bones.get(b)
    if pb:
        print('BONE', b, [round(x, 3) for x in rig.matrix_world @ pb.head], [round(x, 3) for x in rig.matrix_world @ pb.tail])
names = {g.index: g.name for g in body.vertex_groups}
co = np.array([body.matrix_world @ v.co for v in body.data.vertices])
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] if v.groups else '' for v in body.data.vertices])
for b in ('Head', 'Neck1'):
    p = co[dom == b]
    print('VERTS', b, len(p), 'min', p.min(0).round(3), 'max', p.max(0).round(3))
p = co[dom == 'Head']
for y in np.arange(p[:, 1].min(), p[:, 1].max(), 0.05):
    s = p[(p[:, 1] >= y) & (p[:, 1] < y + 0.05)]
    if len(s):
        print('SLICE y %.2f zmax %.3f xhalf %.3f zmin %.3f' % (y, s[:, 2].max(), np.abs(s[:, 0]).max(), s[:, 2].min()))
print('OBJECTS', [(o.name, o.type, o.parent_bone if o.parent_type == 'BONE' else '') for o in bpy.data.objects][:60])
