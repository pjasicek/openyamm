"""Close-up renders of the head parts of a parts blend: all parts, and with chosen parts hidden. Args: tag hide..."""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
tag, hide = args[0], args[1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, f'{tag}_parts.blend'))
for o in bpy.data.objects:
    if o.name in hide:
        o.hide_render = True
    if o.type == 'MESH':
        o.show_wire = False
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, f'{tag}_headx_{"_".join(hide) or "all"}'), 1.43, 0.32,
                    views=('front', 'three_quarter', 'left'), resolution=(500, 500))
