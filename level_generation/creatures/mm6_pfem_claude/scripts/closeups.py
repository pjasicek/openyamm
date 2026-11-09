"""Close-up clay renders (wireframe overlay optional): head front/side and right hand. Args: tag."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
tag = sys.argv[sys.argv.index('--') + 1]
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name.startswith('Meshy') or o.name == 'BodyRef'
scene = bpy.context.scene
common.workbench_clay(scene)
scene.display.shading.color_type = 'SINGLE'
scene.display.shading.single_color = (0.75, 0.62, 0.55)
common.render_views(os.path.join(common.REVIEW, f'{tag}_face'), 1.46, 0.26, views=('front', 'left', 'three_quarter'), resolution=(500, 500))
rig = bpy.data.objects['Human.rig']
hand = rig.matrix_world @ rig.data.bones['mixamorig:RightHand'].head_local
common.render_views(os.path.join(common.REVIEW, f'{tag}_hand'), hand.z - 0.06, 0.22, views=('front', 'right'),
                    resolution=(400, 400), target=(hand.x, hand.y))
