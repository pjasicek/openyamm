"""Close-up clay renders of clip frames. Args: blend out_tag clip:frame[,clip:frame...] view[,view] cx,cy,cz scale"""
import bpy, os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
tag, frames, views = a[1], [x.split(':') for x in a[2].split(',')], a[3].split(',')
c = [float(x) for x in a[4].split(',')]; scale = float(a[5])
arm = bpy.data.objects['Werewolf_Rig']; scene = bpy.context.scene
common.workbench_clay(scene)
scene.render.resolution_x = scene.render.resolution_y = 420
ANG = {'front': 0, 'tq': 35, 'side': 90, 'back': 180, 'tqr': -35, 'rside': -90}
tiles = []
for clip, f in frames:
    act = bpy.data.actions[clip]; arm.animation_data.action = act
    if getattr(act, 'slots', None):
        arm.animation_data.action_slot = act.slots[0]
    scene.frame_set(int(f))
    # follow the Spine bone
    hb = arm.matrix_world @ arm.pose.bones['Spine'].head
    tgt = (c[0] + hb.x, c[1] + hb.y, c[2] + hb.z) if a[4].startswith('rel') is False and len(c) == 3 else c
    for v in views:
        r = math.radians(ANG[v])
        cam = common.ortho_camera('c', (tgt[0] + math.sin(r) * 5, tgt[1] - math.cos(r) * 5, tgt[2]), (math.radians(90), 0, r), scale)
        scene.camera = cam
        p = os.path.join(common.REVIEW, 'tmpf_%s_%s_%s.png' % (clip, f, v))
        scene.render.filepath = p; bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
        tiles.append((clip + ' ' + f + ' ' + v, p))
import json
json.dump({'tag': tag, 'tiles': tiles}, open(os.path.join(common.REVIEW, 'tmpf_%s.json' % tag), 'w'))
