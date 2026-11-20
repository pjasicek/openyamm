"""Blender preview of a tier before the runtime build: the export GLB with the body base colour replaced by the tier
preview (tiers_boy.py) and the head set by the tier's head base colour. Args: <glb> <body png> <head png> <out prefix>
[views] [pose action@frame] [ortho] [centre x,y,z]"""
import bpy, sys
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
glb, body_png, head_png, out = a[:4]
views = (a[4] if len(a) > 4 else 'front,q34').split(',')
pose = a[5] if len(a) > 5 and a[5] != '-' else None
ortho = float(a[6]) if len(a) > 6 else 1.5
cen = Vector([float(x) for x in a[7].split(',')]) if len(a) > 7 else Vector((0, 0, 0.68))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    for n in m.node_tree.nodes:
        if n.type == 'TEX_IMAGE' and n.image and any(l.to_socket.name == 'Base Color' for l in n.outputs[0].links):
            if m.name == 'PeasantBoy':
                n.image = bpy.data.images.load(body_png)
            elif m.name == 'PeasantBoyHead':
                n.image = bpy.data.images.load(head_png)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
import os, bmesh
if os.environ.get('NOEARS'):        # tiers a/b: the game draws no ear attachment on them
    for o in bpy.data.objects:
        g = o.vertex_groups.get('Bip01 ElfEars') if o.type == 'MESH' else None
        if g is None:
            continue
        bm = bmesh.new(); bm.from_mesh(o.data); dl = bm.verts.layers.deform.active
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if dl and v[dl].get(g.index, 0) > 0.5], context='VERTS')
        bm.to_mesh(o.data); bm.free()
if pose:
    act, fr = pose.split('@')
    arm.animation_data.action = bpy.data.actions[act]
    try:
        arm.animation_data.action_slot = bpy.data.actions[act].slots[0]
    except Exception:
        pass
    bpy.context.scene.frame_set(int(fr))
elif arm.animation_data:
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis.identity()
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sh = sc.display.shading
import os
sh.light = os.environ.get('LIGHT', 'STUDIO'); sh.color_type = 'TEXTURE'; sh.show_backface_culling = True; sh.show_specular_highlight = False
sc.render.resolution_x = sc.render.resolution_y = 700
w = bpy.data.worlds.new('w'); sc.world = w; w.color = (0.42, 0.42, 0.42)
cd = bpy.data.cameras.new('cam'); cd.type = 'ORTHO'; cd.ortho_scale = ortho
cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
D = {'front': (0, -1, 0.08), 'q34': (-1, -1.25, 0.45), 'back': (0, 1, 0.08), 'left': (1, 0, 0.05), 'right': (-1, 0, 0.05),
     'q34l': (1, -1.25, 0.45), 'party': (0, -1, 0.45), 'below': (0, -0.5, -0.8), 'backl': (1.2, 1, 0.2), 'backr': (-1.2, 1, 0.2)}
for v in views:
    d = Vector(D[v]).normalized()
    cam.location = cen + d * 10
    cam.rotation_euler = (cen - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = f'{out}_{v}.png'
    bpy.ops.render.render(write_still=True)
print('TIERPREVIEW', out)
