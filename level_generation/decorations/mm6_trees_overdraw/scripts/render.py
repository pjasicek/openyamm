"""Gate and review renders of one GLB (Blender, Eevee, no shadow maps: the engine default; as the MM6 pipeline's
render_review.py: sun + sky, Standard view, base colour x COLOR_0, leaves alpha-clipped). Single-sided materials (bark,
shell) cull back faces as the engine does.
Usage: blender --background --python render.py -- <model.glb> <out_prefix> <views> [res]
Views: eye, three_quarter, side (whole tree, every LOD: <prefix>_LOD<n>_<view>.png); close (LOD0 crown from 3 m);
under (LOD0 from below the crown, looking up); trunk (LOD0 lower trunk close-up); up (LOD0 from 2 m above the
ground 1.8 m from the trunk axis, pitched 60 degrees up: the black-heart check); low3q (LOD0 three-quarter from 1 m up)."""
import bpy, math, os, sys
from mathutils import Vector
args = sys.argv[sys.argv.index('--') + 1:]
path, prefix, views = args[0], args[1], args[2].split(',')
res = int(args[3]) if len(args) > 3 else 540
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glb
bpy.ops.wm.read_factory_settings(use_empty=True)
# the LOD meshes hang off the Tree node's openyamm_lods (no nodes of their own): give each a node for the importer
model = glb.read(path)
for k, mi in enumerate(model.mesh_chain()[1:], 1):
    model.doc['nodes'].append({'name': f'Tree_LOD{k}', 'mesh': mi})
    model.doc['scenes'][0]['nodes'].append(len(model.doc['nodes']) - 1)
tmp = prefix + '_import.glb'
model.write(tmp)
bpy.ops.import_scene.gltf(filepath=tmp)
os.remove(tmp)
sc = bpy.context.scene
for engine in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE'):
    try:
        sc.render.engine = engine; break
    except TypeError:
        continue
sc.view_settings.view_transform = 'Standard'
sc.render.film_transparent = True
sc.render.resolution_y = res; sc.render.resolution_x = int(res * 480 / 540)
world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
bg.inputs['Color'].default_value = (0.55, 0.6, 0.68, 1); bg.inputs['Strength'].default_value = 0.5
sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sc.collection.objects.link(sun)
sun.data.energy = 3.6; sun.data.color = (1.0, 0.95, 0.86)
sun.rotation_euler = (math.radians(40), 0, math.radians(-35))
sun.data.use_shadow = False
for attr in ('use_shadows', 'use_fast_gi', 'use_raytracing', 'use_gtao'):
    if hasattr(sc.eevee, attr):
        setattr(sc.eevee, attr, False)
for m in bpy.data.materials:          # the importer already multiplies base colour by COLOR_0 (Mix node)
    bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
    if bsdf is not None:
        # the engine's leaves barely reflect (openyamm_specular 0.1); the shell half as much (0.05)
        bsdf.inputs['Specular IOR Level'].default_value = 0.075 if m.name == 'Shell' else 0.15
lods = sorted([o for o in bpy.data.objects if o.type == 'MESH'], key=lambda o: o.name)
cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 50
Hh = max((o.matrix_world @ Vector(c)).z for o in lods if o.name == 'Tree' for c in o.bound_box)   # LOD0 frames all
scale = Hh / 6.69
CAMS = {'eye': (0.0, 1.6, 10.5, 0.5), 'three_quarter': (45.0, 5.5, 10.5, 0.5), 'side': (90.0, 1.6, 10.5, 0.5),
        'close': (20.0, 3.4, 5.2, 0.7), 'under': (0.0, 1.5, 2.6, 0.62), 'trunk': (30.0, 1.0, 2.6, 0.12),
        'low3q': (45.0, 1.0, 7.0, 0.62)}
# 'up': standing next to the trunk (1.8 m out from its axis, eye 2 m above the ground, not scaled), looking up at 60 degrees
UP = (200.0, 2.0, 1.8, 60.0)


def lod_name(o):
    n = o.name
    return 'LOD0' if n == 'Tree' else n.replace('Tree_', '')


for o in lods:
    for view in views:
        if view in ('close', 'under', 'trunk', 'up', 'low3q') and o.name != 'Tree':
            continue
        for x in lods:
            x.hide_render = x is not o
        if view == 'up':
            yaw, height, dist, pitch = UP
            cam.location = (math.sin(math.radians(yaw)) * dist, -math.cos(math.radians(yaw)) * dist, height)
            inward = Vector((-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)), 0.0))
            target = cam.location + inward * math.cos(math.radians(pitch)) + Vector((0, 0, math.sin(math.radians(pitch))))
        else:
            yaw, height, dist, aim = CAMS[view]
            cam.location = (math.sin(math.radians(yaw)) * dist * scale, -math.cos(math.radians(yaw)) * dist * scale,
                            height * scale)
            target = Vector((0, 0, Hh * aim))
        cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = f'{prefix}_{lod_name(o)}_{view}.png'
        bpy.ops.render.render(write_still=True)
        print('RENDERED', sc.render.filepath)
