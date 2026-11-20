"""Blender: builds each Inventa Storca prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>, <Prop>_LOD1, ...)
and work/<prop>_meta.json from the raw converter GLBs, with the isle props project's helpers (its scripts/blib.py,
paths pointed at this project), as the Anskram props project builds its own: asset frame (the raw import mirrored in
X), clean, faces wound to agree with the ABC's authored normals, open pieces on a double-sided copy of their material,
normals smooth within 40 degrees, COLOR_0 vertex occlusion, base centre at the origin; LODs only from 1000 triangles
(the native ABC LOD when its count is near, else a collapse decimation).

Differences from the Anskram build: a model keeps one material per MM9 skin (the skeleton statue and its base, the
herb bag and its herbs: ABC material k -> textures/<prop>[_k]_basecolor.png); a skin with transparent texels is a
cut-out (MASK); the deforming models (work/raw/<prop>/mode.txt 'full': the book, the burner) are baked in their bind
pose; the tilted book has its placements' pitch baked in.
Usage: blender --background --python build.py -- [prop ...]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISLE = os.path.join(HERE, '..', 'mm9_isleofashes_claude', 'scripts')
sys.path.insert(0, ISLE)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402
import props_table  # noqa: E402

blib.HERE, blib.WORK, blib.TEX = HERE, os.path.join(HERE, 'work'), os.path.join(HERE, 'textures')

SMOOTH = 40.0
LOD_MIN = 1000
SPECS = {name: {} for name in props_table.built_props()}
SPECS.update({name: {'tilt': tilt, 'lods': False} for name, (_, tilt) in props_table.TILTED.items()})
SPECS.update(json.load(open(os.path.join(HERE, 'scripts', 'specs.json'))) if os.path.exists(
    os.path.join(HERE, 'scripts', 'specs.json')) else {})


def tilt_matrix(pitch, roll):
    """The transcoder's object rotation (about OpenYAMM x by pitch, then y by roll) in the asset frame, which is
    OpenYAMM turned half round z: D R D with D = diag(-1, -1, 1) (as the isle's build)."""
    r = Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')
    d = Matrix.Diagonal((-1, -1, 1))
    return (d @ r @ d).to_4x4()


def skin_count(prop):
    return len(props_table.source(prop)[1])


def skin_texture(prop, k):
    return f'{prop}_basecolor.png' if k == 0 else f'{prop}_{k}_basecolor.png'


def has_cutout(prop, k):
    image = bpy.data.images.load(os.path.join(blib.TEX, skin_texture(prop, k)), check_existing=True)
    pixels = np.empty(len(image.pixels), np.float32)
    image.pixels.foreach_get(pixels)
    return image.channels == 4 and float((pixels[3::4] < 0.5).mean()) > 0.002


def mode(prop):
    with open(os.path.join(blib.WORK, 'raw', prop, 'mode.txt')) as f:
        return f.read().strip()


def import_raw(path, name, origin, armature):
    """blib.import_raw, keeping each face's ABC material (skin) index in the face layer 'skin' (the raw GLB's
    materials are named <MODEL>.<k>; blib's join drops them)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=False)
    skins = []
    for o in [o for o in bpy.data.objects if o not in before and o.type == 'MESH']:
        for poly in o.data.polygons:
            material = o.data.materials[poly.material_index] if o.data.materials else None
            skins.append(int(material.name.rsplit('.', 1)[-1].split('_')[0]) if material else 0)
    for o in [o for o in bpy.data.objects if o not in before]:
        bpy.data.objects.remove(o, do_unlink=True)
    obj = blib.import_raw(path, name, origin, apply_armature=armature)
    layer = obj.data.attributes.new('skin', 'INT', 'FACE')
    if len(skins) != len(obj.data.polygons):
        raise SystemExit(f'{path}: face count changed on import ({len(skins)} -> {len(obj.data.polygons)})')
    layer.data.foreach_set('value', np.array(skins, np.int32))
    return obj


def open_faces(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, piece = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop()
            piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index)
                        stack.append(h)
        if any(len(e.link_faces) != 2 for g in piece for e in g.edges):
            out.extend(g.index for g in piece)
    bm.free()
    return set(out)


def lod_sources(prop):
    raw = os.path.join(blib.WORK, 'raw', prop)
    paths = [os.path.join(raw, f'{prop}.glb')]
    n = 1
    while os.path.exists(os.path.join(raw, f'lod{n}', f'{prop}.glb')):
        paths.append(os.path.join(raw, f'lod{n}', f'{prop}.glb'))
        n += 1
    return paths


def prepare(obj, spec):
    if spec.get('tilt'):
        obj.data.transform(tilt_matrix(*spec['tilt']))
    if spec.get('turn'):
        obj.data.transform(Matrix.Rotation(math.radians(spec['turn']), 4, 'Z'))


def build(prop):
    spec = SPECS[prop]
    blib.reset()
    origin = blib.binding_origins()[props_table.source_prop(prop)]
    sources = lod_sources(prop)
    armature = mode(prop) == 'full'
    mats = []
    for k in range(skin_count(prop)):
        solid = blib.texture_material(f'{prop}_{k}' if k else prop, skin_texture(prop, k),
                                      alpha=spec.get('alpha', has_cutout(prop, k)))
        double = solid.copy()
        double.name = f'{solid.name}_2s'
        double.use_backface_culling = False
        mats.append((solid, double))
    lod0 = import_raw(sources[0], 'lod0', origin, armature)
    prepare(lod0, spec)
    dup, small = blib.clean(lod0)
    count0 = blib.triangles(lod0)
    levels = [lod0]
    if count0 >= LOD_MIN and spec.get('lods', True):
        natives = []
        for path in sources[1:]:
            o = import_raw(path, 'native', origin, armature)
            prepare(o, spec)
            blib.clean(o)
            natives.append(o)
        for target, window in ((0.5, (0.4, 0.65)), (0.25, (0.18, 0.35))):
            pick = next((o for o in natives if window[0] <= blib.triangles(o) / count0 <= window[1]), None)
            if pick is None:
                pick = lod0.copy()
                pick.data = lod0.data.copy()
                bpy.context.scene.collection.objects.link(pick)
                blib.decimate(pick, target)
            else:
                natives.remove(pick)
            levels.append(pick)
        for o in natives:
            bpy.data.objects.remove(o, do_unlink=True)
    centre, lo, hi = blib.base_centre([lod0])
    names = [prop.capitalize()] + [f'{prop.capitalize()}_LOD{i}' for i in range(1, len(levels))]
    finished, counts = [], []
    for obj, name in zip(levels, names):
        blib.shift([obj], centre)
        for v in obj.data.vertices:
            if v.co.z < 0.0:
                v.co.z = 0.0
        skins = np.zeros(len(obj.data.polygons), np.int32)
        if 'skin' in obj.data.attributes:
            obj.data.attributes['skin'].data.foreach_get('value', skins)
        obj.data.materials.clear()
        for solid, double in mats:
            obj.data.materials.append(solid)
            obj.data.materials.append(double)
        opened = open_faces(obj)
        for p in obj.data.polygons:
            k = int(min(max(skins[p.index], 0), len(mats) - 1))
            p.material_index = 2 * k + (1 if p.index in opened else 0)
        if 'skin' in obj.data.attributes:
            obj.data.attributes.remove(obj.data.attributes['skin'])
        blib.smooth(obj, SMOOTH)
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        blib.occlusion(obj, distance=0.15 * size, strength=0.55)
        obj.name = name
        obj.data.name = name
        used = {p.material_index for p in obj.data.polygons}
        for index in sorted(range(len(obj.data.materials)), reverse=True):
            if index not in used:
                obj.data.materials.pop(index=index)
        finished.append(obj)
        counts.append(blib.triangles(obj))
    blib.export(finished, os.path.join(blib.WORK, f'{prop}_export.glb'))
    _, lo2, hi2 = blib.base_centre([finished[0]])
    meta = {'prop': prop, 'triangles': counts, 'removed_duplicates': dup, 'removed_small': small,
            'origin_local_units': [-centre.x * blib.UNITS_PER_METRE, -centre.y * blib.UNITS_PER_METRE,
                                   centre.z * blib.UNITS_PER_METRE],
            'extent_m': [float(v) for v in hi2 - lo2], 'height_units': float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE,
            'flame_head_m': None, 'materials': [m.name for m in finished[0].data.materials]}
    with open(os.path.join(blib.WORK, f'{prop}_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT', prop, counts, 'height', round(meta['height_units'], 1), meta['materials'])


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for prop in args or sorted(SPECS):
        build(prop)


main()
