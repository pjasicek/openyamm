"""Meshy image-to-3D prop -> game model with LODs (bone pile dec29, carcass dec21, carrion dec22).

1. High: the Meshy GLB (meshy/meshy/<job>/model_urls_glb.glb, textured PBR), welded, joined, turned by `yaw` (+35:
   Meshy's front is the three-quarter reference camera, 35 degrees off the sprite's front) so the sprite's front faces
   the model front (-y), crumbs dropped, scaled to `width` metres, centred, grounded; vertices within `flatten` of the
   bottom are pressed onto the ground (flat on the ground).
2. LOD0: a copy voxel-remeshed (manifold, no inner shells), collapse-decimated to `tris`, Smart UV unwrapped.
3. Bake (Cycles, selected to active, cage out from LOD0): base colour (the Meshy texture as emission), roughness,
   tangent-space normal, and ambient occlusion of the high mesh, at `res`.
4. Texture: base colour times AO^ao, graded so its rendered mean lands on the sprite's mean (`grade` linear gains);
   roughness clamped to `rough` (meat: wet spots from the bake's low values, kept small). Saved as
   props/textures/<name>_{basecolor,normal,mr}.png.
5. LOD1: LOD0 collapse-decimated (its UVs and texture). LOD2: a coarser voxel remesh with its own charts in the
   atlas corner FAR, baked together with LOD0. COLOR_0 white (the light is in the bake).
Usage: blender --background --python meshy_prop.py -- <name> [--preview]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mm8lib as ml  # noqa: E402

pl = ml.pl
MESHY = os.path.join(ml.HERE, 'meshy')
CONFIG = {
    'bonepile': {'job': 'bonepile_i23d_v1', 'yaw': 35.0, 'width': 1.12, 'tris': (2500, 1150, 480), 'res': 1024,
                 'voxel': 0.006, 'flatten': 0.012, 'ao': 0.6, 'rough': (0.62, 0.8), 'wet': 0.0,
                 'specular': 0.4, 'grade_target': (127, 116, 94), 'sprite': 'dec29'},
    'carcass': {'job': 'carcass_i23d_v1', 'yaw': 35.0, 'width': 1.28, 'tris': (3000, 1400, 600), 'res': 1024,
                'voxel': 0.007, 'flatten': 0.015, 'ao': 0.6, 'rough': (0.6, 0.75), 'wet': 0.35,
                'specular': 0.5, 'grade_target': (152, 112, 76), 'sprite': 'dec21'},
    'carrion': {'job': 'carrion_i23d_v1', 'yaw': 35.0, 'width': 1.26, 'tris': (3500, 1600, 650), 'res': 1024,
                'voxel': 0.007, 'flatten': 0.015, 'ao': 0.6, 'rough': (0.6, 0.75), 'wet': 0.35,
                'specular': 0.5, 'grade_target': (147, 91, 57), 'sprite': 'dec22'},
}
OVERRIDES = os.path.join(ml.HERE, 'meshy', 'prop_overrides.json')     # tuned yaw / grade per prop


def find_glb(job):
    folder = os.path.join(MESHY, 'meshy', job)
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.endswith('.glb'):
                return os.path.join(root, f)
    raise FileNotFoundError(folder)


def import_high(cfg):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=find_glb(cfg['job']))
    meshes = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    for o in bpy.data.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    high = bpy.context.view_layer.objects.active
    for o in [o for o in bpy.data.objects if o not in before and o is not high]:
        bpy.data.objects.remove(o)
    high.parent = None
    high.matrix_world = high.matrix_world.copy()
    ml.apply_transforms(high)
    high.name = 'High'
    # weld the import's seam splits (texture coordinates stay per corner), then drop crumbs: loose parts under 0.3 %
    bm = bmesh.new(); bm.from_mesh(high.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(high.data); bm.free()
    label, count = ml.loose_labels(high)
    sizes = np.bincount(label, minlength=count)
    ml.delete_verts(high, sizes[label] < 0.003 * len(label))
    high.data.transform(Matrix.Rotation(math.radians(cfg['yaw']), 4, 'Z'))
    lo, hi = pl.bounds([high])
    s = cfg['width'] / (hi.x - lo.x)
    high.data.transform(Matrix.Diagonal((s, s, s, 1.0)) @ Matrix.Translation(-Vector(((lo.x + hi.x) / 2,
                                                                                       (lo.y + hi.y) / 2, lo.z))))
    for v in high.data.vertices:
        if v.co.z < cfg['flatten']:
            v.co.z = max(0.0, v.co.z - cfg['flatten'] * 0.5) * 0.5
    high.data.update()
    return high


def unwrap(obj, region):
    """Smart UV of obj packed into region (u0, v0, size) of the atlas."""
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.uv_layers.new(name='UVMap')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.004)
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    u0, v0, size = region
    for loop in obj.data.uv_layers[0].data:
        loop.uv = (u0 + loop.uv[0] * size, v0 + loop.uv[1] * size)


def remeshed(high, name, voxel, tris):
    obj = ml.duplicate(high, name)
    obj.data.materials.clear()
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    mod = obj.modifiers.new('R', 'REMESH'); mod.mode = 'VOXEL'; mod.voxel_size = voxel
    bpy.ops.object.modifier_apply(modifier=mod.name)
    label, count = ml.loose_labels(obj)                 # voxel crumbs (a far level shows them as floaters)
    sizes = np.bincount(label, minlength=count)
    ml.delete_verts(obj, sizes[label] < 0.01 * len(label))
    pl.decimate_to(obj, tris)
    for v in obj.data.vertices:
        v.co.z = max(v.co.z, 0.0)
    ml.smooth(obj)
    return obj


FAR = (0.875, 0.875, 0.125)          # atlas corner of the far level's own charts; LOD0 takes [0, 0.875]^2


def make_low(high, cfg):
    """LOD0 (voxel remesh, decimated) and the far level (a coarser voxel remesh, decimated: collapsing LOD0 that far
    shatters across its UV islands), unwrapped into one atlas and joined for a single bake (attribute 'far' marks
    the far level's vertices for the split after it)."""
    low = remeshed(high, 'Low', cfg['voxel'], cfg['tris'][0])
    unwrap(low, (0.0, 0.0, 0.875))
    far = remeshed(high, 'Far', cfg['voxel'] * 4, cfg['tris'][2])
    unwrap(far, FAR)
    for obj, flag in ((low, 0), (far, 1)):
        a = obj.data.attributes.new('far', 'INT', 'POINT')
        a.data.foreach_set('value', np.full(len(obj.data.vertices), flag, np.int32))
    return pl.join('Low', [low, far])


def split_far(joined):
    values = np.empty(len(joined.data.vertices), np.int32)
    joined.data.attributes['far'].data.foreach_get('value', values)
    far = ml.duplicate(joined, 'Far')
    ml.delete_verts(joined, values == 1)
    ml.delete_verts(far, values == 0)
    for o in (joined, far):
        o.data.attributes.remove(o.data.attributes['far'])
    return joined, far


def bake(high, low, cfg):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'               # the GPU is shared with other sessions (CUDA out of memory)
    scene.cycles.samples = 16
    b = scene.render.bake
    b.use_selected_to_active = True; b.use_cage = False
    b.cage_extrusion = 0.012; b.max_ray_distance = 0.05; b.margin = 8; b.margin_type = 'EXTEND'
    res = cfg['res']
    target = bpy.data.materials.new('BakeTarget'); target.use_nodes = True
    low.data.materials.clear(); low.data.materials.append(target)
    tnode = target.node_tree.nodes.new('ShaderNodeTexImage'); target.node_tree.nodes.active = tnode
    mats = [m for m in high.data.materials if m and m.node_tree]

    def emit_from(socket_name):
        undo = []
        for m in mats:
            nt = m.node_tree
            bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
            out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output)
            src = bsdf.inputs[socket_name]
            emit = nt.nodes.new('ShaderNodeEmission')
            if src.links:
                nt.links.new(src.links[0].from_socket, emit.inputs['Color'])
            else:
                v = src.default_value
                emit.inputs['Color'].default_value = (v, v, v, 1) if isinstance(v, float) else v
            nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
            undo.append((nt, bsdf, out, emit))
        return undo

    def restore(undo):
        for nt, bsdf, out, emit in undo:
            nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface']); nt.nodes.remove(emit)

    def run(name, kind, colorspace, socket=None):
        img = bpy.data.images.new(name, res, res, alpha=False); img.colorspace_settings.name = colorspace
        tnode.image = img
        undo = emit_from(socket) if socket else []
        for o in bpy.data.objects:
            o.select_set(o in (high, low))
        bpy.context.view_layer.objects.active = low
        bpy.ops.object.bake(type=kind)
        restore(undo)
        a = np.empty(res * res * 4, np.float32); img.pixels.foreach_get(a)
        return a.reshape(res, res, 4)[..., :3]
    base = run('base', 'EMIT', 'sRGB', 'Base Color')
    rough = run('rough', 'EMIT', 'Non-Color', 'Roughness')
    normal = run('normal', 'NORMAL', 'Non-Color')
    scene.cycles.samples = 64
    ao = run('ao', 'AO', 'Non-Color')
    return base, rough, normal, ao


