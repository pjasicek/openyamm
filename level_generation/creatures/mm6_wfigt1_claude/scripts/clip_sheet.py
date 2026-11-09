"""Contact sheet of actions on the rig: N evenly spaced frames per action, three-quarter and side, frame numbers.
Args: blend out_prefix action[,action...] [N]"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
args = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, args[0]))
out, names = args[1], args[2].split(',')
N = int(args[3]) if len(args) > 3 else 8
arm = bpy.data.objects['Werewolf_Rig']
scene = bpy.context.scene
common.workbench_clay(scene)
scene.render.resolution_x, scene.render.resolution_y = 240, 320
cams = {}
for view, a in (('tq', 35.0), ('side', 90.0)):
    r = math.radians(a)
    cams[view] = common.ortho_camera('c' + view, (math.sin(r) * 6, -math.cos(r) * 6, 0.85), (math.radians(90), 0, r), 2.1)
paths = []
for n in names:
    act = bpy.data.actions[n]
    arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range
    for i in range(N):
        f = int(round(f0 + (f1 - f0) * i / (N - 1)))
        scene.frame_set(f)
        for view, cam in cams.items():
            scene.camera = cam
            p = os.path.join(common.REVIEW, 'tmp_%s_%s_%03d.png' % (n, view, f))
            scene.render.filepath = p
            bpy.ops.render.render(write_still=True)
            paths.append((n, view, i, f, p))
import json
json.dump(paths, open(os.path.join(common.REVIEW, 'tmp_sheet.json'), 'w'))
