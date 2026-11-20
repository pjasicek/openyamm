"""Candidate attack preview on the cutpurse body with the knife: N evenly spaced frames per action, front (party eye
height, 2.5 m) and side cameras, EEVEE -> review/attack/<action>_<cam>.png frames (_<action>_<cam>_NN.png, stitched by strip.py); prints the knife tip path
(Socket_Knife_Tip: forward reach -Y, height, lateral) and the right-hand/knife relation.
Args: -- <blend> <frames per clip> action [action ...]"""
import bpy, os, sys, math
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
blend, N, acts = a[0], int(a[1]), a[2:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = os.path.join(HERE, 'review', 'attack'); os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']
print('OBJS', [(o.name, o.type, o.parent.name if o.parent else None, o.parent_bone) for o in bpy.data.objects])
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 360, 480
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True
next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND').inputs[0].default_value = (0.5, 0.52, 0.56, 1)
sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN')); sc.collection.objects.link(sun); sun.data.energy = 3.5
sun.rotation_euler = (0.8, 0.1, 0.5)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 40
CAMS = {'front': Vector((0.25, -2.6, 1.55)), 'side': Vector((2.6, -0.3, 1.2))}
tip = lambda: rig.matrix_world @ rig.pose.bones['Socket_Knife_Tip'].head
for an in acts:
    act = bpy.data.actions[an]; rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = act.frame_range; frames = [f0 + (f1 - f0) * i / (N - 1) for i in range(N)]
    path = []
    for f in range(int(f0), int(f1) + 1):
        sc.frame_set(f); t = tip(); path.append((f, -t.y, t.z, t.x))
    best = max(path, key=lambda p: p[1])
    print(f'TIP {an} frames {int(f1 - f0) + 1}: max forward {best[1]:.2f} m at f{best[0]} height {best[2]:.2f} lateral {best[3]:.2f}; '
          f'start fwd {path[0][1]:.2f} h {path[0][2]:.2f}; min height {min(p[2] for p in path):.2f}')
    for cn, cp in CAMS.items():
        for i, f in enumerate(frames):
            sc.frame_set(int(round(f)))
            cam.location = cp; cam.rotation_euler = (Vector((0, 0, 1.0)) - cp).to_track_quat('-Z', 'Y').to_euler()
            sc.render.filepath = os.path.join(OUT, f'_{an}_{cn}_{i:02d}.png'); bpy.ops.render.render(write_still=True)
