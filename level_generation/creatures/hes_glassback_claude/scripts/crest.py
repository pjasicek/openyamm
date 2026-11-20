"""Glass crest of the Glassback: procedural faceted crystals (crystals.py) placed on the rest-pose hide, three sizes.
Args: -- <anim.blend> <out.blend>

Layout (from the concept sheet and references_hd/crest.png): a midline row from behind the head to the tail, tallest
over the shoulders; flanking rows over the shoulders (two per side) and the mid back (one per side); three small
spines on the back of the head. Each crystal stands on the surface point found by a ray down onto the hide, its axis
between the surface normal and up, raked back; its root is sunk 1.3 radii into the hide.
Sizes (per tier, actors.yml attachments): short (Pup: height x0.5, stubby, rounder, no outer shoulder row), full (Glassback), tall (Bull: x1.3,
more lean and twin points). Every crystal belongs to the bone that dominates the hide under its root (Head, Neck1,
Spine1..3, Tail1/2): one rigid attachment per bone. Objects Crest_<size>_<bone>[_LOD1..3] are parented to their bone
(review renders and the clearance check) and exported by crest_export.py. LODs: 1 no cracks, 5-sided at most;
2 no seams, 4-sided, the smallest third dropped; 3 three-sided, only the largest half."""
import bpy, os, sys, math, random
import bmesh
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import crystals

src, dst = sys.argv[sys.argv.index('--') + 1:][:2]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]; body = bpy.data.objects[C.MESH]
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data
bvh = BVHTree.FromObject(body, bpy.context.evaluated_depsgraph_get())
names = {g.index: g.name for g in body.vertex_groups}
dom = [names[max(v.groups, key=lambda g: g.weight).group] for v in me.vertices]
co = [v.co.copy() for v in me.vertices]
from mathutils import kdtree
kd = kdtree.KDTree(len(co))
for i, c in enumerate(co):
    kd.insert(c, i)
kd.balance()
def hide_hit(origin, direction):
    hit = bvh.ray_cast(Vector(origin), Vector(direction).normalized(), 1.0)
    return hit[0]


ALLOWED = ('Head', 'Neck1', 'Spine1', 'Spine2', 'Spine3', 'Tail1')   # one attachment (two draws) per bone: the tail
# beyond Tail1 keeps its own pointed plates


def height_mid(y):
    """Midline spine height (m) along the body for the full crest (shoulders y -0.55 tallest)."""
    pts = [(-1.10, 0.07), (-0.95, 0.15), (-0.70, 0.28), (-0.50, 0.31), (-0.25, 0.27), (0.05, 0.23), (0.35, 0.19),
           (0.65, 0.14), (0.90, 0.10), (1.15, 0.07), (1.32, 0.045)]
    ys, hs = zip(*pts)
    return float(np.interp(y, ys, hs))


rng = random.Random(1022)
SPECS = []                      # (x, y, height, row); polish 2026-10-22: fewer, chunkier plates (30 instead of 53)
for y in np.arange(-0.96, 0.98, 0.165):
    SPECS.append((0.0, float(y) + rng.uniform(-0.02, 0.02), height_mid(y), 'mid'))
for y in (-0.80, -0.58, -0.36):
    for s in (1, -1):
        SPECS.append((s * (0.19 + rng.uniform(-0.02, 0.02)), y + rng.uniform(-0.02, 0.02), height_mid(y) * 0.72, 'lat1'))
for y in (-0.68, -0.46):
    for s in (1, -1):
        SPECS.append((s * (0.34 + rng.uniform(-0.01, 0.02)), y + rng.uniform(-0.02, 0.02), height_mid(y) * 0.48, 'lat2'))
for y in (-0.08, 0.20, 0.48):
    for s in (1, -1):
        SPECS.append((s * (0.17 + rng.uniform(-0.02, 0.02)), y + rng.uniform(-0.02, 0.02), height_mid(y) * 0.55, 'lat1'))
for x, y in ((0.07, -1.11), (-0.07, -1.11)):
    SPECS.append((x, y, 0.06, 'head'))

