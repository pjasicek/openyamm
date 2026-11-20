"""Builds the 6tree01 3D tree (work/tree.blend): Sapling skeleton -> bark meshes per LOD; leaf-cluster cards placed in
the sprite's canopy envelope -> leaf meshes per LOD. Objects Tree, Tree_LOD1, Tree_LOD2 (Bark + Leaves materials).
LOD3 (impostor) is made by bake_impostor.py. Inputs from prepare_inputs.py and make_leaf_atlas.py (work/).

Skeleton: Sapling Tree Gen (SAPLING below), trunk forking low into three limbs. Only splines at least BRANCH_MIN[lod]
thick are kept (twigs sit inside the canopy); each spline is converted on its own so its UVs can be scaled to a
0.5 m bark tile around and along; parts outside the canopy envelope are cut away; then decimated to the budget.
Canopy: the envelope is the 6tree01 sprite's half-width per height, revolved about the trunk (work/profile.json).
Cards (quads showing a leaf cluster) are drawn round ~48 lumps near the envelope surface plus inner filler; each
faces outward with a random tilt and roll. Vertex normals point outward from the canopy centre so the crown shades as
one volume. Cards deep inside use the darkened atlas row (baked occlusion). LOD1/LOD2 keep a farthest-point subset
of the LOD0 cards, scaled up (area-preserving) and pulled inward by the growth so the silhouette stays."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
H = 6.5                                    # tree height (m); the engine scales to the sprite height anyway
SAPLING = {"levels": 3, "scale": 4.6, "baseSplits": 2, "splitHeight": 0.42, "shape": "2",
           "branches": [0, 80, 15, 8], "length": [1.0, 0.3, 0.35, 0.3], "downAngle": [90, 50, 45, 45],
           "downAngleV": [0, 25, 10, 10], "segSplits": [0.15, 0.25, 0.3, 0], "splitAngle": [25, 15, 15, 0],
           "baseSize": 0.3, "ratio": 0.035, "curveRes": [6, 4, 3, 1], "resU": 2, "bevelRes": 1,
           "attractUp": [0, 0.6, 0.3, 0], "curve": [0, -20, 0, 0], "seed": 5, "rootFlare": 1.5}
BRANCH_MIN = {0: 0.017, 1: 0.035, 2: 0.07}            # first kept spline thickness (m); raised to meet the budget
BRANCH_BUDGET = {0: 1700, 1: 560, 2: 190}             # triangles
CARDS = {0: 3000, 1: 1180, 2: 390}
CARD_SIZE = (0.62, 0.92)                              # LOD0 card edge (m)
TILE = 0.5                                            # bark texture tile (m)
rng = np.random.default_rng(6101)

profile = np.array(json.load(open(os.path.join(WORK, 'profile.json')))['half_width_by_height'])


def R(z):
    """Envelope radius (m) at height z (m)."""
    return float(np.interp(z / H, profile[:, 0], profile[:, 1])) * H


CANOPY_LOW = 0.36 * H
CENTRE = Vector((0, 0, 0.62 * H))

# ---------------------------------------------------------------- skeleton
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
bpy.ops.curve.tree_add(do_update=True, bevel=True, showLeaves=False, useArm=False, prune=False, **SAPLING)
skel = bpy.data.objects['tree']; cu = skel.data
print('SAPLING splines', len(cu.splines))


def bezier_length(s):
    pts = s.bezier_points
    return sum((pts[i + 1].co - pts[i].co).length for i in range(len(pts) - 1))


def branch_mesh(lod, minimum=None):
    minimum = minimum or BRANCH_MIN[lod]
    parts = []
    for si, s in enumerate(cu.splines):
        thick = max(p.radius for p in s.bezier_points) * cu.bevel_depth
        if thick < minimum:
            continue
        c = cu.copy()
        for other in list(c.splines):
            c.splines.remove(other)
        ns = c.splines.new('BEZIER'); ns.bezier_points.add(len(s.bezier_points) - 1)
        for a, b in zip(s.bezier_points, ns.bezier_points):
            b.co = a.co; b.handle_left = a.handle_left; b.handle_right = a.handle_right; b.radius = a.radius
            b.handle_left_type = a.handle_left_type; b.handle_right_type = a.handle_right_type
        sides = (8 if thick > 0.08 else 6 if thick > 0.04 else 4) if lod == 0 else (6 if thick > 0.08 else 4)
        c.bevel_resolution = (sides - 4) // 2
        c.resolution_u = (3 if thick > 0.08 else 1) if lod == 0 else (2 if thick > 0.08 and lod == 1 else 1)
        o = bpy.data.objects.new('b', c); bpy.context.scene.collection.objects.link(o)
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        bpy.data.objects.remove(o, do_unlink=True); bpy.data.curves.remove(c)
        # UVs: u around (0..1) -> whole tiles round the circumference, v along (0..1) -> length / TILE
        around = max(1, round(2 * math.pi * thick * 0.8 / TILE)); along = max(bezier_length(s) / TILE, 0.3)
        uv = np.zeros(len(me.loops) * 2); me.uv_layers[0].data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        lo, hi = uv.min(0), uv.max(0); span = np.maximum(hi - lo, 1e-6)
        uv = (uv - lo) / span * np.array([around, along]); me.uv_layers[0].data.foreach_set('uv', uv.ravel())
        parts.append(me)
    bm = bmesh.new()
    for me in parts:
        bm.from_mesh(me); bpy.data.meshes.remove(me)
    # cut what pokes out of the canopy (twig tips beyond the envelope)
    out = [v for v in bm.verts if v.co.z > CANOPY_LOW and Vector((v.co.x, v.co.y)).length > R(v.co.z) * 0.97]
    bmesh.ops.delete(bm, geom=out, context='VERTS')
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'bark{lod}'); bm.to_mesh(me); bm.free()
    obj = bpy.data.objects.new(f'bark{lod}', me); bpy.context.scene.collection.objects.link(obj)
    tris = len(me.polygons)
    if tris > BRANCH_BUDGET[lod]:                    # drop the thinnest kept branches until within budget
        bpy.data.objects.remove(obj, do_unlink=True); bpy.data.meshes.remove(me)
        return branch_mesh(lod, minimum * 1.12)
    for p in obj.data.polygons:
        p.use_smooth = True
    print('BARK lod', lod, 'splines', len(parts), 'min thickness', round(minimum, 3), 'tris', tris)
    return obj


barks = {lod: branch_mesh(lod) for lod in (0, 1, 2)}
bpy.data.objects.remove(skel, do_unlink=True)

# ---------------------------------------------------------------- canopy cards
zs = np.linspace(CANOPY_LOW, H, 200)


def inside(p, margin=1.0):
    return CANOPY_LOW <= p[2] <= H and math.hypot(p[0], p[1]) <= R(p[2]) * margin


lumps = []
while len(lumps) < 48:
    z = rng.uniform(0.40, 0.95) * H; th = rng.uniform(0, 2 * math.pi); r = R(z) * rng.uniform(0.8, 1.0)
    lumps.append((np.array([r * math.cos(th), r * math.sin(th), z]), rng.uniform(0.6, 1.05)))
weights = np.array([l[1] ** 2 for l in lumps]); weights /= weights.sum()
cards = []                                            # centre, normal, roll, size, cell column, inner
while len(cards) < CARDS[0]:
    if rng.random() < 0.85:
        li = rng.choice(len(lumps), p=weights); c, rho = lumps[li]; lump = Vector(c)
        p = c + rng.normal(0, rho * 0.45, 3)
    else:
        z = rng.uniform(CANOPY_LOW + 0.3, H * 0.92); th = rng.uniform(0, 2 * math.pi)
        p = np.array([0, 0, z]) + R(z) * rng.uniform(0, 0.75) * np.array([math.cos(th), math.sin(th), 0])
        lump = None
    if not inside(p, 1.04 if lump is not None else 0.9):
        continue
    out = Vector(p) - CENTRE; out.z *= 1.15; out.normalize()
    n = (out + Vector(rng.normal(0, 0.35, 3))).normalized()
    depth = math.hypot(p[0], p[1]) / max(R(p[2]), 0.05)
    inner = depth < 0.55 or (p[2] < 0.40 * H and depth < 0.75)
    cards.append((Vector(p), n, rng.uniform(0, 2 * math.pi), rng.uniform(*CARD_SIZE), int(rng.integers(2)), inner, lump))
print('CARDS', len(cards), 'inner', sum(c[5] for c in cards))


def subset(count):
    """Farthest-point subset of the LOD0 cards (spatially even)."""
    pts = np.array([c[0] for c in cards]); chosen = [int(rng.integers(len(pts)))]
    dist = np.linalg.norm(pts - pts[chosen[0]], axis=1)
    for _ in range(count - 1):
        k = int(dist.argmax()); chosen.append(k); dist = np.minimum(dist, np.linalg.norm(pts - pts[k], axis=1))
    return [cards[k] for k in chosen]


def card_mesh(lod):
    sel = cards if lod == 0 else subset(CARDS[lod])
    grow = math.sqrt(CARDS[0] / CARDS[lod]) * (0.95 if lod else 1.0)
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    normals = []
    for centre, n, roll, size, col, inner, lump in sel:
        s = size * grow
        c = centre.copy()
        if lod:                                      # keep the silhouette: bigger cards sit further in
            radial = Vector((c.x, c.y, 0))
            if radial.length > 1e-3:
                c -= radial.normalized() * min((s - size) * 0.45, radial.length * 0.5)
            c.z = min(c.z, H - s * 0.42)
        t = n.orthogonal().normalized(); b = n.cross(t)
        rot = Matrix.Rotation(roll, 3, n)
        t = rot @ t; b = rot @ b
        corners = [c + (-t - b) * s / 2, c + (t - b) * s / 2, c + (t + b) * s / 2, c + (-t + b) * s / 2]
        vs = [bm.verts.new(p) for p in corners]
        f = bm.faces.new(vs)
        # Blender v up: image top row (outer) = v 0.5..1. Coarser LODs show fewer gaps into the dark interior, so more
        # of their cards take the darkened row to keep the crown's overall tone across LOD switches.
        if lod and not inner:
            depth = math.hypot(centre.x, centre.y) / max(R(centre.z), 0.05)
            inner = depth < 0.55 + 0.12 * lod or rng.random() < 0.12 * lod
        u0 = 0.5 * col; v0 = 0.0 if inner else 0.5
        for loop, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            loop[uvl].uv = (u0 + 0.5 * du, v0 + 0.5 * dv)
        for p in corners:                            # clump shading: lump normal blended with the crown's
            o = p - CENTRE; o.z *= 1.15; o.normalize()
            if lump is not None:
                o = (0.3 * o + 0.7 * (p - lump).normalized()).normalized()
            normals.append(o)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(f'leaves{lod}'); bm.to_mesh(me); bm.free()
    vn = [None] * len(me.vertices)
    for i, nn in enumerate(normals):
        vn[i] = nn
    me.normals_split_custom_set_from_vertices(vn)
    obj = bpy.data.objects.new(f'leaves{lod}', me); bpy.context.scene.collection.objects.link(obj)
    print('LEAVES lod', lod, 'cards', len(sel), 'tris', len(me.polygons), 'card size x', round(grow, 2))
    return obj


leaves = {lod: card_mesh(lod) for lod in (0, 1, 2)}

# ---------------------------------------------------------------- materials


def image(name, colorspace):
    img = bpy.data.images.load(os.path.join(WORK, name)); img.colorspace_settings.name = colorspace
    return img


def material(name, base, normal, roughness, alpha=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')
    tb = nt.nodes.new('ShaderNodeTexImage'); tb.image = image(base, 'sRGB')
    nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = image(normal, 'Non-Color')
    nm = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = roughness; bsdf.inputs['Metallic'].default_value = 0.0
    if alpha:
        nt.links.new(tb.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.use_backface_culling = False
        m.surface_render_method = 'DITHERED'
        clip = nt.nodes.new('ShaderNodeMath'); clip.operation = 'GREATER_THAN'; clip.inputs[1].default_value = 0.5
        nt.links.new(tb.outputs['Alpha'], clip.inputs[0]); nt.links.new(clip.outputs[0], bsdf.inputs['Alpha'])
    return m


bark_mat = material('Bark', 'bark_basecolor.png', 'bark_normal.png', 0.9)
leaf_mat = material('Leaves', 'leaves_basecolor.png', 'leaves_normal.png', 0.9, alpha=True)
bark_mat['openyamm_wind'] = 0.03
leaf_mat['openyamm_wind'] = 0.12

names = {0: 'Tree', 1: 'Tree_LOD1', 2: 'Tree_LOD2'}
for lod in (0, 1, 2):
    b, l = barks[lod], leaves[lod]
    b.data.materials.append(bark_mat); l.data.materials.append(leaf_mat)
    for x in bpy.data.objects:
        x.select_set(x in (b, l))
    bpy.context.view_layer.objects.active = b
    bpy.ops.object.join()
    b.name = names[lod]; b.data.name = names[lod]
    print('LOD', lod, names[lod], 'tris', len(b.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, 'tree.blend'))
