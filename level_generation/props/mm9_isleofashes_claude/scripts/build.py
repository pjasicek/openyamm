"""Blender: builds each isle prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>, <Prop>_LOD1, ...)
and work/<prop>_meta.json (asset origin in the source frame, bounds, triangles) from the raw converter GLBs.

Per LOD: import in the asset frame (blib.import_raw), clean (weld, drop degenerate, duplicate and one-triangle
pieces), triangulate; faces of open pieces (sails, ropes, chains, cloth, planks) go to a double-sided material,
closed pieces stay single-sided; normals smooth within SMOOTH degrees; COLOR_0 = vertex occlusion; base centre to
the origin. LODs only for models of 250 or more triangles: about 50 % and 25 % (the native ABC LOD when its count
is near, else a collapse decimation). Extras per prop below (flames, the stat stone's orb).
Usage: blender --background --python build.py -- [prop ...]"""
import json
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blib  # noqa: E402

# Import skinned (armature) props without Blender 5's bone-display ball (the book kept an 80-triangle Icosphere at its
# spine until 2026-10-31).
blib.SKIP_BONE_SHAPES = True

SMOOTH = 40.0
LOD_MIN = 1000
# Per prop: alpha (cut-out skin), flame (cards: [(x, width, bottom, top, mirrored)], in units of the model's
# footprint width / height above the base, or absolute metres with 'abs'), tilt (the book's placement pitch/roll,
# baked: its yaw stays the placement's), orb (the stat stone's sphere on its own scrolling material).
PROPS = {
    'skull': {}, 'shipwreck': {}, 'vikingship': {}, 'podium': {}, 'stonedebris02': {}, 'stonedebris03': {},
    'cot': {}, 'stool': {}, 'coatrack': {}, 'dresser': {}, 'roundtable': {}, 'well': {},
    # the Book object's Rotation (LithTech pitch 2.506, roll pi): lying tilted on the lectern
    'book': {'tilt': (2.5062928199768066, 3.1415927410125732), 'armature': True, 'lods': False,
             'frame_x': blib.BOOK_BALL_FRAME_X_M},
    'statstone': {'orb': True},
    # flames over the log pile (MM9 places a Fire effect object on it) and under the cook pot (its FireNode socket)
    'logsburning': {'flame': {'cards': [(-0.12, 0.45, 0.05, 0.75, False), (0.14, 0.4, 0.05, 0.65, True),
                                        (0.0, 0.6, 0.0, 0.95, False)]}},
    'cookpot': {'alpha': True, 'lod_targets': [0.5], 'flame': {'cards': [(-0.04, 0.4, 0.05, 0.78, False), (0.08, 0.34, 0.05, 0.64, True)],
                                         'abs': True}},
}


def lod_sources(prop):
    raw = os.path.join(blib.WORK, 'raw', prop)
    paths = [os.path.join(raw, f'{prop}.glb')]
    n = 1
    while os.path.exists(os.path.join(raw, f'lod{n}', f'{prop}.glb')):
        paths.append(os.path.join(raw, f'lod{n}', f'{prop}.glb')); n += 1
    return paths


def open_faces(obj):
    """Indices of faces in connected pieces (over welded positions) that have a boundary edge."""
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, piece = [f], []
        seen.add(f.index)
        while stack:
            g = stack.pop(); piece.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        if any(len(e.link_faces) != 2 for g in piece for e in g.edges):
            out.extend(g.index for g in piece)
    bm.free()
    return set(out)


def tilt_matrix(pitch, roll):
    """The transcoder's object rotation (about OpenYAMM x by pitch, then y by roll) in the asset frame, which is
    OpenYAMM turned half round z: D R D with D = diag(-1, -1, 1)."""
    r = Matrix.Rotation(roll, 3, 'Y') @ Matrix.Rotation(pitch, 3, 'X')
    d = Matrix.Diagonal((-1, -1, 1))
    return (d @ r @ d).to_4x4()


def orb_faces(obj, image):
    """Faces whose texture centroid samples the skin's red marble (the stat stone's sphere)."""
    w, h = image.size
    px = np.array(image.pixels[:], np.float32).reshape(h, w, 4)
    uv = obj.data.uv_layers.active.data
    out = []
    for p in obj.data.polygons:
        u = sum(uv[li].uv.x for li in p.loop_indices) / len(p.loop_indices)
        v = sum(uv[li].uv.y for li in p.loop_indices) / len(p.loop_indices)
        r, g, b, _ = px[min(h - 1, max(0, int(v * h))), min(w - 1, max(0, int(u * w)))]
        if r > 0.35 and r > 2.0 * g and r > 2.0 * b:
            out.append(p.index)
    return out


