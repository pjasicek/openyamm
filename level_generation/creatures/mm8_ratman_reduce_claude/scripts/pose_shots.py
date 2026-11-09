"""Whole-body side / three-quarter shots straight from GLBs (own normals, LOD0 only) at given clip frames, for the
head/shoulder review. Usage: blender -b -P pose_shots.py -- <label=glb,...> <clip:frame,...> [out dir]
-> <out>/<label>_<clip><frame>_<view>.png (rest pose: clip 'rest'). Frames are Blender's 24 fps scene frames unless
POSE_FPS gives the rate they count in (48 for the engine viewer's frame numbers)."""
import math, os, sys, bpy
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(HERE, args[2] if len(args) > 2 else 'review/head_fix'); os.makedirs(out, exist_ok=True)
VIEWS = {'side': ((1, 0, .05), 1.9), 'q34': ((.7, -.7, .2), 1.9), 'shoulder': ((.75, -.45, .35), .75), 'front': ((0, -1, .05), 1.9),
         'rside': ((-1, 0, .05), 1.9), 'rshoulder': ((-.75, -.45, .35), .75), 'rback': ((-.6, .7, .3), .75),
         'rarm': ((-1, -.15, .1), .5), 'rarm_low': ((-.8, -.4, -.35), .5), 'larm': ((1, -.15, .1), .5),
         'rarm_front': ((-.3, -1, .1), .5), 'rarm_wide': ((-1, -.25, .25), .8),
         'neck_low': ((.25, -1, -.6), .7), 'neck_back': ((.3, 1, .35), .7),
         'throat_front': ((.35, -1, -.15), .42), 'throat_below': ((.2, -.6, -1), .42), 'throat_q34': ((-.75, -.7, -.1), .42),
         'head_fr': ((-.55, -1, .45), .6), 'head_fl': ((.55, -1, .45), .6), 'head_back': ((.4, 1, .6), .6), 'head_top': ((0, -.3, 1), .6),
         'legs_front': ((.2, -1, .1), 1.0), 'legs_back': ((-.3, 1, .1), 1.0), 'legs_side': ((1, -.2, .05), 1.0)}
VIEWS = {k: VIEWS[k] for k in os.environ.get('POSE_VIEWS', ','.join(VIEWS)).split(',')}
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb) if not os.path.isabs(glb) else glb)
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    for o in bpy.data.objects:
        if o.type == 'MESH' and o.name != 'Ratman':
            o.hide_render = True
    if os.environ.get('POSE_HIDE_HEAD'):  # drop the head texture set (right half of the atlas) to see the shoulders
        import bmesh
        body = bpy.data.objects['Ratman']; bm = bmesh.new(); bm.from_mesh(body.data); uvl = bm.loops.layers.uv.active
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if sum(l[uvl].uv[0] for l in f.loops) / 3 > 1056 / 2080], context='FACES')
        bm.to_mesh(body.data); bm.free()
    if os.environ.get('POSE_CULL'):  # the engine back-face-culls creature triangles; inverted or inside faces show as holes
        for m in bpy.data.materials:
            m.use_backface_culling = True
        sc.display.shading.show_backface_culling = True
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 480
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.33, .34, .37, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.render.engine = os.environ.get('POSE_ENGINE', 'BLENDER_EEVEE')
    sc.display.shading.light = 'STUDIO'; sc.display.shading.color_type = 'SINGLE'; sc.display.shading.single_color = (.8, .78, .74)
    for cf in args[1].split(','):
        clip, frame = cf.split(':')
        if clip == 'rest':
            rig.animation_data.action = None
            for b in rig.pose.bones:
                b.matrix_basis.identity()
        else:
            rig.animation_data.action = bpy.data.actions[clip]
        f = float(frame) * sc.render.fps / float(os.environ.get('POSE_FPS', sc.render.fps))
        sc.frame_set(int(f), subframe=f - int(f)); bpy.context.view_layer.update()
        for view, (d, size) in VIEWS.items():
            bn = 'B_Pelvis' if view.startswith('legs') else 'B_R_UpperArm' if view.startswith('rarm') else 'B_L_UpperArm' if view == 'larm' else 'B_Head' if view.startswith('head') else 'B_Neck' if view.startswith('neck') or view.startswith('throat') else 'B_Spine2' if 'shoulder' in view or view == 'rback' else 'B_Spine'; b = rig.pose.bones[bn]
            c = (rig.matrix_world @ ((b.head + b.tail) / 2) if view.startswith('throat') else rig.matrix_world @ b.head) + (Vector((0, 0, .2)) if 'shoulder' in view or view == 'rback' else Vector((0, 0, -.38)) if view.startswith('legs') else Vector((0, 0, 0)))
            cam.location = c + Vector(d).normalized() * 4; cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
            cam.data.ortho_scale = size; cam.data.clip_end = 10
            sc.render.filepath = os.path.join(out, f'{label}_{clip}{frame}_{view}{os.environ.get("POSE_SUFFIX", "")}.png'); bpy.ops.render.render(write_still=True)
print('POSESHOTS done')
