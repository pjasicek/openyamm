import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'st1_parts.blend'))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name not in ('P01', 'P02', 'P00')
        o.show_wire = True
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, 'st1_tail'), 0.65, 0.75, views=('left', 'back'), resolution=(700, 700), target=(0, 0.1))
