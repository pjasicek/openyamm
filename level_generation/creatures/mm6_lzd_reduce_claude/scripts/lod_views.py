"""Front and three-quarter renders of every colour LOD of a runtime GLB (Standing frame 0, transparent film) for
the LOD comparison sheet: review/lods/<label>_lod<k>_<view>.png. Usage: blender -b -P lod_views.py -- <glb> <label>"""
import copy, math, os, sys, tempfile
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb  # noqa: E402
HERE = Path(__file__).resolve().parents[1]
glb, label = sys.argv[sys.argv.index('--') + 1:][:2]
doc, binary = read_glb(Path(glb)); node = next(n for n in doc['nodes'] if n.get('name') == 'Lizard')
levels = [node['mesh']] + doc['meshes'][node['mesh']]['extras']['openyamm_lods']
(HERE / 'review/lods').mkdir(parents=True, exist_ok=True)
for k, mi in enumerate(levels):
    d = copy.deepcopy(doc); n = next(x for x in d['nodes'] if x.get('name') == 'Lizard'); n['mesh'] = mi
    tmp = Path(tempfile.mkdtemp()) / 'lod.glb'; write_glb(tmp, d, bytearray(binary))
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.ops.import_scene.gltf(filepath=str(tmp))
    sc = bpy.context.scene; rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    rig.animation_data.action = bpy.data.actions['Standing']; sc.frame_set(0)
    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('Cam')); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.0
    sun = bpy.data.objects.new('Sun', bpy.data.lights.new('Sun', 'SUN')); sun.data.energy = 3
    sun.rotation_euler = (math.radians(40), 0, math.radians(-25)); sc.collection.objects.link(sun)
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (.35, .35, .38, 1)
    sc.view_settings.view_transform = 'Standard'; sc.render.resolution_x = sc.render.resolution_y = 600
    sc.render.engine = 'BLENDER_EEVEE'; sc.render.film_transparent = True
    c = Vector((0, 0, 0.88))
    for view, dv in {'front': (0, -1, .1), 'q34': (.7, -.7, .2)}.items():
        cam.location = c + Vector(dv).normalized() * 4
        cam.rotation_euler = (c - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = str(HERE / 'review/lods' / f'{label}_lod{k}_{view}.png'); bpy.ops.render.render(write_still=True)
