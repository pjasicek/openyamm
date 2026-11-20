"""Clay + wire review renders of a work blend. Args: blend tag [wire 0/1]."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag, wire = (sys.argv[sys.argv.index('--') + 1:] + ['1'])[:3]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; common.workbench_clay(sc); sc.display.shading.color_type = 'SINGLE'
sc.display.shading.single_color = (0.72, 0.72, 0.7)
for o in bpy.data.objects:
    if o.type == 'MESH': o.show_wire = wire == '1'
R = lambda n: os.path.join(common.REVIEW, f'{tag}_{n}')
common.render_views(R('full'), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
common.render_views(R('head'), 1.43, 0.36, views=('front', 'three_quarter', 'left', 'back'), resolution=(500, 500))
common.render_views(R('waist'), 0.84, 0.36, views=('front', 'left', 'back'), resolution=(500, 500))
common.render_views(R('handR'), 0.82, 0.16, views=('front', 'right', 'back'), resolution=(400, 400), target=(-0.43, -0.02))
common.render_views(R('handL'), 0.81, 0.16, views=('front', 'left', 'back'), resolution=(400, 400), target=(0.43, -0.02))
common.render_views(R('feet'), 0.25, 0.55, views=('front', 'left'), resolution=(500, 500))