def save_textures(name, cfg, base, rough, normal, ao):
    """Raw bakes to work/<name>_bake.npz; scripts/meshy_textures.py (system Python with PIL) writes the PNGs."""
    import subprocess
    path = os.path.join(ml.WORK, f'{name}_bake.npz')
    np.savez_compressed(path, base=base, rough=rough, normal=normal, ao=ao)
    subprocess.run(['/usr/bin/python3', '-I', os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                           'meshy_textures.py'), path, json.dumps(cfg)], check=True)


def reduce_to(obj, target):
    """Collapse toward target; where the UV-island borders stall it, accept the lowest count reached, then drop
    loose islands below 0.5 % of the triangles (crumbs a far level does not need)."""
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    for _ in range(6):
        start = pl.triangles(obj)
        if start <= target * 1.05:
            break
        mod = obj.modifiers.new('D', 'DECIMATE'); mod.decimate_type = 'COLLAPSE'
        mod.ratio = max(0.05, target / start); mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        if pl.triangles(obj) > start * 0.97:
            break
    label, count = ml.loose_labels(obj)
    sizes = np.bincount(label, minlength=count)
    ml.delete_verts(obj, sizes[label] < 0.005 * len(label))
    print('REDUCED', obj.name, pl.triangles(obj), 'target', target)


