"""Clay renders of the posed rig: per action N evenly spaced frames from front and side (orthographic, fixed framing),
written as <out_dir>/<action>_<k>_<view>.png; compose with compose_sheet.py. Args: -- <blend> <out_dir> <n> <action...>"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
blend, out, n = a[0], a[1], int(a[2]); acts = a[3:]
os.makedirs(out, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; scene = bpy.context.scene; common.workbench_clay(scene)
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.data.materials.clear()
scene.render.resolution_x, scene.render.resolution_y = 320, 320
cams = {'front': ((0, -8, 1.1), (math.radians(90), 0, 0)), 'side': ((8, 0, 1.1), (math.radians(90), 0, math.radians(90)))}
objs = {}
for v, (loc, rot) in cams.items():
    objs[v] = common.ortho_camera('cam_' + v, loc, rot, 3.4)
rig.animation_data_create()
for act in acts:
    A = bpy.data.actions[act]; rig.animation_data.action = A
    if len(A.slots): rig.animation_data.action_slot = A.slots[0]
    f0, f1 = A.frame_range
    for k in range(n):
        f = f0 + (f1 - f0) * k / max(n - 1, 1)
        scene.frame_set(int(f), subframe=f - int(f))
        for v, cam in objs.items():
            scene.camera = cam; scene.render.filepath = os.path.join(out, f'{act}_{k}_{v}.png')
            bpy.ops.render.render(write_still=True)
    print('POSES', act, 'frames', int(f1 - f0) + 1)
