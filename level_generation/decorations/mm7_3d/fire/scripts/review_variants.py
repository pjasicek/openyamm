"""Front renders (outdoor review light) of finished variant GLBs (LOD0, the only node after linking) into
review/<folder>/<glb stem>.png and a night view (dark background, the additive halos) <glb stem>_night.png, for the
variant sheets (sheet_variants.py).
Usage: blender --background --python review_variants.py -- <folder> <glb> [<glb> ...]"""
import math
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
args = sys.argv[sys.argv.index('--') + 1:]
out = os.path.join(fl.HERE, 'review', args[0])
os.makedirs(out, exist_ok=True)
import json  # noqa: E402
import struct  # noqa: E402


def glb_json(path):
    with open(path, 'rb') as handle:
        raw = handle.read()
    size = struct.unpack_from('<I', raw, 12)[0]
    return json.loads(raw[20:20 + size])


for glb in args[1:]:
    pl.reset()
    bpy.ops.import_scene.gltf(filepath=glb)
    document = glb_json(glb)
    for entry in document['materials']:
        if entry.get('extras', {}).get('openyamm_additive') and entry['name'] in bpy.data.materials:
            factor = entry.get('pbrMetallicRoughness', {}).get('baseColorFactor', [1, 1, 1, 1])[:3]
            fl.review_additive(bpy.data.materials[entry['name']], factor)
    parts = [o for o in bpy.data.objects if o.type == 'MESH']
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if m.node_tree else None
        if bsdf is not None and m.get('openyamm_specular') is not None:
            bsdf.inputs['Specular IOR Level'].default_value = 0.5 * float(m['openyamm_specular'])
    scene = pl.setup_render((384, 640))
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.lens = 85
    pts = [o.matrix_world @ Vector(c) for o in parts for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, radius = (lo + hi) / 2, (hi - lo).length / 2
    fov = 2 * math.atan(cam.data.sensor_width / (2 * cam.data.lens))
    e = math.radians(6)
    d = Vector((0, -math.cos(e), math.sin(e)))
    cam.location = centre + d * radius * 1.0 / math.sin(fov / 2)
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    bpy.data.objects['Sun'].rotation_euler = (math.radians(45), 0, math.radians(-35))
    scene.render.filepath = os.path.join(out, os.path.basename(glb)[:-4] + '.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER', scene.render.filepath)
    # Night view on an opaque dark background: the additive halos show only over a background.
    scene.render.film_transparent = False
    bg = next(n for n in scene.world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.02, 0.025, 0.035, 1.0)
    bpy.data.objects['Sun'].data.energy = 0.25
    scene.render.filepath = os.path.join(out, os.path.basename(glb)[:-4] + '_night.png')
    bpy.ops.render.render(write_still=True)
