"""Build a statue from its Meshy retexture (statues_hd/<name>/meshy/<retexture>.glb, on the prepared Smart Topology
mesh with our UVs): import, ground, scale-free (the binding height scales it), LOD0 = the Meshy mesh (or a reduction
to the budget), LOD1-LOD3 collapse-decimated from it (UVs kept, so every level uses one texture set), and the
textures written to textures/hd_<name>_{basecolor,normal,mr}.png by hd_grade.py beforehand.
COLOR_0 = softened vertex occlusion x a tint that brings each material's albedo to its sprite target (dungeon
statues) or to target x GAIN (outdoor statues, as statue_knight.py).
Stages: --extract writes the Meshy texture images to statues_hd/<name>/meshy/ (for hd_grade.py); default builds and
exports work/<name>_export.glb from the graded textures (the current statue_*.py export is replaced).
Usage: blender --background --python hd_build.py -- <name> <retexture glb> [--extract]"""
import json
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statue_lib as sl  # noqa: E402

dlib, pl, hl = sl.dlib, sl.pl, sl.hl
sys.path.insert(0, os.path.join(dlib.DECO, 'mm6_dungeons_3d', 'bones', 'scripts'))
import blib  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
NAME, SOURCE = args[0], args[1]
EXTRACT = '--extract' in args
HD = os.path.join(dlib.HERE, 'statues_hd', NAME)
SPECS = {
    # LOD triangle targets; COLOR_0 target (sRGB) for the stone; outdoor gain (None: dungeon statue)
    '7dec55': {'lods': [3900, 1800, 600, 280], 'target': (70, 75, 62), 'gain': None, 'sprite_mean': (69, 74, 61)},
    '7dec54': {'lods': [5900, 2450, 540, 215], 'target': (75, 79, 65), 'gain': None, 'sprite_mean': (77, 79, 63)},
    'dec94': {'lods': [5900, 2500, 680, 300], 'target': (90, 81, 68), 'gain': (0.88, 0.85, 0.8)},
    'dec95': {'lods': [3900, 1500, 500, 260], 'target': (110, 104, 92), 'gain': (0.88, 0.85, 0.8)},
}
spec = SPECS[NAME]


def extract():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = blib.import_mesh(SOURCE, 'Statue')
    blib.ground(obj, 1.0)
    # per-triangle texture coordinates and heights (0..1 of the statue) for hd_grade.py's texel masks
    me = obj.data; me.calc_loop_triangles()
    uv = me.uv_layers[0].data
    tris = np.array([[(*uv[l].uv, me.vertices[me.loops[l].vertex_index].co.z) for l in t.loops]
                     for t in me.loop_triangles], np.float32)
    os.makedirs(os.path.join(HD, 'meshy'), exist_ok=True)
    np.save(os.path.join(HD, 'meshy', 'uv_tris.npy'), tris)
    print('UVTRIS', tris.shape)
    out = os.path.join(HD, 'meshy')
    for img in bpy.data.images:
        if img.size[0] == 0:
            continue
        path = os.path.join(out, f'tex_{img.name.replace(" ", "_")}.png')
        img.filepath_raw = path; img.file_format = 'PNG'; img.save()
        print('IMAGE', path, img.size[:], img.colorspace_settings.name)
    for m in bpy.data.materials:
        if m.node_tree:
            bsdf = next((n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None)
            links = {k: [l.from_node.image.name for l in bsdf.inputs[k].links if l.from_node.type == 'TEX_IMAGE']
                     for k in ('Base Color',)} if bsdf else {}
            print('MATERIAL', m.name, links)


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = blib.import_mesh(SOURCE, 'Statue')
    obj.data.materials.clear()
    blib.ground(obj, 1.0)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)       # glTF splits vertices at UV/normal seams
    bm.to_mesh(obj.data); bm.free()
    while len(obj.data.uv_layers) > 1:
        obj.data.uv_layers.remove(obj.data.uv_layers[-1])
    obj.data.uv_layers[0].name = 'UVMap'
    for key in ('custom_normal',):
        if key in obj.data.attributes:
            obj.data.attributes.remove(obj.data.attributes[key])
    mat = dlib.material('Stone', f'hd_{NAME}', extras={'openyamm_specular': 0.35})
    obj.data.materials.append(mat)
    sl.robust_decimate(obj, spec['lods'][0])
    sl.smooth(obj, 60)
    lods = [obj]
    for k, target in enumerate(spec['lods'][1:], 1):
        lod = sl.duplicate(lods[0], f'Statue_LOD{k}')          # every level from LOD0, one pass
        lod = sl.decimate_pieces(lod, target, minimum=(30, 16, 10)[k - 1])
        lods.append(lod)
    record = json.load(open(os.path.join(dlib.WORK, f'hd_{NAME}_texture.json')))
    exposed, albedo = record['mean'], record['albedo']
    # dungeon statues: the sprite's whole mean (gold included); outdoor: the graded albedo x the outdoor gain
    if spec['gain'] is None:          # keep the graded chroma, match the sprite's luminance
        lin = sl.srgb_to_linear(np.array(albedo) / 255); ref = sl.srgb_to_linear(np.array(spec['sprite_mean']) / 255)
        k = float(ref @ [0.2126, 0.7152, 0.0722]) / float(lin @ [0.2126, 0.7152, 0.0722])
        t = tuple((sl.linear_to_srgb(lin * k) * 255).tolist())
    else:
        t = tuple(v * g for v, g in zip(albedo, spec['gain']))
    for k, lod in enumerate(lods):
        pl.vertex_occlusion(lod, rays=(32, 20, 12, 8)[k], distance=0.06, strength=0.55, floor=True)
        sl.tint_groups(lod, {'Stone': (t, exposed)}, keep={'Stone': 0.4})
    dlib.save(NAME, lods)


if EXTRACT:
    extract()
else:
    build()
