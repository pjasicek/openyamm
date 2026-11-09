"""Clay renders of the rest pose: full body (front, three-quarter) and close-ups of the skull and the left claw.
Args: -- <blend> <out prefix>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
sc = bpy.context.scene; common.workbench_clay(sc)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = True
common.render_views(a[1], 0.95, 1.95, views=('front', 'three_quarter'), resolution=(700, 800))
common.render_views(a[1] + '_skull', 1.66, 0.35, views=('front', 'three_quarter'), resolution=(500, 500))
common.render_views(a[1] + '_claw', 1.2, 0.3, views=('front', 'left'), resolution=(500, 500), target=(0.68, 0))
