"""Blender: builds each Dungeon of Secrets prop's decoration GLB (work/<prop>_export.glb, LOD objects <Prop>,
<Prop>_LOD1, ...) and work/<prop>_meta.json from the raw converter GLBs, with the isle props project's helpers (its
scripts/blib.py, paths pointed at this project): Dark Passageway's build (Yanmir's Fort's: asset frame = the raw
import mirrored in X, clean, faces wound to agree with the ABC's authored normals, open pieces on a double-sided copy
of their material, normals smooth within 40 degrees, COLOR_0 vertex occlusion, base centre at the origin; LODs only
from 1000 triangles: the native ABC LOD when its count is near, else a collapse decimation; one material per MM9 skin;
closed pieces wound outwards).

Here only `sconce2`, the 20 Torch-class wall sconces (a demon's head with horns on the wall, SCONCE2 / Sconce2.dtx):
orange flame cards of the shared CC0 Flame02 flipbook (the isle's, unrecoloured; MM9's FireColor is orange-yellow
220,180,0 -> 255,215,0), seated on the head's crown (the 2026-10-30 fix; Chasm of the Dead's blue `bluesconce` took the
same seat): MM9's Torch fire starts at the object origin + FireOffset (0, 2, 0) LT, inside the head at the chin, and its
particles rise out through the crown, so the visible flame stands on the crown. The crown is found from the mesh
(crown_seat: the highest vertex near the head's centre line, the horns excluded), printed, and checked from the side in
review/sconce2/closeup_*.png. The sconce hangs on a wall: its vertex occlusion has no floor (Chasm's `hung`).
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
SPECS.update({name: {"tilt": tilt} for name, tilt in props_table.TILTS.items() if name in SPECS})
ORB_RADIUS_M = 5.5 * 2.56 / blib.UNITS_PER_METRE
ORBS = set()
# Flame cards: (x offset, width, bottom, top, mirrored) in metres of the model before its placement scale, from the
# seat. The Anskram torch's cards (Chasm's TORCH_FLAME, MM9 gives every torch the same FireScale 1 fire, which the
# prop's Scale does not enlarge) divided by this sconce's Scale 1.5, so the placed flame is the Anskram wall torch's.
TORCH_FLAME = [(-0.03, 0.30, -0.05, 0.42, False), (0.04, 0.26, -0.05, 0.34, True)]
SCONCE_SCALE = 1.5
FLAMES = {'sconce2': [tuple(v / SCONCE_SCALE if isinstance(v, float) else v for v in card) for card in TORCH_FLAME]}
SEATS = {'sconce2': 'crown'}
HUNG = {'sconce2'}
OPAQUE = set()
for name in ORBS & set(SPECS):
    SPECS[name]['orb'] = True
for name, cards in FLAMES.items():
    if name in SPECS:
        SPECS[name]['flame'] = cards
        SPECS[name]['seat'] = SEATS.get(name)
for name in OPAQUE & set(SPECS):
    SPECS[name]['alpha'] = False
for name in HUNG & set(SPECS):
    SPECS[name]['hung'] = True
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
    before_actions = set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=path, merge_vertices=False)
    skins = []
    for o in [o for o in bpy.data.objects if o not in before and o.type == 'MESH']:
        for poly in o.data.polygons:
            material = o.data.materials[poly.material_index] if o.data.materials else None
            skins.append(int(material.name.rsplit('.', 1)[-1].split('_')[0]) if material else 0)
    for o in [o for o in bpy.data.objects if o not in before]:
        bpy.data.objects.remove(o, do_unlink=True)
    # this first import's actions too: else blib.import_raw's pose picks them by name ('stand', not 'stand.001'), and
    # an action whose slot belongs to the removed armature leaves the new one in its rest pose (Blender 5 slots)
    for a in [a for a in bpy.data.actions if a not in before_actions]:
        bpy.data.actions.remove(a)
    prop = os.path.basename(os.path.dirname(path))
    prop = prop if prop in SPECS else os.path.basename(os.path.dirname(os.path.dirname(path)))   # lod<n>/
    pose = props_table.POSES.get(prop)
    obj = blib.import_raw(path, name, origin, apply_armature=armature or pose is not None, pose=pose)
    for a in [a for a in bpy.data.actions if a not in before_actions]:      # its actions too (the LODs' poses)
        bpy.data.actions.remove(a)
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


def glow_seat(obj):
    """Centre of the ABC's flame-socket marker: the one-face loose piece (the Glow-Node triangle) of the raw import."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    singles = [f for f in bm.faces if all(len(e.link_faces) == 1 for e in f.edges)]
    if len(singles) != 1:
        raise SystemExit(f'{obj.name}: {len(singles)} one-face pieces, expected the Glow-Node marker only')
    seat = Vector(singles[0].calc_center_median())
    bm.free()
    print('GLOW SEAT', tuple(round(v * blib.UNITS_PER_METRE, 2) for v in seat))
    return seat