RADIUS = 0.52                  # base radius per metre of height (0.42 before the polish: thin needles)
SIZES = {'short': (0.5, 0.9, 0.5), 'full': (1.0, 1.0, 1.0), 'tall': (1.3, 1.05, 1.6)}
placed = []
for i, (x, y, h, row) in enumerate(SPECS):
    hit = bvh.ray_cast(Vector((x, y, 3.0)), Vector((0, 0, -1)))
    if hit[0] is None:
        continue
    p, n = hit[0], hit[1].normalized()
    if n.z < 0.2:
        continue
    _, vi, _ = kd.find(p)
    bone = dom[vi]
    if bone.startswith('Tail') and bone not in ALLOWED:
        continue
    if bone not in ALLOWED:
        bone = 'Spine3' if y < -0.4 else 'Spine2' if y < 0.1 else 'Spine1'
    axis = (n * 0.45 + Vector((0, 0, 1)) * 0.55 + Vector((0, 0.22, 0))).normalized()
    placed.append(dict(p=p, axis=axis, h=h, row=row, bone=bone, seed=i, sides=7 if h > 0.2 else 6 if h > 0.1 else 5))
print('CREST crystals', len(placed), 'bones', sorted({c['bone'] for c in placed}))


def build(size, lod):
    hs, rs, jag = SIZES[size]
    groups = {}
    hmax = max(c['h'] for c in placed)
    for c in placed:
        if lod >= 2 and c['h'] < 0.12 and c['row'] != 'mid':
            continue
        if lod >= 3 and c['h'] < 0.5 * hmax:
            continue
        if size == 'short' and (c['row'] == 'lat2' or c['h'] < 0.09):
            continue                     # the Pup: fewer plates (no outer shoulder row, no tiny ones)
        r = rng_local = random.Random(c['seed'] * 7 + 1)
        h = c['h'] * hs
        radius = max(0.035, min(0.15, RADIUS * c['h'])) * rs
        sides = {0: c['sides'], 1: min(c['sides'], 5), 2: 4, 3: 3}[lod]
        if size == 'short':
            h = max(h, radius * 0.9)     # stubby: about half the full crest's height (radius*1.6 floor made it 0.7)
            sides = min(sides + 1, 7)    # rounder
        axis = c['axis'].copy()
        tilt = 0.12 * jag
        axis = (axis + Vector((r.uniform(-tilt, tilt), r.uniform(-tilt, tilt), 0))).normalized()
        bm = groups.setdefault(c['bone'], bmesh.new())
        crystals.crystal(bm, c['p'], axis, h, radius, sides, r, lod=lod, crack_count=3 if c['h'] > 0.15 else 2,
                         seam=lod <= 1, twist=r.uniform(-0.3, 0.3), glow_scale=1.0, long_dir=(0, 1, 0),
                         aspect=(1.3, 0.85), edge_glow=2 if c['h'] > 0.12 else 1, hide_hit=hide_hit)
        if size == 'tall' and c['h'] > 0.18 and lod <= 1:
            # a second, leaning point beside the big spines: the Bull's jagged crest
            side = Vector((r.choice((-1, 1)) * 1.0, 0.3, 0)).normalized()
            a2 = (axis + side * 0.35).normalized()
            crystals.crystal(bm, c['p'] + side * radius * 0.7, a2, h * 0.55, radius * 0.6, 4, r, lod=lod,
                             crack_count=1, seam=False, twist=r.uniform(0, 3.14))
    objs = []
    for bone, bm in groups.items():
        name = f'Crest_{size}_{bone}' + (f'_LOD{lod}' if lod else '')
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh); bm.free()
        ob = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        for m in ('Glass', 'Glow'):
            mesh.materials.append(bpy.data.materials.get(m) or bpy.data.materials.new(m))
        ob.parent = rig
        ob.parent_type = 'BONE'
        ob.parent_bone = bone
        bpy.context.view_layer.update()
        ob.matrix_world = Matrix.Identity(4)
        objs.append(ob)
    return objs


import json
json.dump([{'p': list(c['p']), 'axis': list(c['axis']), 'radius': max(0.035, min(0.15, RADIUS * c['h'])), 'bone': c['bone'],
            'h': c['h'], 'row': c['row']} for c in placed], open(C.path('work/crest_layout.json'), 'w'), indent=0)
glass = bpy.data.materials.new('Glass'); glass.diffuse_color = (0.05, 0.055, 0.065, 1)
glow = bpy.data.materials.new('Glow'); glow.diffuse_color = (0.3, 1.0, 0.85, 1)
report = {}
for size in SIZES:
    for lod in range(4):
        objs = build(size, lod)
        tris = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
        report[(size, lod)] = tris
        print('CREST', size, 'LOD', lod, 'tris', tris, 'pieces', len(objs))
bpy.ops.wm.save_as_mainfile(filepath=C.path(dst))
