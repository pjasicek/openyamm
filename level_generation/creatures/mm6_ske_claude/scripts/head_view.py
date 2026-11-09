"""Head close-up (front, three-quarter, left) of a rig blend. Args: -- <blend> <tag>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, tag + '_head'), 1.42, 0.42, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(450, 450))
common.render_views(os.path.join(common.REVIEW, tag + '_full'), 0.82, 1.75, views=('front', 'three_quarter', 'left'),
                    resolution=(400, 800))
