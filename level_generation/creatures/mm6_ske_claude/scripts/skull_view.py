"""Skull turnaround renders of a parts blend. Args: -- <blend> <tag>"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, tag = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
common.render_views(os.path.join(common.REVIEW, tag), 0.79, 1.75, views=('front', 'three_quarter', 'left', 'back'),
                    resolution=(500, 500))
