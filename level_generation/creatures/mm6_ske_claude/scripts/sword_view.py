"""Sword + hand side view in the rest grip. Args: -- <blend> <out png>"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
blend, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
scene = bpy.context.scene; common.workbench_clay(scene); scene.display.shading.color_type = 'MATERIAL'
scene.render.resolution_x, scene.render.resolution_y = 900, 900
cam = common.ortho_camera('c', (-2.0, -0.25, 0.85), (math.radians(90), 0, math.radians(-90)), 0.9)
scene.camera = cam; scene.render.filepath = out
bpy.ops.render.render(write_still=True)
