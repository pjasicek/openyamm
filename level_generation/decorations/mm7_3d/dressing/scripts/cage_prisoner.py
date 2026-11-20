"""7dec07's prisoner: the MM6 native male creature (assets_source/worlds/mm6/models/mm6_natm.glb, read only:
bare-chested, loincloth) posed standing in the MM7 cage with its legs apart and both arms up gripping the bars, as
the sprite paints him: his right arm (screen left) high up the left bars, his left arm out to the right with the
forearm raised to a bar. Posing with the MM6 leftovers batch's world-space bone operations
(../../../mm6_dungeons_3d/leftovers/scripts/corpse_pose.py, read only). The feather mantle and the feathered necklace
(grey texels above the waist) are dropped: the sprite's prisoner wears only a loincloth. The baked, welded mesh is
collapse-decimated into four levels.
Cage frame in map units: cage axis at x = y = 0, cage floor at z = 12, front (camera) toward -y.
Writes work/prisoner.blend (objects Prisoner_L0..L3, material Prisoner on textures/cage_prisoner_*).
Usage: blender --background --python cage_prisoner.py -- [--preview]"""
import colorsys
import math
import os
import sys

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dlib  # noqa: E402

sys.path.insert(0, os.path.join(dlib.DECO, 'mm6_dungeons_3d', 'leftovers', 'scripts'))
import corpse_pose as cp  # noqa: E402

pl = dlib.pl
U = 1 / dlib.UNITS_PER_METRE
SOURCE = os.path.join(dlib.MODELS_MM6, 'mm6_natm.glb')
STANDING = 106.0          # rest height in map units (feet to crown): crown about 116 above the cage bottom
FLOOR = 12.0
LOD_TRIS = (3300, 1500, 600, 320)
POSE = [
    # legs apart (screen left is his right), knees nearly straight
    ('aim', 'B_L_Thigh', (0.5, -0.04, -1.0), 1.0),
    ('aim', 'B_L_Calf', (0.30, 0.02, -1.0), 1.0),
    ('aim', 'B_R_Thigh', (-0.48, -0.02, -1.0), 1.0),
    ('aim', 'B_R_Calf', (-0.32, 0.04, -1.0), 1.0),
    ('rot', 'B_Spine1', (0, 1, 0), 4),                   # the trunk leans a little toward his raised arm
    ('rot', 'B_Head', (0, 1, 0), 8),
    ('rot', 'B_Head', (1, 0, 0), -6),                    # chin slightly down
    # right arm (screen left): high, hand on the bars up at the left
    ('aim', 'B_R_UpperArm', (-0.68, 0.12, 0.72), 1.0),
    ('aim', 'B_R_Forearm', (-0.35, 0.18, 0.92), 1.0),
    ('aim', 'B_R_Hand', (-0.35, 0.25, 0.9), 1.0),
    # left arm (screen right): elbow out to the side, forearm up to a bar
    ('aim', 'B_L_UpperArm', (0.95, 0.15, 0.24), 1.0),
    ('aim', 'B_L_Forearm', (0.3, 0.22, 0.92), 1.0),
    ('aim', 'B_L_Hand', (0.25, 0.35, 0.9), 1.0),
]
FINGER_CURL = 70            # degrees per joint about the hand's across axis: fists round the bars


def curl(arm, side):
    """Bend each finger's three joints toward the palm (thumbs half as much)."""
    hand = arm.pose.bones[f'B_{side}_Hand']
    across = (arm.matrix_world.to_3x3() @ (hand.matrix.to_3x3() @ Vector((1, 0, 0)))).normalized()
    names = [b.name for b in arm.pose.bones if b.name.startswith(f'B_{side}_Finger')]
    for name in sorted(names):
        amount = FINGER_CURL * (0.5 if name.startswith(f'B_{side}_Finger0') else 1.0)
        cp.pose(arm, [('rot', name, tuple(across), amount if side == 'L' else -amount)])


