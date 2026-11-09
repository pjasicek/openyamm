"""Shading close-ups of a runtime GLB in its rest pose (2026-10-30 flat-shading fix): LOD0 only (LOD and shadow
meshes hidden), Eevee, one sun from above-front plus a grey world. Two looks: textured (the GLB's own base colour,
normal and metal-rough maps) and clay (no textures: the mesh normals alone).
Args: -- <in.glb> <out_prefix> [size]   writes <out_prefix>_<view>_<look>.png for views head34, headside, body34"""
import bpy, sys, math
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
glb, out = args[0], args[1]
size = int(args[2]) if len(args) > 2 else 700
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
arm.animation_data_clear()
for b in arm.pose.bones:
    b.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'Shadow' in o.name):
        o.hide_render = True
body = next(o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render)
bpy.context.view_layer.update()
head = arm.matrix_world @ arm.pose.bones['Xhead'].head
pts = [body.matrix_world @ Vector(c) for c in body.bound_box]
centre = sum(pts, Vector()) / 8
ext = max((p - centre).length for p in pts)
sc = bpy.context.scene
for eng in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = eng
        break
    except TypeError:
        pass
sc.render.resolution_x = sc.render.resolution_y = size
sc.render.film_transparent = False
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs[0].default_value = (0.35, 0.37, 0.4, 1); bg.inputs[1].default_value = 0.8
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.5
sun = bpy.data.objects.new('sun', sd); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(50), 0, math.radians(-30))
cd = bpy.data.cameras.new('cam'); cam = bpy.data.objects.new('cam', cd); sc.collection.objects.link(cam); sc.camera = cam
cd.lens = 85
mouth = bpy.data.objects['Socket_Mouth'].matrix_world.translation
hc = (head + mouth) / 2
hl = (mouth - head).length
views = {'head34': (hc + Vector((-0.6, -1.0, 0.35)).normalized() * hl * 7.0, hc),
         'headside': (hc + Vector((-1.0, -0.1, 0.1)).normalized() * hl * 7.0, hc),
         'body34': (centre + Vector((-0.6, -1.0, 0.3)).normalized() * ext * 3.2, centre)}
clay = bpy.data.materials.new('clay'); clay.use_nodes = True
cb = next(n for n in clay.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
cb.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1); cb.inputs['Roughness'].default_value = 0.6
orig = [s.material for s in body.material_slots]
for look in ('textured', 'clay'):
    for i, s in enumerate(body.material_slots):
        s.material = orig[i] if look == 'textured' else clay
    for name, (loc, tgt) in views.items():
        cam.location = loc
        cam.rotation_euler = (tgt - loc).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{out}_{name}_{look}.png'
        bpy.ops.render.render(write_still=True)
print('CLOSEUPS', out)