def flame_cards(spec, lo, hi, uv_name):
    """Camera-facing flame cards (shared Flame02 flipbook) on the model's footprint centre; uv_name: the model's
    texture coordinate layer (the join keeps only layers of the same name)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new(uv_name)
    if spec.get('abs'):
        size, height = 1.0, 1.0
    else:
        size = max(hi[0] - lo[0], hi[1] - lo[1]); height = size
    for cx, w, b, t, mirrored in spec['cards']:
        x0, x1 = cx * size - w * size / 2, cx * size + w * size / 2
        z0, z1 = b * height, t * height
        verts = [bm.verts.new(c) for c in ((x0, 0, z0), (x1, 0, z0), (x1, 0, z1), (x0, 0, z1))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uvl].uv = (1 - u if mirrored else u, (1 - v) * 0.8)
    me = bpy.data.meshes.new('Fire'); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new('Fire', me); bpy.context.scene.collection.objects.link(obj)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.ones(len(me.vertices) * 4, np.float32))
    me.color_attributes.active_color = attr
    return obj


def join(objects, name):
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name; objects[0].data.name = name
    return objects[0]


def build(prop):
    spec = PROPS[prop]
    blib.reset()
    origin = blib.binding_origins()[prop]
    sources = lod_sources(prop)
    mats = {'solid': blib.texture_material(prop, f'{prop}_basecolor.png', alpha=spec.get('alpha', False))}
    mats['double'] = mats['solid'].copy(); mats['double'].name = f'{prop}_2s'; mats['double'].use_backface_culling = False
    image = mats['solid'].node_tree.nodes['Image Texture'].image
    if spec.get('orb'):
        mats['orb'] = blib.texture_material(f'{prop}_orb', f'{prop}_orb_basecolor.png', roughness=0.35)
    if spec.get('flame'):
        mats['fire'] = blib.texture_material('Fire', 'flame02_basecolor.png', alpha=True)
        mats['fire'].use_backface_culling = False

    lod0 = blib.import_raw(sources[0], 'lod0', origin, apply_armature=spec.get('armature', False))
    if spec.get('tilt'):
        lod0.data.transform(tilt_matrix(*spec['tilt']))
    dup, small = blib.clean(lod0)
    count0 = blib.triangles(lod0)
    levels = [lod0]
    if count0 >= LOD_MIN and spec.get('lods', True):
        natives = []
        for path in sources[1:]:
            o = blib.import_raw(path, 'native', origin, apply_armature=spec.get('armature', False))
            if spec.get('tilt'):
                o.data.transform(tilt_matrix(*spec['tilt']))
            blib.clean(o)
            natives.append(o)
        windows = {0.5: (0.4, 0.65), 0.25: (0.18, 0.35)}
        for target in spec.get('lod_targets', [0.5, 0.25]):
            window = windows[target]
            pick = next((o for o in natives if window[0] <= blib.triangles(o) / count0 <= window[1]), None)
            if pick is None:
                pick = lod0.copy(); pick.data = lod0.data.copy(); bpy.context.scene.collection.objects.link(pick)
                blib.decimate(pick, target)
            else:
                natives.remove(pick)
            levels.append(pick)
        for o in natives:
            bpy.data.objects.remove(o, do_unlink=True)
    # the asset origin (base centre) from LOD0, shared by every LOD
    centre, lo, hi = blib.base_centre([lod0])
    centre.x += spec.get('frame_x', 0.0)
    names = [prop.capitalize()] + [f'{prop.capitalize()}_LOD{i}' for i in range(1, len(levels))]
    finished, counts = [], []
    for level, (obj, name) in enumerate(zip(levels, names)):
        blib.shift([obj], centre)
        for v in obj.data.vertices:              # a coarser LOD keeps LOD0's ground line
            if v.co.z < 0.0:
                v.co.z = 0.0
        obj.data.materials.clear()
        for key in ('solid', 'double', 'orb'):
            if key in mats:
                obj.data.materials.append(mats[key])
        opened = open_faces(obj)
        for p in obj.data.polygons:
            p.material_index = 1 if p.index in opened else 0
        if spec.get('orb'):
            orb = set(orb_faces(obj, image))
            u0, v0, u1, v1 = ORB_REGION
            uv = obj.data.uv_layers.active.data
            for p in obj.data.polygons:
                if p.index in orb:
                    p.material_index = 2
                    for li in p.loop_indices:
                        uv[li].uv = ((uv[li].uv.x - u0) / (u1 - u0) * 0.5, (uv[li].uv.y - v0) / (v1 - v0))
        blib.smooth(obj, SMOOTH)
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        blib.occlusion(obj, distance=0.15 * size, strength=0.55)
        if spec.get('flame'):
            fire = flame_cards(spec['flame'], lo - np.array(centre), hi - np.array(centre), obj.data.uv_layers.active.name)
            fire.data.materials.append(mats['fire'])
            obj = join([obj, fire], name)          # the fire's primitive last: blended after the solid parts
        obj.name = name; obj.data.name = name
        # drop material slots no face uses (no empty primitives)
        used = {p.material_index for p in obj.data.polygons}
        for index in sorted(range(len(obj.data.materials)), reverse=True):
            if index not in used:
                obj.data.materials.pop(index=index)
        finished.append(obj); counts.append(blib.triangles(obj))
    path = os.path.join(blib.WORK, f'{prop}_export.glb')
    blib.export(finished, path)
    _, lo2, hi2 = blib.base_centre([finished[0]])
    meta = {'prop': prop, 'triangles': counts, 'removed_duplicates': dup, 'removed_small': small,
            # asset origin in the source's OpenYAMM-local frame (units, before the placement's scale and yaw)
            'origin_local_units': [-centre.x * blib.UNITS_PER_METRE, -centre.y * blib.UNITS_PER_METRE,
                                   centre.z * blib.UNITS_PER_METRE],
            'extent_m': [float(v) for v in hi2 - lo2], 'height_units': float(hi2[2] - lo2[2]) * blib.UNITS_PER_METRE,
            'flipped_faces': levels[0]['flipped_faces'] if 'flipped_faces' in levels[0] else None,
            'tilt': spec.get('tilt')}
    with open(os.path.join(blib.WORK, f'{prop}_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT', prop, counts, 'height', round(meta['height_units'], 1))


ORB_REGION = None


def main():
    global ORB_REGION
    with open(os.path.join(blib.WORK, 'orb_region.json')) as f:
        ORB_REGION = json.load(f)
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for prop in args or sorted(PROPS):
        build(prop)


main()
