"""Textured review render of the props in work/props.blend (front = bow plane, side, arrow). Args: -- <out prefix>"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'props.blend'))
scene = bpy.context.scene; common.workbench_clay(scene, textured=True)
objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in objs:
    o.rotation_euler = (math.radians(90), 0, 0)              # prop +Y (up the bow) -> world +Z
for name, rot in (('plane', (math.radians(90), 0, 0)), ('edge', (math.radians(90), 0, math.radians(90)))):
    cam = common.ortho_camera('c', (0, -3, 0.25) if name == 'plane' else (3, 0, 0.25), rot, float(os.environ.get('ORTHO', '2.2')))
    scene.camera = cam; scene.render.resolution_x, scene.render.resolution_y = 500, 800
    scene.render.filepath = f'{out}_{name}.png'; bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)
