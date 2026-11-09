"""Clay review renders of an assembly: 4 views full body + head close-ups. Args: blend tag [color_type]."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
tag = args[0]; color = args[1] if len(args) > 1 else 'RANDOM'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.hide_render = o.name.startswith('Meshy') or o.name in ('BodyRef',) or o.name.startswith('cam')
scene = bpy.context.scene
common.workbench_clay(scene, textured=(color == 'TEXTURE'))
if color != 'TEXTURE':
    scene.display.shading.color_type = color
common.render_views(os.path.join(common.REVIEW, f'{tag}'), 0.8, 1.7, resolution=(700, 700))
common.render_views(os.path.join(common.REVIEW, f'{tag}_head'), 1.42, 0.42, views=('front', 'left', 'back', 'three_quarter'),
                    resolution=(500, 500))