def crown_seat(obj):
    """The head's crown (asset frame, metres, before re-centring): the highest vertex within 12 % of the model's width
    of its centre line across (the horns stand out at the sides, so they are left out)."""
    pts = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = pts.min(0), pts.max(0)
    cx = (lo[0] + hi[0]) / 2
    near = pts[np.abs(pts[:, 0] - cx) < 0.12 * (hi[0] - lo[0])]
    top = near[near[:, 2].argmax()]
    seat = Vector((cx, float(top[1]), float(top[2])))
    print('CROWN SEAT (units, before centring)', tuple(round(v * blib.UNITS_PER_METRE, 2) for v in seat),
          'model z', round(lo[2] * blib.UNITS_PER_METRE, 2), '-', round(hi[2] * blib.UNITS_PER_METRE, 2),
          'y', round(lo[1] * blib.UNITS_PER_METRE, 2), '-', round(hi[1] * blib.UNITS_PER_METRE, 2))
    return seat


def mark_orb(obj, glow):
    """Face attribute 'orb' = 1 on the closed piece whose vertices all lie 0.9-1.1 orb radii from the glow socket (the
    ice orb the claw holds); pieces joined by vertex positions (the import does not weld UV seams)."""
    verts = np.array([v.co[:] for v in obj.data.vertices])
    keys = {}
    parent = list(range(len(verts)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i, v in enumerate(np.round(verts, 5)):
        k = tuple(v)
        if k in keys:
            parent[find(i)] = find(keys[k])
        else:
            keys[k] = i
    for poly in obj.data.polygons:
        a = find(poly.vertices[0])
        for j in poly.vertices[1:]:
            parent[find(j)] = a
    roots = np.array([find(i) for i in range(len(verts))])
    distance = np.linalg.norm(verts - np.array(glow[:]), axis=1) / ORB_RADIUS_M
    orb_roots = {r for r in set(roots.tolist()) if (roots == r).sum() >= 20
                 and np.all(np.abs(distance[roots == r] - 1.0) < 0.1)}
    values = np.array([1 if roots[p.vertices[0]] in orb_roots else 0 for p in obj.data.polygons], np.int32)
    layer = obj.data.attributes.new('orb', 'INT', 'FACE')
    layer.data.foreach_set('value', values)
    if not values.any():
        raise SystemExit(f'{obj.name}: no orb piece round the glow socket')


def flame_cards(cards, head, uv_name):
    """Camera-facing cards (openyamm_billboard in finish.py) of the shared Flame02 flipbook above `head` (the Anskram
    Keep's build)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new(uv_name)
    for cx, w, b, t, mirrored in cards:
        x0, x1 = head[0] + cx - w / 2, head[0] + cx + w / 2
        verts = [bm.verts.new(c) for c in ((x0, head[1], head[2] + b), (x1, head[1], head[2] + b),
                                            (x1, head[1], head[2] + t), (x0, head[1], head[2] + t))]
        f = bm.faces.new(verts)
        for loop, (u, v) in zip(f.loops, ((0, 1), (1, 1), (1, 0), (0, 0))):
            loop[uvl].uv = (1 - u if mirrored else u, (1 - v) * 0.8)
    me = bpy.data.meshes.new('Fire')
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new('Fire', me)
    bpy.context.scene.collection.objects.link(obj)
    attr = me.color_attributes.new('Color', 'FLOAT_COLOR', 'POINT')
    attr.data.foreach_set('color', np.ones(len(me.vertices) * 4, np.float32))
    me.color_attributes.active_color = attr
    return obj


def join(objects, name):
    for o in bpy.data.objects:
        o.select_set(o in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    objects[0].name = name
    objects[0].data.name = name
    return objects[0]


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
    glow = glow_seat(lod0) if spec.get('orb') else None
    crown = crown_seat(lod0) if spec.get('seat') == 'crown' else None
    if glow is not None:
        mark_orb(lod0, glow)
    dup, small = blib.clean(lod0)
    count0 = blib.triangles(lod0)
    levels = [lod0]
    if count0 >= LOD_MIN and spec.get('lods', True):
        natives = []
        for path in sources[1:]:
            o = import_raw(path, 'native', origin, armature)
            prepare(o, spec)
            if glow is not None:
                mark_orb(o, glow)
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
    head = None if glow is None else tuple(float(v) for v in (glow - centre))
    seat = None if head is None else (head[0], head[1], head[2] + 0.75 * ORB_RADIUS_M)
    if crown is not None:
        seat = tuple(float(v) for v in (crown - centre))
    if spec.get('orb'):
        orb_material = mats[0][0].copy()
        orb_material.name = f'{prop}_orb'
    if spec.get('flame'):
        fire_material = blib.texture_material('Fire', 'flame02_basecolor.png', alpha=True)
        fire_material.use_backface_culling = False
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
        if spec.get('orb'):
            obj.data.materials.append(orb_material)
        orb = np.zeros(len(obj.data.polygons), np.int32)
        if 'orb' in obj.data.attributes:
            obj.data.attributes['orb'].data.foreach_get('value', orb)
            obj.data.attributes.remove(obj.data.attributes['orb'])
        opened = open_faces(obj)
        for p in obj.data.polygons:
            k = int(min(max(skins[p.index], 0), len(mats) - 1))
            p.material_index = 2 * len(mats) if orb[p.index] else 2 * k + (1 if p.index in opened else 0)
        if spec.get('orb'):
            print('ORB FACES', name, int(orb.sum()), 'of', len(obj.data.polygons))
        if 'skin' in obj.data.attributes:
            obj.data.attributes.remove(obj.data.attributes['skin'])
        blib.smooth(obj, SMOOTH)
        size = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
        if spec.get('hung'):
            blib.pl.vertex_occlusion(obj, rays=48, distance=0.15 * size, strength=0.55, floor=False)
        else:
            blib.occlusion(obj, distance=0.15 * size, strength=0.55)
        if spec.get('flame'):
            fire = flame_cards(spec['flame'], seat, obj.data.uv_layers.active.name)
            fire.data.materials.append(fire_material)
            obj = join([obj, fire], name)
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
            'flame_head_m': list(seat) if spec.get('flame') else None, 'glow_socket_m': list(head) if head else None,
            'materials': [m.name for m in finished[0].data.materials]}
    with open(os.path.join(blib.WORK, f'{prop}_meta.json'), 'w') as f:
        json.dump(meta, f, indent=1)
    print('BUILT', prop, counts, 'height', round(meta['height_units'], 1), meta['materials'])


def fix_closed_parts(obj):
    """Reverse the closed pieces whose volume is negative (the coffins' lid pins, a bone of the bone pile: the ABC's
    authored normals point in; check_winding.py refuses them)."""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.faces.ensure_lookup_table()
    seen = set()
    for face in bm.faces:
        if face.index in seen:
            continue
        stack, piece = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            piece.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        if any(len(e.link_faces) != 2 for f in piece for e in f.edges):
            continue
        volume = 0.0
        for f in piece:
            verts = [v.co for v in f.verts]
            for k in range(1, len(verts) - 1):
                volume += verts[0].dot(verts[k].cross(verts[k + 1]))
        if volume < 0.0:
            bmesh.ops.reverse_faces(bm, faces=piece)
    bm.to_mesh(obj.data)
    bm.free()


_smooth = blib.smooth


def smooth(obj, angle):
    fix_closed_parts(obj)
    return _smooth(obj, angle)


blib.smooth = smooth


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    for prop in args or sorted(SPECS):
        build(prop)


main()
