"""Job 7: orthographic side views of the head of a static textured export (unmirrored, Blender z-up, floor 0) for
measuring: camera on +x (`R`) or -x (`L`) looking at the head side, ortho size SIZE m centred at (CY, CZ); EEVEE,
the GLB's own maps, flat grey world + soft sun. Writes <out>_<side>.png and prints the pixel mapping.
Optional `clay` renders a grey material instead (geometry check). Args: <glb> <out prefix> [size 0.24] [cy -0.01]
[cz 1.0] [clay|tex] [px 800] [nohead_hide]"""
import bpy, sys, math
a = sys.argv[sys.argv.index('--') + 1:]
glb, out = a[0], a[1]
SIZE = float(a[2]) if len(a) > 2 else 0.24; CY = float(a[3]) if len(a) > 3 else -0.01; CZ = float(a[4]) if len(a) > 4 else 1.0
MODE = a[5] if len(a) > 5 else 'tex'; PX = int(a[6]) if len(a) > 6 else 800
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb)
rig = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if rig and rig.animation_data: rig.animation_data.action = None
if rig:
    for pb in rig.pose.bones: pb.matrix_basis.identity()
for o in bpy.data.objects:
    if o.type == 'MESH' and ('LOD' in o.name or 'hadow' in o.name): o.hide_render = True
if MODE == 'clay':
    m = bpy.data.materials.new('clay'); m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'); bs.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1)
    bs.inputs['Roughness'].default_value = 0.7
    for o in bpy.data.objects:
        if o.type == 'MESH':
            for i in range(len(o.material_slots)): o.material_slots[i].material = m
sc = bpy.context.scene
try: sc.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError: sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x = sc.render.resolution_y = PX
sc.world = bpy.data.worlds.new('W'); sc.world.use_nodes = True
bg = next(n for n in sc.world.node_tree.nodes if n.type == 'BACKGROUND'); bg.inputs['Color'].default_value = (0.3, 0.32, 0.35, 1)
for nm, rot, en in (('key', (40, 0, 60), 2.5), ('key2', (40, 0, -60), 2.5), ('fill', (100, 0, 180), 0.8)):
    ld = bpy.data.lights.new(nm, 'SUN'); ld.energy = en; lo = bpy.data.objects.new(nm, ld); sc.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(x) for x in rot]
cd = bpy.data.cameras.new('C'); cd.type = 'ORTHO'; cd.ortho_scale = SIZE; cd.clip_start = 0.01
cam = bpy.data.objects.new('C', cd); sc.collection.objects.link(cam); sc.camera = cam
for side, x, rz in (('R', 0.6, 90), ('L', -0.6, -90)):
    cam.location = (x, CY, CZ); cam.rotation_euler = (math.radians(90), 0, math.radians(rz))
    sc.render.filepath = f'{out}_{side}.png'; bpy.ops.render.render(write_still=True)
print('SIDEORTHO', SIZE, CY, CZ, PX)
