"""Render a GLB in a clip pose around a point with textures (flat light) and a red marker. Args: <glb> <out> <clip> <frame24> <x,y,z gltf> <ortho> [views]"""
import bpy, sys, os
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=a[0])
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name): o.hide_render = True
act = bpy.data.actions[a[2]] if a[2] in bpy.data.actions else next(x for x in bpy.data.actions if x.name.startswith(a[2]))
rig.animation_data_create(); rig.animation_data.action = act
if getattr(act, 'slots', None) is not None and len(act.slots): rig.animation_data.action_slot = act.slots[0]
sc = bpy.context.scene; sc.frame_set(int(a[3]))
x, y, z = [float(t) for t in a[4].split(',')]; c = Vector((x, -z, y))
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.004, location=c)
m = bpy.data.materials.new('r'); m.diffuse_color = (1, 0, 0, 1); bpy.context.object.data.materials.append(m)
sc.render.engine = 'BLENDER_WORKBENCH'; sh = sc.display.shading; sh.light = 'STUDIO'; sh.color_type = 'TEXTURE'
sc.render.resolution_x = sc.render.resolution_y = 512
cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = float(a[5])
cam = bpy.data.objects.new('c', cd); sc.collection.objects.link(cam); sc.camera = cam
views = (a[6] if len(a) > 6 else 'front,side,back').split(',')
D = {'front': (0, -1, 0.1), 'side': (1, 0, 0.1), 'oside': (-1, 0, 0.1), 'back': (0, 1, 0.1), 'below': (0, -0.3, -1)}
for v in views:
    d = Vector(D[v]).normalized(); cam.location = c + d * 3
    cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
    sc.render.filepath = a[1] + f'.{v}.png'; bpy.ops.render.render(write_still=True)
print('POSERENDER done')
