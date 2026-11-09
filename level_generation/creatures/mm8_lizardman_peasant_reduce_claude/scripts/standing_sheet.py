"""Standing v2 review renders straight from viewer GLBs (textured EEVEE): whole body front / three-quarter / side /
back at several clip times, and arm close-ups. Usage: blender -b -P standing_sheet.py -- <label=glb,...> <times,> [views,]
-> review/standing_v2/<label>_<view>_<t>.png"""
import os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'standing_v2'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]; times = [float(t) for t in args[1].split(',')]
VIEWS = {'front': ('Spine02', 1.95, (0, -1, .08)), 'q34': ('Spine02', 1.95, (.75, -.65, .1)),
         'side': ('Spine02', 1.95, (1, 0, .05)), 'back': ('Spine02', 1.95, (0, 1, .08)),
         'rq34': ('Spine02', 1.95, (-.75, -.65, .1)), 'rback34': ('Spine02', 1.95, (-.7, .7, .1)),
         'arm_r': ('RightForeArm', .85, (-1, -.2, .1)), 'arm_r34': ('RightForeArm', .85, (-.75, -.7, .2)),
         'arm_l': ('LeftForeArm', .85, (1, -.2, .1))}
only = args[2].split(',') if len(args) > 2 else None
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:
        if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
            o.hide_render = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = 420; sc.render.resolution_y = 460
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'; sc.render.engine = 'BLENDER_EEVEE'
    act = bpy.data.actions['Standing']; rig.animation_data.action = act
    if act.slots:
        rig.animation_data.action_slot = act.slots[0]
    fps = sc.render.fps / sc.render.fps_base; end = act.frame_range[1] / fps
    for t in times:
        tt = min(t, end); f = tt * fps; sc.frame_set(int(f), subframe=f % 1)
        for v, (b, size, d) in VIEWS.items():
            if only and v not in only:
                continue
            pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2) if b != 'Spine02' else Vector((0, 0, .88))
            if v.startswith('arm'):
                c = rig.matrix_world @ rig.pose.bones[b].head
            cam.location = c + Vector(d).normalized() * 3; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = size; sc.render.filepath = os.path.join(out, f'{label}_{v}_{t:.2f}.png')
            bpy.ops.render.render(write_still=True)
print('STANDING_SHEET done', end)
