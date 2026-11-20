"""MM7 skull decorations from the MM6 bones batch's Meshy skull and skeleton (read only, ../../../mm6_dungeons_3d/
bones/work/skull_tex.blend and skeleton_tex.blend):

- `7dec20` (1 placement, 7d28): a large skull seen from the front, ivory with brown spots. The Meshy skull (cranium
  with its fused jaw and 21 separate teeth) on the big_skull texture set; LODs by per-piece decimation (teeth drop at
  LOD2).
- `7dec18` (13 placements in 5 dungeons): a skull without its lower jaw resting on a flat pile of loose bones (long
  bones, pelvis, ribs, vertebrae, hand and foot bones, the jaw lying apart at the right). The Meshy skull is cut at
  the bite (its jaw is fused: everything below the upper teeth in the front half becomes the loose jaw); the bones
  are pieces of the Meshy skeleton scaled to a 220-unit body, each laid on its broad side and dropped (ray casts) at
  the lowest of six random spots, tipped onto its far end; then the skull (2.8 x the asset, as the sprite paints it)
  and the jaw are lowered onto the pile.

COLOR_0 = vertex occlusion with the floor; the textures (bones_textures.py) are graded to the sprites / their
expected occlusion. Writes work/<prop>.blend and work/<prop>_export.glb.
Usage: blender --background --python build_bones.py -- <7dec20|7dec18>"""
import math
import os
import random
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402
import skel_pose as P  # noqa: E402

pl, u = dlib.pl, dlib.u
PROP = sys.argv[sys.argv.index('--') + 1]
SKULL_BLEND = os.path.join(dlib.MM6_BONES, 'work', 'skull_tex.blend')
BITE_Z = 4.2 / dlib.UNITS_PER_METRE          # the upper teeth's lower edge (skull asset metres)


def load_skull():
    with bpy.data.libraries.load(SKULL_BLEND) as (src, dst):
        dst.objects = ['skull']
    skull = dst.objects[0]
    bpy.context.scene.collection.objects.link(skull)
    skull.data = skull.data.copy()
    return skull


def set_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0


def piece_labels(obj):
    label, count = P.pieces(obj)
    return label, count


def lods_by_pieces(high, targets, minimum, drop):
    """Per-piece decimated copies of `high` (loose pieces), small pieces dropped at the far levels."""
    out = []
    for level, target in enumerate(targets):
        dup = P.blib.duplicate(high, f'L{level}')
        if drop[level]:
            P.drop_small(dup, drop[level])
        dup = P.decimate_pieces(dup, target, minimum[level])
        out.append(dup)
    return out


def finish(lods, name, rays=(48, 32, 16, 12), distance=12, strength=0.55):
    for k, obj in enumerate(lods):
        obj.name = name if k == 0 else f'{name}_LOD{k}'
        obj.data.name = obj.name
        for p in obj.data.polygons:
            p.use_smooth = True
        bpy.context.view_layer.objects.active = obj
        for o in bpy.data.objects:
            o.select_set(o is obj)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(50))
        occ = pl.vertex_occlusion(obj, rays=rays[k], distance=u(distance), strength=strength, floor=True)
        if 'core' in obj.data.attributes:                 # the heap's core: darker, its crevices only show
            flag = np.empty(len(obj.data.vertices), np.float32)
            obj.data.attributes['core'].data.foreach_get('value', flag)
            colour = obj.data.color_attributes['Color']
            c = np.empty(len(obj.data.vertices) * 4, np.float32); colour.data.foreach_get('color', c)
            c = c.reshape(-1, 4)
            c[flag > 0.5, :3] *= CORE_SHADE
            colour.data.foreach_set('color', c.ravel())
            obj.data.attributes.remove(obj.data.attributes['core'])
        print('LEVEL', k, obj.name, 'tris', pl.triangles(obj), 'occlusion', round(occ, 3))
    dlib.save(PROP, lods)


