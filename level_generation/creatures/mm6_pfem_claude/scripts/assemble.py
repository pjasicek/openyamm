"""Stage B: build the clean low-poly peasant from the fitted MPFB body plus own garment meshes.

Garment shapes are retopologised by radial ray casts onto the Meshy detail source (outside-in), so the
silhouette follows the reviewed references while topology, slit-free skirt, shoes and hair stay our own.
Output: work/assembly_v1.blend with objects Body, Eyes, Shoes, Skirt, Sleeves, Belt, HairCap, Braid,
Headband (all unrigged except Body/Eyes/Shoes which keep MPFB weights) and BodyRef (weight source).
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

common.enable_mpfb()
from bl_ext.blender_org.mpfb.services.humanservice import HumanService

MPFB_DATA = os.path.expanduser('~/.config/blender/5.2/extensions/.user/blender_org/mpfb/data')
DY = 0.019  # body-to-Meshy torso alignment measured by fit_body.py
Z_BELT = (1.005, 1.049)
Z_SKIRT_TOP, Z_HEM = 1.0, 0.19
ARM_BONES = {'Arm', 'ForeArm', 'Hand'}
FOOT_BONES = {'Foot', 'ToeBase', 'Leg'}

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'body_v3.blend'))
rig = bpy.data.objects['Human.rig']
rig.location.y = 0.0
human = bpy.data.objects['Human']
eyes = HumanService.add_mhclo_asset(os.path.join(MPFB_DATA, 'eyes/low-poly/low-poly.mhclo'), human,
                                    asset_type='Eyes', subdiv_levels=0, material_type='SIMPLE')
eyes.name = 'Eyes'
with bpy.data.libraries.load(os.path.join(common.WORK, 'meshy_fitted.blend')) as (src, dst):
    dst.objects = ['MeshyDetail', 'MeshyNoSkin']
for obj in dst.objects:
    bpy.context.scene.collection.objects.link(obj)
    obj.location.y -= DY
    obj.hide_render = True
bpy.context.view_layer.update()


def bvh_world(obj):
    dg = bpy.context.evaluated_depsgraph_get()
    me = obj.evaluated_get(dg).to_mesh()
    verts = [obj.matrix_world @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    tree = BVHTree.FromPolygons(verts, polys)
    obj.evaluated_get(dg).to_mesh_clear()
    return tree


meshy_bvh = bvh_world(dst.objects[0])
cloth_bvh = bvh_world(dst.objects[1])


def cast_in(tree, centre, direction, start):
    """Outside-in radial cast; returns radius from centre to the first surface, or None."""
    origin = centre + direction * start
    hit = tree.ray_cast(origin, -direction, start)
    return None if hit[0] is None else start - hit[3]


# ---------------------------------------------------------------- body cleanup
for mod in list(human.modifiers):
    if mod.type == 'MASK':
        human.modifiers.remove(mod)
groups = {g.index: g.name for g in human.vertex_groups}


def dominant_bone(v):
    best, weight = None, 0.0
    for g in v.groups:
        name = groups[g.group]
        if name.startswith('mixamorig:') and g.weight > weight:
            best, weight = name[10:], g.weight
    return best or ''


def strip_side(name):
    for p in ('Left', 'Right'):
        if name.startswith(p):
            return name[len(p):]
    return name


helper_ids = {i for i, n in groups.items() if n in ('HelperGeometry', 'JointCubes')}
bm = bmesh.new(); bm.from_mesh(human.data); bm.verts.ensure_lookup_table()
deform = bm.verts.layers.deform.active
bmesh.ops.delete(bm, geom=[v for v in bm.verts if any(k in helper_ids and w > 0 for k, w in v[deform].items())],
                 context='VERTS')
bm.to_mesh(human.data); bm.free()
human.data.update()
for name in [n for n in groups.values() if n.startswith('helper') or n.startswith('joint') or n in
             ('HelperGeometry', 'JointCubes')]:
    human.vertex_groups.remove(human.vertex_groups[name])
groups = {g.index: g.name for g in human.vertex_groups}

body_ref = human.copy(); body_ref.data = human.data.copy(); body_ref.name = 'BodyRef'
bpy.context.scene.collection.objects.link(body_ref)
body_ref.hide_render = True
body_bvh = bvh_world(body_ref)

co = np.array([tuple(v.co) for v in human.data.vertices])
dom = [dominant_bone(v) for v in human.data.vertices]
kind = [strip_side(d) for d in dom]
chest = co[(abs(co[:, 2] - 1.2) < 0.02) & (abs(co[:, 0]) < 0.08)]
yc_chest = (chest[:, 1].min() + chest[:, 1].max()) / 2

# Shoes: closed parametric low shoe per foot (heel to toe sections), weights transferred later.
def build_shoe(side_sign, name):
    sel = co[[co[i, 2] < 0.09 and kind[i] in FOOT_BONES and co[i, 0] * side_sign > 0 for i in range(len(co))]]
    heel_y, toe_y = sel[:, 1].max(), sel[:, 1].min()
    x_heel = sel[sel[:, 1] > heel_y - 0.04][:, 0].mean()
    x_toe = sel[sel[:, 1] < toe_y + 0.05][:, 0].mean()
    profile = [(0.0, 0.052), (0.3, 0.066), (0.5, 0.074), (0.7, 0.054), (0.85, 0.042), (1.0, 0.03)]
    def top(t):
        for (t0, h0), (t1, h1) in zip(profile, profile[1:]):
            if t <= t1:
                return h0 + (h1 - h0) * (t - t0) / (t1 - t0)
        return profile[-1][1]
    sections, seg, bottom = 11, 12, -0.012
    rings = []
    for k in range(sections):
        t = k / (sections - 1)
        y = heel_y + 0.007 - (heel_y - toe_y + 0.017) * t
        xc = x_heel + (x_toe - x_heel) * t
        band = sel[abs(sel[:, 1] - y) < 0.012]
        half_w = ((band[:, 0].max() - band[:, 0].min()) / 2 if len(band) > 3 else 0.03) + 0.006
        half_w *= max(0.25, (1 - abs(2 * t - 1) ** 5)) ** 0.5
        h = top(t); zc = (h + bottom) / 2; hh = (h - bottom) / 2
        ring = []
        for sgm in range(seg):
            th = 2 * math.pi * sgm / seg
            cx, sz = math.cos(th), math.sin(th)
            px = xc + half_w * math.copysign(abs(cx) ** 0.7, cx)
            pz = zc + hh * math.copysign(abs(sz) ** 0.8, sz)
            ring.append(Vector((px, y, max(pz, bottom))))
        rings.append(ring)
    obj = make_grid_mesh(name, rings)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=0)
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free()
    return obj


# Body deletions: hidden legs/hips under the skirt, feet inside the shoes.
delete = set()
for i, (x, y, z) in enumerate(co):
    if 0.40 < z < 0.985 and kind[i] not in ARM_BONES and not kind[i].startswith('Hand'):
        delete.add(i)
    if (z < 0.062 and kind[i] in FOOT_BONES) or kind[i] == 'ToeBase':
        delete.add(i)

# Bodice: inflate the torso surface below the square neckline.
def bodice_region(i):
    x, y, z = co[i]
    if not (0.975 < z < 1.345) or i in delete:
        return False
    if kind[i] in ARM_BONES or kind[i] in ('Head', 'Neck') or kind[i].startswith('Hand'):
        return False
    front = y < yc_chest
    if front and abs(x) < 0.095 and z > 1.20:
        return False
    if not front and abs(x) < 0.09 and z > 1.235:
        return False
    if abs(x) < 0.07 and z > 1.30:
        return False
    return True


mask = np.array([1.0 if bodice_region(i) else 0.0 for i in range(len(co))])
adjacency = [[] for _ in co]
for e in human.data.edges:
    a, b = e.vertices
    adjacency[a].append(b); adjacency[b].append(a)
soft = mask.copy()
for _ in range(2):
    soft = np.array([(soft[i] + sum(soft[j] for j in adjacency[i])) / (1 + len(adjacency[i])) for i in range(len(co))])
soft = np.maximum(soft, mask * 0.85)
bm = bmesh.new(); bm.from_mesh(human.data); bm.verts.ensure_lookup_table()
inner = [bm.verts[i] for i in range(len(co)) if mask[i] > 0 and soft[i] > 0.99]
for _ in range(6):  # remove bare-chest anatomy under the supportive bodice
    bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.normal_update()
offset = np.zeros(len(co))
for i in range(len(co)):
    if soft[i] <= 0:
        continue
    v = bm.verts[i]
    hit = cloth_bvh.ray_cast(v.co + v.normal * 0.05, -v.normal, 0.07)
    offset[i] = min(max(0.05 - hit[3], 0.003), 0.018) if hit[0] is not None else 0.004
for _ in range(4):
    offset = np.array([(offset[i] * 2 + sum(offset[j] for j in adjacency[i])) / (2 + len(adjacency[i]))
                       if soft[i] > 0 else 0.0 for i in range(len(co))])
for i in range(len(co)):
    if soft[i] > 0:
        bm.verts[i].co += bm.verts[i].normal * max(offset[i], 0.003) * soft[i]
bm.to_mesh(human.data); bm.free()
bodice_group = human.vertex_groups.new(name='region_bodice')
for i, m in enumerate(mask):
    if m > 0:
        bodice_group.add([i], 1.0, 'REPLACE')
bm = bmesh.new(); bm.from_mesh(human.data); bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in sorted(delete)], context='VERTS')
bm.to_mesh(human.data); bm.free()
human.name = 'Body'


# ---------------------------------------------------------------- helpers for lathe-like meshes
def make_grid_mesh(name, rings, closed=True, caps=()):
    """rings: list of lists of Vector (same length). Builds quads between consecutive rings."""
    me = bpy.data.meshes.new(name)
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = []
    for r in range(len(rings) - 1):
        for s in range(n if closed else n - 1):
            a = r * n + s; b = r * n + (s + 1) % n
            faces.append((a, b, b + n, a + n))
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def ring_filter(values, window=2, low=0.02, high=0.03):
    n = len(values)
    out = list(values)
    for i in range(n):
        neighbourhood = sorted(values[(i + k) % n] for k in range(-window, window + 1))
        med = neighbourhood[len(neighbourhood) // 2]
        if values[i] < med - low or values[i] > med + high:
            out[i] = med
    return out


def azimuth_dir(phi):
    # phi = 0 faces the character front (-Y); increases toward the character's left (+X).
    return Vector((math.sin(phi), -math.cos(phi), 0.0))


shoes = [build_shoe(1, 'ShoeLeft'), build_shoe(-1, 'ShoeRight')]

# ---------------------------------------------------------------- belt
belt_seg = 32
waist = co[(abs(co[:, 2] - 1.027) < 0.01) & (abs(co[:, 0]) < 0.2)]
yc_waist = (waist[:, 1].min() + waist[:, 1].max()) / 2
centre_w = Vector((0.0, yc_waist, 1.027))
belt_r = []
for s in range(belt_seg):
    d = azimuth_dir(2 * math.pi * s / belt_seg)
    r_body = cast_in(body_bvh, centre_w, d, 0.3) or 0.1
    r_m = cast_in(meshy_bvh, centre_w, d, r_body + 0.035) or r_body + 0.01
    belt_r.append(max(r_m, r_body + 0.009))
belt_r = ring_filter(belt_r, 2, 0.006, 0.006)
rings = []
for (z, dr) in ((Z_BELT[0], -0.004), (Z_BELT[0], 0.0), (Z_BELT[1], 0.0), (Z_BELT[1], -0.004)):
    rings.append([Vector((0, yc_waist, z)) + azimuth_dir(2 * math.pi * s / belt_seg) * (belt_r[s] + dr)
                  for s in range(belt_seg)])
belt = make_grid_mesh('Belt', rings)
# Rectangular buckle frame, slightly proud of the front.
front_r = belt_r[0]
bm = bmesh.new()
bmesh.ops.create_cube(bm, size=1.0)
for v in bm.verts:
    v.co = Vector((v.co.x * 0.036, v.co.y * 0.006, v.co.z * 0.032)) + Vector((0, yc_waist - front_r - 0.002, 1.027))
buckle_me = bpy.data.meshes.new('Buckle'); bm.to_mesh(buckle_me); bm.free()
buckle = bpy.data.objects.new('Buckle', buckle_me); bpy.context.scene.collection.objects.link(buckle)

# ---------------------------------------------------------------- skirt
skirt_seg, skirt_rings = 48, 20
zs = [Z_SKIRT_TOP - (Z_SKIRT_TOP - Z_HEM) * (k / (skirt_rings - 1)) ** 1.08 for k in range(skirt_rings)]
radii, centres = [], []
for k, z in enumerate(zs):
    c = Vector((0.0, yc_waist, z))
    front = cast_in(cloth_bvh, c, azimuth_dir(0), 0.6); back = cast_in(cloth_bvh, c, azimuth_dir(math.pi), 0.6)
    if front and back and k > 1:
        c.y += (back - front) / 2 * 0.5
    centres.append(c)
    row = []
    for s in range(skirt_seg):
        d = azimuth_dir(2 * math.pi * s / skirt_seg)
        r_leg = cast_in(body_bvh, c, d, 0.2) or 0.0  # hips/legs only; arms lie outside 0.2
        r = cast_in(cloth_bvh, c, d, 0.6)
        if k == 0:
            r = belt_r[int(s * belt_seg / skirt_seg)] - 0.006
        row.append(max(r if r else 0.0, r_leg + 0.012))
    radii.append(ring_filter(row, 2, 0.02, 0.03) if k > 0 else row)
radii = np.array(radii)
for k in range(1, skirt_rings):  # hands/slit/holes: continue from the ring above
    cap = 0.16 + (1.0 - zs[k]) * 0.30
    bad = (radii[k] < 0.05) | (radii[k] > radii[k - 1] + (0.05 if k == 1 else 0.03)) | (radii[k] > cap)
    radii[k][bad] = radii[k - 1][bad] * 1.025
for _ in range(3):  # keep vertical folds, remove ring-to-ring lumps
    smoothed = radii.copy()
    for k in range(1, skirt_rings - 1):
        smoothed[k] = 0.25 * radii[k - 1] + 0.5 * radii[k] + 0.25 * radii[k + 1]
    smoothed[-1] = np.maximum(radii[-1], smoothed[-2])
    radii = smoothed
for k in range(1, skirt_rings):  # a skirt never narrows below the waist
    radii[k] = np.maximum(radii[k], radii[k - 1] * 0.995 if k < 4 else radii[k] * 0)
rings = [[centres[k] + azimuth_dir(2 * math.pi * s / skirt_seg) * radii[k][s] for s in range(skirt_seg)]
         for k in range(skirt_rings)]
skirt = make_grid_mesh('Skirt', rings)
skirt['radii'] = radii.tolist(); skirt['zs'] = zs; skirt['yc'] = [c.y for c in centres]

# ---------------------------------------------------------------- sleeves
pose_bones = {b.name: b for b in rig.data.bones}
sleeve_objects = []
torso_centre = Vector((0.0, yc_chest, 1.2))
for side in ('Left', 'Right'):
    J = rig.matrix_world @ pose_bones[f'mixamorig:{side}Arm'].head_local
    E = rig.matrix_world @ pose_bones[f'mixamorig:{side}ForeArm'].head_local
    axis = (E - J).normalized(); L = (E - J).length
    u = axis.cross(Vector((0, 1, 0))).normalized(); v = axis.cross(u).normalized()
    seg = 16
    ts = [-0.10, -0.04, 0.03, 0.10, 0.17, 0.24, 0.31, 0.37, 0.42, 0.455, 0.47]
    rings = []
    for t in ts:
        origin = J + axis * (t * L)
        ring = []
        for s in range(seg):
            th = 2 * math.pi * s / seg
            d = (u * math.cos(th) + v * math.sin(th)).normalized()
            r_body = cast_in(body_bvh, origin, d, 0.12) or 0.04
            medial = d.dot((torso_centre - origin).normalized()) > 0.35
            if t in (ts[0], ts[-1]):
                r = r_body + (0.004 if t == ts[0] else 0.003)
            elif t == ts[-2]:
                r = r_body + 0.007
            elif medial and t < 0.2:
                r = r_body + 0.008
            else:
                r_m = cast_in(cloth_bvh, origin, d, 0.15)
                r = min(max(r_m or r_body + 0.02, r_body + 0.008), r_body + 0.06)
            ring.append(r)
        if t not in (ts[0], ts[-1], ts[-2]):
            ring = ring_filter(ring, 2, 0.012, 0.015)
        rings.append([origin + (u * math.cos(2 * math.pi * s / seg) + v * math.sin(2 * math.pi * s / seg)) * ring[s]
                      for s in range(seg)])
    sleeve_objects.append(make_grid_mesh(f'Sleeve{side}', rings))

# ---------------------------------------------------------------- hair cap, braid, headband
ear_index = body_ref.vertex_groups['ears'].index
ears = np.array([tuple(v.co) for v in body_ref.data.vertices if any(g.group == ear_index for g in v.groups)])
head_centre = Vector((0.0, float(ears[:, 1].mean()), float(ears[:, 2].mean()) + 0.012))
ear_verts = {v.index for v in body_ref.data.vertices if any(g.group == ear_index and g.weight > 0.3 for g in v.groups)}
ear_faces = {p.index for p in body_ref.data.polygons if any(i in ear_verts for i in p.vertices)}


def scalp_cast(d):
    """Radius to the scalp along d; None where the ray lands on an ear (filled from neighbours later)."""
    hit = body_bvh.ray_cast(head_centre + d * 0.25, -d, 0.25)
    if hit[0] is None:
        return None, None
    return (None if hit[2] in ear_faces else 0.25 - hit[3]), hit[0]
HAIRLINE = [(0.0, 1.497), (55.0, 1.474), (90.0, 1.455), (125.0, 1.418), (180.0, 1.392)]


def hairline_z(phi):
    a = math.degrees(abs(((phi + math.pi) % (2 * math.pi)) - math.pi))
    for (a0, z0), (a1, z1) in zip(HAIRLINE, HAIRLINE[1:]):
        if a <= a1:
            t = (a - a0) / (a1 - a0); t = t * t * (3 - 2 * t)
            return z0 + (z1 - z0) * t
    return HAIRLINE[-1][1]


def head_dir(phi, el):
    return (azimuth_dir(phi) * math.cos(el) + Vector((0, 0, math.sin(el)))).normalized()


n_az, n_el = 28, 9
grid = []
for i in range(n_az):
    phi = 2 * math.pi * i / n_az
    target = hairline_z(phi)
    lo_el, hi_el = math.radians(-70), math.radians(70)
    for _ in range(30):  # elevation whose scalp (or ear) surface point sits on the hairline
        mid = (lo_el + hi_el) / 2
        _, point = scalp_cast(head_dir(phi, mid))
        if point is not None and point.z < target:
            lo_el = mid
        else:
            hi_el = mid
    els = [lo_el + (math.radians(84) - lo_el) * (j / (n_el - 1)) ** 0.9 for j in range(n_el)]
    column = []
    for j, el in enumerate(els):
        d = head_dir(phi, el)
        r_scalp, _ = scalp_cast(d)
        r_hair = cast_in(meshy_bvh, head_centre, d, 0.3)
        column.append([r_scalp, r_hair, d])
    grid.append(column)
for j in range(n_el):  # ear hits: take neighbouring azimuths on the same ring
    for _ in range(n_az):
        missing = [i for i in range(n_az) if grid[i][j][0] is None]
        if not missing:
            break
        for i in missing:
            nb = [grid[(i + k) % n_az][j][0] for k in (-1, 1) if grid[(i + k) % n_az][j][0] is not None]
            if nb:
                grid[i][j][0] = sum(nb) / len(nb)
offs = np.zeros((n_az, n_el))
for i in range(n_az):
    for j in range(n_el):
        r_scalp, r_hair, _ = grid[i][j]
        off = min(max((r_hair - r_scalp) if r_hair else 0.012, 0.006), 0.022)
        if j <= 3:  # near the hairline Meshy ears/sideburns would flare the cap
            off = min(off, 0.006 + 0.003 * j)
        offs[i, j] = 0.0025 if j == 0 else off
for _ in range(3):
    sm = offs.copy()
    for i in range(n_az):
        for j in range(2, n_el):
            nb = [offs[(i - 1) % n_az, j], offs[(i + 1) % n_az, j], offs[i, j - 1], offs[i, min(j + 1, n_el - 1)]]
            sm[i, j] = (offs[i, j] * 2 + sum(nb)) / 6
    offs = sm
verts, faces = [], []
for i in range(n_az):
    for j in range(n_el):
        r_scalp, _, d = grid[i][j]
        verts.append(tuple(head_centre + d * (r_scalp + offs[i, j])))
top_dir = Vector((0, 0.15, 1)).normalized()
pole_r = (scalp_cast(top_dir)[0] or 0.1) + float(offs[:, -1].mean())
verts.append(tuple(head_centre + top_dir * pole_r))
for i in range(n_az):
    i2 = (i + 1) % n_az
    for j in range(n_el - 1):
        faces.append((i * n_el + j, i2 * n_el + j, i2 * n_el + j + 1, i * n_el + j + 1))
    faces.append((i * n_el + n_el - 1, i2 * n_el + n_el - 1, len(verts) - 1))
hair_me = bpy.data.meshes.new('HairCap'); hair_me.from_pydata(verts, [], faces); hair_me.update()
hair = bpy.data.objects.new('HairCap', hair_me); bpy.context.scene.collection.objects.link(hair)
hair_bvh = bvh_world(hair)

# Braid: follows the nape/upper back surface from below the occiput.
def back_y(z, trees):
    best = None
    for tree in trees:
        hit = tree.ray_cast(Vector((0.0, 0.4, z)), Vector((0, -1, 0)), 0.8)
        if hit[0] is not None:
            best = hit[0].y if best is None else max(best, hit[0].y)
    return best


P0 = Vector((0.0, back_y(1.405, (hair_bvh,)) - 0.014, 1.405))
P1 = Vector((0.0, back_y(1.33, (hair_bvh, body_bvh)) + 0.024, 1.33))
P2 = Vector((0.0, back_y(1.215, (body_bvh,)) + 0.016, 1.215))
braid_path = [P0 * (1 - t) ** 2 + P1 * 2 * t * (1 - t) + P2 * t * t for t in np.linspace(0, 1, 15)]
seg = 8
rings = []
for k, p in enumerate(braid_path):
    t = k / (len(braid_path) - 1)
    radius = 0.019 * (1 - t) + 0.011 * t
    if k >= len(braid_path) - 3:  # tie then small tuft
        radius = (0.0075, 0.0125, 0.006)[k - (len(braid_path) - 3)]
    lobe = 1.0 if k % 2 == 0 else 0.86
    centre = p
    nxt = braid_path[min(k + 1, len(braid_path) - 1)] - braid_path[max(k - 1, 0)]
    tangent = nxt.normalized()
    a = tangent.cross(Vector((1, 0, 0))).normalized(); b = tangent.cross(a).normalized()
    rings.append([centre + (b * math.cos(2 * math.pi * s / seg) * 1.1 + a * math.sin(2 * math.pi * s / seg))
                  * radius * lobe for s in range(seg)])
braid = make_grid_mesh('Braid', rings)
braid['path'] = [tuple(p) for p in braid_path]

band_seg = 28
band_rows = []
band_r = []
for s in range(band_seg):
    phi = 2 * math.pi * s / band_seg
    d = azimuth_dir(phi)
    z = 1.493 + 0.012 * (1 - math.cos(phi)) / 2
    c = Vector((0.0, head_centre.y, z))
    band_r.append(max(cast_in(hair_bvh, c, d, 0.2) or 0.0, cast_in(body_bvh, c, d, 0.2) or 0.0) + 0.0025)
band_r = ring_filter(band_r, 2, 0.006, 0.006)
for dz, dr in ((-0.004, -0.0015), (-0.004, 0.0), (0.004, 0.0), (0.004, -0.0015)):
    band_rows.append([Vector((0.0, head_centre.y, 1.493 + 0.012 * (1 - math.cos(2 * math.pi * s / band_seg)) / 2 + dz))
                      + azimuth_dir(2 * math.pi * s / band_seg) * (band_r[s] + dr) for s in range(band_seg)])
headband = make_grid_mesh('Headband', band_rows)

for obj in [belt, buckle, skirt, braid, headband, hair] + sleeve_objects:
    obj.data.update()
meta = {'yc_chest': yc_chest, 'yc_waist': yc_waist, 'head_centre': list(head_centre), 'belt_r_front': front_r}
bpy.context.scene['pfem_meta'] = json.dumps(meta)
counts = {}
for obj in bpy.context.scene.objects:
    if obj.type == 'MESH' and not obj.name.startswith('Meshy') and obj.name != 'BodyRef':
        counts[obj.name] = sum(len(p.vertices) - 2 for p in obj.data.polygons)
print('TRIS', json.dumps(counts), 'total', sum(counts.values()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'assembly_v1.blend'))
