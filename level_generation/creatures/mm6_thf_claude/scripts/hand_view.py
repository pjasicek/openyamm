import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
for o in bpy.data.objects:
    if o.type == 'MESH': o.show_wire = True
for sd, x in (('R', -0.245), ('L', 0.24)):
    for v in ('front', 'left', 'right', 'back'):
        common.render_views(os.path.join(common.REVIEW, 'hand_' + sd), 0.78, 0.2, views=(v,), resolution=(400, 400),
                            target=(x, -0.06))
