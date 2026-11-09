"""Review renders of a parts blend (work/<tag>_parts.blend): whole creature incl. the tail (ortho 2.1 m), head and
hand close-ups. Args: -- <blend> <out prefix>"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, pre = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
for o in bpy.data.objects:
    if o.type == 'MESH': o.show_wire = False
common.render_views(pre + '_all', 0.85, 2.2, views=('front', 'three_quarter', 'left', 'back', 'right'), resolution=(700, 880), target=(0, 0.2))
common.render_views(pre + '_head', 1.45, 0.45, views=('front', 'three_quarter', 'left'), resolution=(500, 500), target=(0, -0.6))
common.render_views(pre + '_handR', 0.55, 0.7, views=('front', 'right'), resolution=(500, 500), target=(-0.45, -0.5))