def drop_mantle(obj, image):
    """Delete grey-texel faces (feathers) above the waist, and behind the body down to the knees: the mantle."""
    w, h = image.size
    px = np.empty(w * h * 4, np.float32); image.pixels.foreach_get(px); px = px.reshape(h, w, 4)
    uv = obj.data.uv_layers[0].data
    waist = None
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    layer = bm.loops.layers.uv[0]
    zs = np.array([v.co.z for v in bm.verts]); waist = zs.min() + (zs.max() - zs.min()) * 0.55
    knee = zs.min() + (zs.max() - zs.min()) * 0.25
    back = np.median([v.co.y for v in bm.verts]) + 3 * U
    drop = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.z < knee or (c.z < waist and c.y < back):
            continue
        cols = []
        for loop in f.loops:
            uu, vv = loop[layer].uv
            cols.append(px[min(h - 1, int((vv % 1) * h)), min(w - 1, int((uu % 1) * w)), :3])
        r, g, b = np.mean(cols, 0)
        _, s, v = colorsys.rgb_to_hsv(r, g, b)
        if s < 0.3 and v > 0.12:
            drop.append(f)
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    print('MANTLE faces dropped', len(drop))


def stocky(r):
    """Radial remap about the cage axis (map units): the painted prisoner is a bulkier man than the creature, about
    1.25 x as broad, while his hands stay on the bars (radius 42 at most)."""
    if r <= 24.0:
        return r * 1.25
    return min(30.0 + (r - 24.0) * 0.75, 42.5)


def drop_islands(obj, min_faces):
    """Delete loose pieces with fewer faces than min_faces (eyes, teeth, small fringes at the far levels)."""
    bm = bmesh.new(); bm.from_mesh(obj.data); bm.faces.ensure_lookup_table()
    seen = set(); drop = []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack = [f]; island = []; seen.add(f.index)
        while stack:
            g = stack.pop(); island.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h.index not in seen:
                        seen.add(h.index); stack.append(h)
        if len(island) < min_faces:
            drop += island
    bmesh.ops.delete(bm, geom=drop, context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bm.to_mesh(obj.data); bm.free()


def decimate(obj, target):
    """Collapse toward target; when collapse stalls above it (seams, small pieces), keep the lowest count reached."""
    for o in bpy.data.objects:
        o.select_set(o is obj)
    bpy.context.view_layer.objects.active = obj
    for _ in range(6):
        count = pl.triangles(obj)
        if count <= target:
            break
        mod = obj.modifiers.new('D', 'DECIMATE'); mod.ratio = max(0.02, target / count * 0.98)
        mod.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    return pl.triangles(obj)


def main():
    preview = '--preview' in sys.argv
    pl.reset()
    arm, body = cp.load(SOURCE)
    scale = STANDING * U / 1.70
    arm.matrix_world = Matrix.Scale(scale, 4)
    bpy.context.view_layer.update()
    cp.pose(arm, POSE)
    curl(arm, 'L'); curl(arm, 'R')
    obj = cp.bake(arm, body, 'Prisoner')
    for o in (arm, body):
        bpy.data.objects.remove(o)
    co = np.array([v.co[:] for v in obj.data.vertices])
    lo = co.min(0)
    for v in obj.data.vertices:
        v.co.z += FLOOR * U - lo[2]
        r = math.hypot(v.co.x, v.co.y) / U
        if r > 1e-6:
            factor = stocky(r) / r
            v.co.x *= factor; v.co.y *= factor
    mat = dlib.material('Prisoner', 'cage_prisoner')
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0; p.use_smooth = True
    image = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE').image
    drop_mantle(obj, image)
    co = np.array([v.co[:] for v in obj.data.vertices]) / U
    print('PRISONER bounds', np.round(co.min(0), 1).tolist(), np.round(co.max(0), 1).tolist(), 'tris',
          pl.triangles(obj))
    radial = np.hypot(co[:, 0], co[:, 1])
    print('PRISONER max radius', round(float(radial.max()), 1))
    levels = []
    for k, target in enumerate(LOD_TRIS):
        dup = obj.copy(); dup.data = obj.data.copy(); bpy.context.scene.collection.objects.link(dup)
        dup.name = f'Prisoner_L{k}'
        if k >= 2:
            drop_islands(dup, (0, 0, 24, 60)[k])
        decimate(dup, target)
        cp.clean(dup)
        levels.append(dup)
    bpy.data.objects.remove(obj)
    print('LODS', [pl.triangles(o) for o in levels])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(dlib.WORK, 'prisoner.blend'))
    if preview:
        out = os.path.join(dlib.REVIEW, '7dec07'); os.makedirs(out, exist_ok=True)
        pl.setup_render((400, 600))
        pl.render_views([levels[0]], out, 'pose', views=((0, 6), (90, 6), (40, 22)))


main()