# ---------------------------------------------------------------- 7dec20
def big_skull():
    pl.reset()
    mat = dlib.material('Skull', 'big_skull', extras={'openyamm_specular': 0.35})
    skull = load_skull()
    set_material(skull, mat)
    skull.data.transform(Matrix.Diagonal((1.16, 1.0, 0.94, 1.0)))     # the sprite's broader, shorter skull
    lods = lods_by_pieces(skull, (5400, 2200, 800, 260), (8, 6, 4, 4), (0, 0, 200, 200))
    bpy.data.objects.remove(skull)
    finish(lods, 'Skull', distance=8, strength=0.75)


# ---------------------------------------------------------------- 7dec18
SKELETON_HEIGHT = 220.0
SKULL_SCALE = 2.8                     # skull asset (15.6 units wide) -> 44 units, the sprite's skull
# skeleton pieces (indices of skel_pose.pieces on the rest mesh, classified by bone; see README)
# (pieces may repeat: a pile holds more than one body's bones; the Meshy ribs are thin strips that read as shards
# at these triangle counts, so the heap has none)
PILE_PIECES = {
    'femur': [4, 45, 4], 'tibia': [36, 11, 36], 'fibula': [15, 50], 'humerus': [37, 75, 37, 75],
    'forearm': [18, 44, 25, 94, 18], 'ribs': [], 'vertebrae': [33, 107, 91, 78, 33, 107, 91],
    'hand': [100, 79, 72, 105], 'foot': [21, 98],
}
MOUND = (40.0, 17.0)                  # half extents (x, y) of the heap's footprint (map units)
CORE = (32.0, 12.0, 11.0)             # the earth-and-bone-dust core under the bones: half extents and height
CORE_SHADE = 0.4                      # COLOR_0 factor on the core: only its dark crevices show between the bones
LONG = 25.0                           # pieces longer than this lie roughly along x, as the sprite's


def split_pieces(obj):
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.separate(type='LOOSE'); bpy.ops.object.mode_set(mode='OBJECT')
    return list(bpy.context.selected_objects)


def origin_to_geometry(obj):
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')


SKULL_YAW = 25.0                      # degrees: the face turned toward the viewer's right
SKULL_SINK = 9.0                      # map units the skull settles into the pile below its first contact


def lay_flat(obj, yaw, tilt):
    """Turn a piece so its thinnest principal axis is vertical (it lies on its broad side), then yaw and tilt it,
    centred on its own bounds."""
    co = np.array([v.co[:] for v in obj.data.vertices])
    c = co.mean(0)
    _, _, vt = np.linalg.svd(co - c, full_matrices=False)
    basis = Matrix([list(vt[0]), list(vt[1]), list(np.cross(vt[0], vt[1]))])   # rows: long, mid, thin axes
    rot = Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(tilt), 4, 'X') @ \
        basis.to_4x4()
    obj.data.transform(rot @ Matrix.Translation(-Vector(c)))
    obj.data.update()


def gaps(points, trees):
    """Downward clearance (metres) of each point to the floor or the trees below it."""
    out = points[:, 2].copy()
    down = Vector((0, 0, -1))
    for i, p in enumerate(points):
        for tree in trees:
            hit, *_ = tree.ray_cast(Vector(p), down)
            if hit is not None:
                out[i] = min(out[i], p[2] - hit.z)
    return out


