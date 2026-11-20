"""Lesson from the m412 temple hole: renders of the body skin with the covering pieces hidden (wrap skirt, rope belt,
wrist bands: every loose piece but the largest), magenta background so holes show. Straight from GLBs.
Usage: blender -b -P hidden_skin.py -- <label=glb,...> [lod suffix, '' for LOD0]  -> review/hidden/<label>_<spot>.png"""
import os, sys, bpy, bmesh
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = os.path.join(HERE, 'review', 'hidden'); os.makedirs(out, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:]; LOD = args[1] if len(args) > 1 else ''
SPOTS = {'waist_front': ('Standing', 0, 'B_Pelvis', .8, (0, -1, .05)), 'waist_back': ('Standing', 0, 'B_Pelvis', .8, (0, 1, .05)),
         'waist_left': ('Standing', 0, 'B_Pelvis', .8, (1, 0, .05)), 'waist_below': ('Standing', 0, 'B_Pelvis', .8, (0, -.6, -.8)),
         'run_waist': ('Running', 8, 'B_Pelvis', .9, (.7, -.7, 0)), 'wrist_r': ('Standing', 0, 'B_R_ForearmTwist', .3, (-.6, -.8, .1)),
         'wrist_l_in': ('Standing', 0, 'B_L_ForearmTwist', .3, (-.4, -.8, .1)), 'attack_wrist': ('Attack', 24, 'B_R_ForearmTwist', .35, (-.3, -1, .2)),
         'head_top': ('Standing', 0, 'B_Head', .55, (0, .3, 1)), 'head_under': ('Standing', 0, 'B_Head', .55, (0, -.5, -1))}
for item in args[0].split(','):
    label, glb = item.split('=')
    bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
    bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, glb))
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    body = next(o for o in meshes if o.name == 'Minotaur' + LOD)
    for o in meshes:
        o.hide_render = o is not body
    bm = bmesh.new(); bm.from_mesh(body.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)  # glTF splits at UV seams
    # loose pieces by edge connectivity
    seen, pieces = set(), []
    for f0 in bm.faces:
        if f0.index in seen:
            continue
        stack, comp = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop(); comp.append(f)
            for v in f.verts:
                for g in v.link_faces:
                    if g.index not in seen:
                        seen.add(g.index); stack.append(g)
        pieces.append(comp)
    pieces.sort(key=len, reverse=True)
    bmesh.ops.delete(bm, geom=[f for comp in pieces[1:] for f in comp], context='FACES_ONLY')
    bm.to_mesh(body.data); bm.free()
    print('PIECES', label, [len(p) for p in pieces][:8])
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 0, 1, 1)
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3.5; sc.collection.objects.link(sun)
    sun.rotation_euler = (0.8, 0, -0.6); sc.view_settings.view_transform = 'Standard'
    sc.render.engine = 'BLENDER_EEVEE'
    for spot, (act, frame, b, size, d) in SPOTS.items():
        rig.animation_data.action = bpy.data.actions[act]; sc.frame_set(frame); bpy.context.view_layer.update()
        pb = rig.pose.bones[b]; c = rig.matrix_world @ ((pb.head + pb.tail) / 2)
        dv = Vector(d).normalized(); cam.location = c + dv * 4; cam.data.ortho_scale = size
        cam.rotation_euler = (-dv).to_track_quat('-Z', 'Y').to_euler(); cam.data.clip_end = 20
        sc.render.filepath = os.path.join(out, f'{label}{LOD}_{spot}.png'); bpy.ops.render.render(write_still=True)
