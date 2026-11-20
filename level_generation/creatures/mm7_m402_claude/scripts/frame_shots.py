"""Clay renders of chosen frames of one action from front, side and three-quarter (orthographic, 3.4 m frame).
Args: -- <blend> <out prefix> <action> <frame> [frame ...]"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, act = a[0], a[1], a[2]; frames = [float(x) for x in a[3:]]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; common.workbench_clay(scene)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear()
scene.render.resolution_x = scene.render.resolution_y = 400
cams = {'front': ((0, -8, float(os.environ.get('CZ', '1.1'))), (math.radians(90), 0, 0)), 'side': ((8, 0, float(os.environ.get('CZ', '1.1'))), (math.radians(90), 0, math.radians(90))),
        'tq': ((5.66, -5.66, float(os.environ.get('CZ', '1.1'))), (math.radians(90), 0, math.radians(45)))}
A = bpy.data.actions[act]; rig.animation_data_create(); rig.animation_data.action = A
if len(A.slots): rig.animation_data.action_slot = A.slots[0]
for f in frames:
    scene.frame_set(int(f), subframe=f - int(f))
    for v, (loc, rot) in cams.items():
        cam = common.ortho_camera('c', loc, rot, float(os.environ.get('OS', '3.4'))); scene.camera = cam
        scene.render.filepath = f'{out}_{act}_{int(f)}_{v}.png'; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
