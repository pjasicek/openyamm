"""Wrist close-ups framed in the forearm's own frame (fix 2026-11-02: the vambrace rim and the glove top). Camera
directions: f = forearm axis (elbow -> wrist), o = outward (body centre -> wrist, perpendicular to f), b = f x o.
Views: above (-f+0.45o: down the arm onto the rim), downb (-f+0.6b), downf (-f-0.6b), abovein (-f-0.45o), below (f+0.35o: from the hand up into the
vambrace), out (o), in (-o), back (b), front (-b). Args: <glb> <out prefix> <spec> ...  spec = name:clip:seconds:side
(L|R); env TEX=1 for textures, SIZE px, ORTHO metres, VIEWS comma list."""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'
sh.color_type = 'SINGLE' if not os.environ.get('TEX') else 'TEXTURE'
sh.single_color = (.72, .7, .62); sh.show_cavity = False; sh.show_backface_culling = True
sc.render.resolution_x = sc.render.resolution_y = int(os.environ.get('SIZE', 360))
sc.world = bpy.data.worlds.new('W'); sc.world.color = (0.5, 0.05, 0.4); sh.background_type = 'WORLD'
cd = bpy.data.cameras.new('C'); cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.type = 'ORTHO'; cd.clip_end = 30; cd.ortho_scale = float(os.environ.get('ORTHO', 0.22))
VIEWS = os.environ.get('VIEWS', 'above,abovein,below,out,in,back,front').split(',')
for sp in a[2:]:
    n, clip, t, side = sp.split(':')
    act = next(x for x in bpy.data.actions if x.name == clip or x.name.startswith(clip))
    rig.animation_data_create(); rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    fr = float(t) * 24.0
    sc.frame_set(int(fr), subframe=fr % 1.0); bpy.context.view_layer.update()
    pb = rig.pose.bones
    el = rig.matrix_world @ pb[f'Bip01 {side} Forearm'].head; wr = rig.matrix_world @ pb[f'Bip01 {side} Hand'].head
    sp3 = rig.matrix_world @ pb['Bip01 Spine2'].head
    f = (wr - el).normalized(); o = wr - sp3; o = (o - f * o.dot(f)).normalized(); b = f.cross(o)
    D = {'downb': -f + 0.6 * b, 'downf': -f - 0.6 * b, 'above': -f + 0.45 * o, 'abovein': -f - 0.45 * o, 'below': f + 0.35 * o, 'out': o, 'in': -o, 'back': b, 'front': -b}
    c = wr + f * 0.01
    for v in VIEWS:
        d = D[v].normalized()
        cam.location = c + d * 3; cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{a[1]}_{n}_{v}.png'; bpy.ops.render.render(write_still=True)
print('WRIST done')