def drop(obj, x, y, placed, sink=0.0, tip=True):
    """Move a piece (mesh coordinates, metres) to (x, y) map units and let it settle on the floor or the pieces
    already placed: lowered until its first contact, then (tip) turned about that contact along its long axis
    until its other end touches too, then sunk `sink` units (bones nest into each other). Returns its top z."""
    from mathutils.bvhtree import BVHTree
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo, hi = co.min(0), co.max(0)
    obj.data.transform(Matrix.Translation(Vector((u(x) - (lo[0] + hi[0]) / 2, u(y) - (lo[1] + hi[1]) / 2,
                                                  u(200) - lo[2]))))
    trees = [BVHTree.FromPolygons([v.co[:] for v in o.data.vertices], [p.vertices[:] for p in o.data.polygons])
             for o in placed]
    co = np.array([v.co[:] for v in obj.data.vertices])
    g = gaps(co, trees)
    obj.data.transform(Matrix.Translation((0, 0, -g.min())))
    co[:, 2] -= g.min(); g -= g.min()
    if tip:
        xy = co[:, :2] - co[:, :2].mean(0)
        d = np.linalg.svd(xy, full_matrices=False)[2][0]
        t = xy @ d
        span = t.max() - t.min()
        pivot = int(np.argmin(g))
        other = t > t[pivot] if t[pivot] < t.mean() else t < t[pivot]
        far = other & (np.abs(t - t[pivot]) > 0.5 * span)
        if far.any():
            # the far end falls until one of its points touches: smallest angle over the far points
            dist = np.abs(t[far] - t[pivot])
            angle = float(np.min(np.arctan2(g[far], dist)))
            axis = Vector((-d[1], d[0], 0.0)) * (1 if t[pivot] < t.mean() else -1)
            pv = Vector(co[pivot])
            rot = Matrix.Translation(pv) @ Matrix.Rotation(angle, 4, axis) @ Matrix.Translation(-pv)
            obj.data.transform(rot)
            co = np.array([v.co[:] for v in obj.data.vertices])
            g = gaps(co, trees)
            if g.min() > 0:
                obj.data.transform(Matrix.Translation((0, 0, -g.min())))
    obj.data.transform(Matrix.Translation((0, 0, -u(sink))))
    obj.data.update()
    return max(v.co.z for v in obj.data.vertices)


def core_mound(skull_uv):
    """A flattened dome under the bones (closes the gaps; reads as the dark crevices of a dense heap)."""
    a, b, h = CORE
    profile = [(1.0, 0.0), (0.95, 0.3), (0.75, 0.7), (0.4, 0.92), (0.0, 1.0)]       # rim flush with the floor
    obj = pl.lathe('Core', [(u(r), u(z * h)) for r, z in profile], 16, None, smooth=True)
    obj.data.transform(Matrix.Diagonal((a, b, 1.0, 1.0)))
    for d in obj.data.uv_layers[0].data:
        d.uv = skull_uv
    attr = obj.data.attributes.new('core', 'FLOAT', 'POINT')
    attr.data.foreach_set('value', np.ones(len(obj.data.vertices), np.float32))
    return obj


