"""Clay turnaround + head close-up of a work blend. Args: blend tag [wire 0/1]"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
wire = len(a) > 2 and a[2] == '1'
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.show_wire = wire
sc = bpy.context.scene
common.workbench_clay(sc)
sc.display.shading.color_type = 'SINGLE'
common.render_views(os.path.join(common.REVIEW, a[1]), 0.8, 1.7, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(600, 900))
common.render_views(os.path.join(common.REVIEW, a[1] + '_head'), 1.42, 0.36, views=('front', 'three_quarter'),
                    resolution=(500, 500))
for side, x in (('hand_l', 0.27), ('hand_r', -0.27)):
    common.render_views(os.path.join(common.REVIEW, a[1] + '_' + side), 0.88, 0.26, views=('front', 'left', 'right'),
                        resolution=(400, 400), target=(x, -0.05))
