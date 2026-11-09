"""Clay and textured close-ups straight from GLBs (no weld: the file's own normals and materials). The Fly clip
starts 0.405 up, so spots follow bones. Usage: blender -b -P glb_close.py -- <label=glb,...> [spot,...]
-> review/glbclose/<label>_<spot>_<mode>.png"""
import os, sys, math, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'glbclose'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]
# (action, frame, bone, ortho size, view direction); the wyvern faces -Y
SPOTS = {'mouth_side': ('Attack', 20, 'Head', .11, (1, 0, .1)), 'mouth_q34': ('Attack', 20, 'Head', .11, (.6, -.8, .2)),
         'mouth_front': ('Attack', 20, 'Head', .09, (0, -1, .15)), 'mouth_low': ('Attack', 20, 'Head', .1, (.5, -.6, -.6)),
         'head_side': ('Fly', 0, 'Head', .11, (1, 0, .15)), 'head_top': ('Fly', 0, 'Head', .12, (.3, -.2, 1)),
         'neck_spikes': ('Fly', 0, 'Neck3', .2, (1, -.2, .3)), 'neck_spikes_l': ('Fly', 0, 'Neck3', .2, (-1, -.2, .3)),
         'back_spikes': ('Fly', 0, 'Spine2', .25, (1, 0, .35)), 'tail_spikes': ('Fly', 0, 'Tail4', .3, (1, 0, .5)),
         'whole': ('Fly', 0, 'Spine2', 1.15, (.8, -.8, .45)), 'wing_top': ('Fly', 0, 'Spine2', 1.15, (0, .1, 1)),
         'wing_under': ('Fly', 0, 'Spine2', 1.15, (0, .1, -1)), 'feet': ('Fly', 0, 'Shin_R', .14, (-.7, -.6, .1)),
         'eye_r': ('Fly', 0, 'Head', .045, (-1, -.15, .15)), 'eye_l': ('Fly', 0, 'Head', .045, (1, -.15, .15)),
         'gape_front': ('Attack', 20, 'Jaw', .07, (.15, -1, .35))}
if len(args) > 1:
    SPOTS = {k: SPOTS[k] for k in args[1].split(',')}
RES = int(os.environ.get('CLOSE_RES', '420'))
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb) if not os.path.isabs(glb) else glb)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.clip_end = 20; sc.render.resolution_x = sc.render.resolution_y = RES
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'
    sc.display.shading.single_color = (.8, .78, .74); sc.display.shading.show_cavity = False
    for spot, (act, frame, b, size, d) in SPOTS.items():
        a = next(x for x in bpy.data.actions if x.name.rsplit('|', 1)[-1] == act)
        rig.animation_data.action = a
        if a.slots:
            rig.animation_data.action_slot = a.slots[0]
        sc.frame_set(frame)
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = size
        for mode, eng in (('tex', 'BLENDER_EEVEE'), ('clay', 'BLENDER_WORKBENCH')):
            sc.render.engine = eng; sc.render.filepath = os.path.join(out, f'{label}_{spot}_{mode}.png')
            bpy.ops.render.render(write_still=True)
print('GLBCLOSE done')
