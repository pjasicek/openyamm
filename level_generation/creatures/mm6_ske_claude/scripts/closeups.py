"""Close-up clay renders of a parts blend. Args: -- <blend> <tag>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
out = os.path.join(common.REVIEW, tag)
common.render_views(out + '_rhand', 0.8, 0.32, views=('front', 'left'), resolution=(500, 500), target=(-0.42, 0.0))
common.render_views(out + '_lhand', 0.8, 0.32, views=('front', 'right'), resolution=(500, 500), target=(0.42, 0.0))
common.render_views(out + '_feet', 0.08, 0.3, views=('front', 'left'), resolution=(900, 500), target=(0.0, 0.0))
common.render_views(out + '_pelvis', 0.95, 0.55, views=('front', 'left', 'back'), resolution=(500, 500))