def main():
    name = sys.argv[sys.argv.index('--') + 1]
    cfg = dict(CONFIG[name])
    if os.path.exists(OVERRIDES):
        cfg.update(json.load(open(OVERRIDES)).get(name, {}))
    pl.reset()
    high = import_high(cfg)
    lo, hi = pl.bounds([high])
    print('HIGH tris', pl.triangles(high), 'size', [round(v, 3) for v in hi - lo])
    if '--preview' in sys.argv:
        pl.setup_render((768, 512))
        out = os.path.join(ml.HERE, 'review', name + '_meshy')
        for tag, view in (('front', (0, 18)), ('tq', (40, 30)), ('side', (90, 10)), ('top', (0, 80))):
            pl.render_views([high], out, 'high_' + tag, views=(view,))
        return
    low = make_low(high, cfg)
    base, rough, normal, ao = bake(high, low, cfg)
    save_textures(name, cfg, base, rough, normal, ao)
    pl._images.clear()
    mat = ml.material(name.title(), name, extras={'openyamm_specular': cfg['specular']})
    bpy.data.objects.remove(high)
    low.data.materials.clear(); low.data.materials.append(mat)
    low.name = name.title()
    low, far = split_far(low)
    low.name = name.title()
    lod1 = ml.duplicate(low, f'{name.title()}_LOD1')
    reduce_to(lod1, cfg['tris'][1])
    far.name = f'{name.title()}_LOD2'
    levels = [low, lod1, far]
    for lod in levels:
        ml.smooth(lod)
        ml.colour(lod, rays=4, distance=0.01, strength=0.0)            # white COLOR_0: the light is in the bake
    print('LODS', [pl.triangles(o) for o in levels])
    ml.export(levels, name)


main()