def pile():
    # bones: the rest skeleton (this opens its blend)
    obj, joints = P.load_rest(SKELETON_HEIGHT)
    label, count = P.pieces(obj)
    bone_mat = dlib.material('Bone', 'pile_bone', extras={'openyamm_specular': 0.35})
    skull_mat = dlib.material('Skull', 'pile_skull', extras={'openyamm_specular': 0.35})
    set_material(obj, bone_mat)
    parts = []
    for k in [k for ks in PILE_PIECES.values() for k in ks]:
        dup = P.blib.duplicate(obj, f'piece{k}')
        bm = bmesh.new(); bm.from_mesh(dup.data); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if label[v.index] != k], context='VERTS')
        bm.to_mesh(dup.data); bm.free()
        parts.append(dup)
    for o in list(bpy.data.objects):
        if o not in parts:
            bpy.data.objects.remove(o)
    rng = random.Random(4)
    parts.sort(key=lambda o: -len(o.data.vertices))
    for part in parts:
        co = np.array([v.co[:] for v in part.data.vertices])
        long = np.ptp(co, 0).max() * dlib.UNITS_PER_METRE > LONG
        yaw = rng.uniform(-35, 35) + rng.choice((0, 180)) if long else rng.uniform(0, 360)
        lay_flat(part, yaw, rng.uniform(-10, 10))
    # the skull, its jaw cut away
    skull = load_skull()
    set_material(skull, skull_mat)
    skull.data.transform(Matrix.Scale(SKULL_SCALE, 4))
    bite = BITE_Z * SKULL_SCALE
    jaw = P.blib.duplicate(skull, 'Jaw')
    for target, inside in ((skull, False), (jaw, True)):
        bm = bmesh.new(); bm.from_mesh(target.data); bm.verts.ensure_lookup_table()
        doomed = [v for v in bm.verts if (v.co.z < bite and v.co.y < u(2.0) * SKULL_SCALE) != inside]
        bmesh.ops.delete(bm, geom=doomed, context='VERTS')
        bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)   # close the cut
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        bm.to_mesh(target.data); bm.free()
    side = max(skull.data.vertices, key=lambda v: v.co.x).index      # a plain texel on the cranium's side
    skull_uv = next(tuple(skull.data.uv_layers[0].data[li].uv) for p in skull.data.polygons
                    for li in p.loop_indices if skull.data.loops[li].vertex_index == side)
    core = core_mound(skull_uv)
    set_material(core, skull_mat)
    placed = [core]
    # pack the bones into a low heap: of 12 spots in the footprint, the one where the piece comes to rest lowest
    ribs = {id(p) for p in parts if p.name.split('.')[0] in {f'piece{k}' for k in PILE_PIECES['ribs']}}
    for i, part in enumerate(parts):
        rest = np.array([v.co[:] for v in part.data.vertices])
        tip = id(part) not in ribs                            # curved ribs stay flat (tipping stands them up)
        best = None
        for _ in range(12):
            r, t = math.sqrt(rng.random()), rng.uniform(0, 2 * math.pi)
            x, y = MOUND[0] * r * math.cos(t), MOUND[1] * r * math.sin(t)
            part.data.vertices.foreach_set('co', rest.ravel())
            top = drop(part, x, y, placed, sink=1.5, tip=tip)
            if best is None or top < best[0]:
                best = (top, x, y)
        part.data.vertices.foreach_set('co', rest.ravel())
        _, x, y = best
        drop(part, x, y, placed, sink=1.5, tip=tip)
        placed.append(part)
    # skull: facing the viewer, turned to the sprite's right, sitting in the heap left of centre; the jaw at the
    # right front
    skull.data.transform(Matrix.Rotation(math.radians(SKULL_YAW), 4, 'Z') @ Matrix.Rotation(math.radians(-6), 4, 'X'))
    drop(skull, -3, 0, placed, sink=SKULL_SINK, tip=False)
    jaw.data.transform(Matrix.Rotation(math.radians(-35), 4, 'Z') @ Matrix.Rotation(math.radians(12), 4, 'Y'))
    drop(jaw, 36, -20, placed + [skull], sink=2.0, tip=False)
    bones = pl.join('PileBones', parts)
    head = pl.join('PileSkull', [skull, jaw])
    co = np.array([v.co[:] for o in (bones, head, core) for v in o.data.vertices])
    centre = (co.min(0) + co.max(0)) / 2
    for o in (bones, head, core):
        o.data.transform(Matrix.Translation((-centre[0], -centre[1], 0.0)))
        o.data.update()
    print('HIGH', pl.triangles(bones), pl.triangles(head), 'bounds',
          ((co.max(0) - co.min(0)) * dlib.UNITS_PER_METRE).round(1))
    bone_lods = lods_by_pieces(bones, (2700, 1250, 470, 170), (24, 12, 6, 4), (0, 0, 40, 90))
    head_lods = lods_by_pieces(head, (1100, 480, 180, 70), (10, 6, 4, 4), (0, 0, 200, 200))
    core_lods = [core] + [P.blib.duplicate(core, f'Core{k}') for k in range(1, 4)]
    for k, c in enumerate(core_lods[2:], 2):
        P.decimate_pieces(c, 40 if k == 2 else 20, 4)
    core_lods = [o for o in bpy.data.objects if o.name.startswith('Core')]
    core_lods.sort(key=lambda o: o.name)
    lods = [pl.join(f'PileL{k}', [bone_lods[k], head_lods[k], core_lods[k]]) for k in range(4)]
    for o in (bones, head):
        bpy.data.objects.remove(o)
    finish(lods, 'Bones', strength=0.75)


if PROP == '7dec20':
    big_skull()
elif PROP == '7dec18':
    pile()
