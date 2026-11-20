"""Close-ups of a parts blend: head front/left, right/left hand front/side. Args: -- <blend> <tag>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
out = os.path.join(common.REVIEW, tag)
common.render_views(out + '_head', 1.55, 0.36, views=('front', 'left'), resolution=(450, 450))
common.render_views(out + '_rhand', 0.86, 0.3, views=('front', 'right'), resolution=(450, 450), target=(-0.40, -0.02))
common.render_views(out + '_lhand', 0.86, 0.3, views=('front', 'left'), resolution=(450, 450), target=(0.40, -0.02))
