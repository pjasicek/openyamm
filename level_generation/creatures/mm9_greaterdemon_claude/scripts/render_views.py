"""Orthographic textured renders of a GLB (bind pose, or ACTION@FRAME) from named views.

Args: glb outdir prefix views(comma) size [action@frame|-] [ortho_scale] [cx,cy,cz]
Views: q34 (front three-quarter from the creature's right, slightly above), front, back, left, right, top.
The creature faces -Y in Blender (glTF +Z).
"""
import bpy, sys, math, os
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
glb, outdir, prefix, views, size = argv[0], argv[1], argv[2], argv[3].split(','), int(argv[4])
pose = argv[5] if len(argv) > 5 and argv[5] != '-' else None
ortho = float(argv[6]) if len(argv) > 6 else 1.45
os.makedirs(outdir, exist_ok=True)
if glb.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=glb)
    import os as _o
    hide = (_o.environ.get('HIDE') or '').split(',')
    for o in bpy.data.objects:
        if o.name in hide:
            o.hide_render = True
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb)
sc = bpy.context.scene
for o in list(sc.objects):
    if o.type == 'MESH' and o.name.startswith('Icosphere'):
        o.hide_render = True
arms = [o for o in sc.objects if o.type == 'ARMATURE']
for arm in arms:
    if pose:
        name, frame = pose.split('@')
        act = bpy.data.actions[name]
        arm.animation_data.action = act
        try:
            arm.animation_data.action_slot = act.slots[0]
        except Exception:
            pass
        sc.frame_set(int(float(frame)))
    else:
        if arm.animation_data:
            arm.animation_data.action = None
        for pb in arm.pose.bones:
            pb.matrix_basis.identity()
bpy.context.view_layer.update()
# frame the evaluated meshes
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for o in sc.objects:
    if o.type == 'MESH' and not o.hide_render:
        me = o.evaluated_get(dg).to_mesh()
        pts += [o.matrix_world @ v.co for v in me.vertices]
        o.evaluated_get(dg).to_mesh_clear()
centre = Vector([(min(p[i] for p in pts) + max(p[i] for p in pts)) / 2 for i in range(3)])
if len(argv) > 7:
    centre = Vector([float(c) for c in argv[7].split(',')])
try:
    sc.render.engine = 'BLENDER_WORKBENCH'
except TypeError as e:
    print(e)
sh = sc.display.shading
sh.light = 'STUDIO'
sh.color_type = 'TEXTURE'
sh.show_backface_culling = False
sc.render.resolution_x = size
sc.render.resolution_y = size
sc.render.film_transparent = True
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
cd = bpy.data.cameras.new('cam')
cd.type = 'ORTHO'
cd.ortho_scale = ortho
cd.clip_end = 100
cam = bpy.data.objects.new('cam', cd)
sc.collection.objects.link(cam)
sc.camera = cam
dirs = {'q34': Vector((-1.0, -1.25, 0.55)), 'front': Vector((0, -1, 0)), 'back': Vector((0, 1, 0)),
        'left': Vector((1, 0, 0)), 'right': Vector((-1, 0, 0)), 'top': Vector((0, 0.0001, 1)),
        'q34l': Vector((1.0, -1.25, 0.55))}
for v in views:
    d = dirs[v].normalized()
    cam.location = centre + d * 10
    cam.rotation_euler = (centre - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = os.path.join(outdir, f'{prefix}_{v}.png')
    bpy.ops.render.render(write_still=True)
print('RENDERED', prefix, views)
