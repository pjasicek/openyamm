"""Before/after review renders for the 2026-10-30 rework, from an exported GLB (textured, Workbench, flat grey ground).
The same cameras for every input: wing root from the side and the back in the bind pose and at both flap extremes
(the frames of all clips where the XwingD tips are lowest / highest relative to XspineC), close-ups of the three
heads, and the right shoulder / upper arm and arm head as in the user's screenshot 24.png.
Args: <glb> <out dir> <prefix> [size]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT, PRE = a[:3]
SIZE = int(a[3]) if len(a) > 3 else 720
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)
sc = bpy.context.scene
rig = next(o for o in sc.objects if o.type == 'ARMATURE')
rig.animation_data_create()
for tr in rig.animation_data.nla_tracks:     # the glTF import may stack clips as NLA tracks
    tr.mute = True
M = rig.matrix_world


def rest():
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.matrix_basis.identity()
    bpy.context.view_layer.update()


def metric():
    sp = M @ rig.pose.bones['XspineC'].head
    return sum((M @ rig.pose.bones[n].head).z - sp.z for n in ('XwingD', 'XwingD01')) / 2


ext = []
for act in bpy.data.actions:
    if act.name.split('.')[0] in ('Dead',):
        continue
    rig.animation_data.action = act
    f0, f1 = (int(x) for x in act.frame_range)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ext.append((metric(), act.name, f))
ext.sort()
poses = {'bind': None, 'flapdown': ext[0][1:], 'flapup': ext[-1][1:]}
print('POSES', poses)
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'; sh.show_backface_culling = False
sc.render.resolution_x = sc.render.resolution_y = SIZE
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.36, 0.37, 0.4)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam


def shot(name, centre, direction, scale):
    cd.ortho_scale = scale
    d = Vector(direction).normalized()
    cam.location = centre + d * 12
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(OUT, f'{PRE}_{name}.png')
    bpy.ops.render.render(write_still=True)


J = lambda n: M @ rig.pose.bones[n].head
for pn, pose in poses.items():
    rest()
    if pose:
        rig.animation_data.action = bpy.data.actions[pose[0]]
        sc.frame_set(pose[1])
        bpy.context.view_layer.update()
    c = J('XspineC') + Vector((0, 0.45, 0.25))
    shot(f'wing_{pn}_side', c, (1, 0.05, 0.08), 4.8)
    shot(f'wing_{pn}_back', c, (0.08, 1, 0.25), 4.8)
rest()
shot('head_main_front', J('Xhead') * 0.5 + J('Xhjaw') * 0.5 + Vector((0, -0.05, 0.1)), (0, -1, 0.15), 1.6)
shot('head_main_q34', J('Xhead') * 0.5 + J('Xhjaw') * 0.5 + Vector((0, -0.05, 0.1)), (-0.75, -1, 0.3), 1.6)
shot('head_armL_q34', (J('Xahead01') + J('Xatongue01')) / 2 + Vector((0, 0, 0.05)), (0.75, -1, 0.35), 1.1)
shot('head_armR_q34', (J('Xahead') + J('Xatongue')) / 2 + Vector((0, 0, 0.05)), (-0.75, -1, 0.35), 1.1)
# the user's 24.png: creature's right shoulder hump, upper arm and arm head, from its right front, slightly above
shot('shoulder_R', J('Xarm') * 0.5 + J('Xaelbow') * 0.5 + Vector((0, -0.2, 0.05)), (-0.45, -1, 0.3), 1.9)
shot('upper_body', J('XspineC') + Vector((0, -0.4, -0.3)), (-0.35, -1, 0.15), 3.0)
print('REVIEW', PRE)
