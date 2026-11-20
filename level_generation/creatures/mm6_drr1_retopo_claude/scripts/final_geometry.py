"""Final Wyrm geometry (production, after the user's review of the a14 pilot, 2026-10-13).

One object 'Wyrm' on 'Wyrm_Rig' replaces the source mesh in work/final_geometry.blend:
- body: the a14 adaptive isotropic remesh (work/body_a14.npz), small holes closed (the chest opening the source
  already had), shrinkwrapped onto the source, material per face from the nearest source face, weights by Data
  Transfer (nearest face interpolated, max 8);
- kept source pieces: tongue, both eyes, both cheek spikes (original geometry and weights);
- new teeth: the source tooth rows were broken triangles; generated cones follow a curve fitted to each original row
  (upper rows rigid on Head, the lower row rigid on Jaw), with fangs and a taper toward the back.
Writes face attribute 'part' (0 body, 1 tongue, 2 eye, 3 cheek, 4 tooth) for the texture compose."""
import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = os.environ.get('REA_TAG', 'a14')
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'source_snapshot.blend'))
scene = bpy.context.scene
src = bpy.data.objects['Wyrm']
rig = bpy.data.objects['Wyrm_Rig']
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
assert src.matrix_world.is_identity if hasattr(src.matrix_world, 'is_identity') else True


def select_only(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


# ---- source components (largest = body); pieces by role from their bone and position (inspect_pieces.py)
sbm = bmesh.new(); sbm.from_mesh(src.data); sbm.verts.ensure_lookup_table(); sbm.faces.ensure_lookup_table()
seen = set(); comps = []
for v in sbm.verts:
    if v.index in seen:
        continue
    stack = [v]; comp = []; seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if w.index not in seen:
                seen.add(w.index); stack.append(w)
    comps.append(comp)
comps.sort(key=len, reverse=True)
ROLES = {1: 'lower_teeth', 2: 'tongue', 3: 'upper_teeth', 4: 'upper_teeth', 5: 'eye', 6: 'eye', 7: 'upper_teeth',
         8: 'cheek', 9: 'cheek'}
assert len(comps) == 10, len(comps)
body_faces = {f.index for f in sbm.faces if f.verts[0].index in set(comps[0])}
src_tree = BVHTree.FromBMesh(sbm)
src_mat = [f.material_index for f in sbm.faces]
groups = {g.index: g.name for g in src.vertex_groups}


def part_object(indices, name):
    """Copy of the source restricted to the given vertex set (keeps UVs, materials, weights)."""
    obj = src.copy(); obj.data = src.data.copy(); obj.name = name
    scene.collection.objects.link(obj); obj.modifiers.clear(); obj.parent = None
    keep = set(indices)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.index not in keep], context='VERTS')
    bm.to_mesh(obj.data); bm.free()
    return obj


# ---- body: the adaptive remesh
data = np.load(os.path.join(HERE, 'work', f'body_{TAG}.npz'))
me = bpy.data.meshes.new('Body')
me.from_pydata([tuple(v) for v in data['verts'].tolist()], [], [tuple(dict.fromkeys(f)) for f in data['faces'].tolist()])
me.update()
body = bpy.data.objects.new('Body', me); scene.collection.objects.link(body)
select_only(body)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.remove_doubles(threshold=1e-6)
bpy.ops.mesh.normals_make_consistent(inside=False)
bpy.ops.object.mode_set(mode='OBJECT')
# Close small holes (the chest opening of the source); report every hole so real openings stay open.
bm = bmesh.new(); bm.from_mesh(body.data)
loops = []
edges = {e for e in bm.edges if e.is_boundary}
while edges:
    e = edges.pop(); loop = [e]; frontier = [e]
    while frontier:
        x = frontier.pop()
        for v in x.verts:
            for y in v.link_edges:
                if y in edges:
                    edges.remove(y); loop.append(y); frontier.append(y)
    loops.append(loop)
filled = []
for loop in loops:
    centre = sum((v.co for e in loop for v in e.verts), Vector()) / (2 * len(loop))
    if len(loop) <= 12:
        bmesh.ops.holes_fill(bm, edges=loop, sides=len(loop))
        filled.append((len(loop), [round(c, 3) for c in centre]))
    else:
        print('HOLE kept', len(loop), 'edges at', [round(c, 3) for c in centre])
bmesh.ops.triangulate(bm, faces=bm.faces[:])
# The source folds around its chest opening (shoulder/chest junction): relax a 2.5 cm patch around it.
for n, centre in filled:
    if n == 5 and centre[1] < -0.33 and centre[2] < 0.2:
        c = Vector(centre)
        patch = [v for v in bm.verts if (v.co - c).length < 0.025]
        for _ in range(12):
            bmesh.ops.smooth_vert(bm, verts=patch, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
        print('CHEST relaxed', len(patch), 'vertices at', centre)
bm.to_mesh(body.data); bm.free()
print('HOLES filled', filled)
sw = body.modifiers.new('Fit', 'SHRINKWRAP'); sw.target = src; sw.wrap_method = 'TARGET_PROJECT'
select_only(body); bpy.ops.object.modifier_apply(modifier=sw.name)

# ---- teeth: cones along a curve fitted to each original row
def row_bins(vids, upper, nbins):
    co = np.array([src.data.vertices[i].co[:] for i in vids])
    order = np.argsort(co[:, 1])
    co = co[order]
    bins = np.array_split(co, nbins)
    out = []
    for b in bins:
        if len(b) < 3:
            continue
        z = b[:, 2]
        if upper:
            root = b[z >= np.percentile(z, 70)].mean(0); tip_z = z.min()
        else:
            root = b[z <= np.percentile(z, 30)].mean(0); tip_z = z.max()
        out.append((Vector(root), abs(root[2] - tip_z)))
    return out


teeth = bmesh.new()
teeth_bone = []          # per vertex
def cone(root, direction, height, radius, bone):
    d = direction.normalized()
    a = d.orthogonal().normalized(); b = d.cross(a)
    ring0, ring1 = [], []
    for k in range(5):
        t = 2 * math.pi * k / 5
        off = a * math.cos(t) + b * math.sin(t)
        ring0.append(teeth.verts.new(root + off * radius - d * radius * 0.6))
        ring1.append(teeth.verts.new(root + d * height * 0.45 + off * radius * 0.55))
    tip = teeth.verts.new(root + d * height)
    for k in range(5):
        k2 = (k + 1) % 5
        teeth.faces.new((ring0[k], ring0[k2], ring1[k2], ring1[k]))
        teeth.faces.new((ring1[k], ring1[k2], tip))
    teeth_bone.extend([bone] * 11)


rows = []
for i, role in ROLES.items():
    if role == 'upper_teeth' and i != 7:
        rows.append((comps[i], True, 'Head'))
lower = comps[1]
lco = np.array([src.data.vertices[i].co[:] for i in lower])
cx = float(lco[:, 0].mean())
rows.append(([i for i in lower if src.data.vertices[i].co.x < cx], False, 'Jaw'))
rows.append(([i for i in lower if src.data.vertices[i].co.x >= cx], False, 'Jaw'))
count = 0
for vids, upper, bone in rows:
    bins = row_bins(vids, upper, 7)
    for k, (root, h) in enumerate(bins):
        front = k / max(len(bins) - 1, 1)          # 0 front .. 1 back
        height = float(np.clip(h, 0.003, 0.007)) * (1.45 if k == 1 else 1.0) * (1.0 - 0.35 * front)
        direction = Vector((0, 0, -1 if upper else 1))
        cone(root, direction, height, height * 0.32, bone)
        count += 1
# the small front piece: one front fang pair
fco = np.array([src.data.vertices[i].co[:] for i in comps[7]])
fr = Vector(fco.mean(0)); fr.z = float(fco[:, 2].max())
for dx in (-0.0025, 0.0025):
    cone(fr + Vector((dx, 0, 0)), Vector((0, -0.25, -1)), 0.006, 0.0018, 'Head'); count += 1
tme = bpy.data.meshes.new('Teeth'); teeth.to_mesh(tme); teeth.free()
tobj = bpy.data.objects.new('Teeth', tme); scene.collection.objects.link(tobj)
for name in ('Head', 'Jaw'):
    g = tobj.vertex_groups.new(name=name)
    g.add([i for i, b in enumerate(teeth_bone) if b == name], 1.0, 'REPLACE')
print('TEETH', count, 'cones,', len(tme.polygons), 'faces')

# ---- kept pieces
kept = {role: [] for role in ('tongue', 'eye', 'cheek')}
for i, role in ROLES.items():
    if role in kept:
        kept[role].append(part_object(comps[i], f'Keep_{role}_{i}'))

# ---- material per body face from the nearest source body face; weights by data transfer
for m in src.data.materials:
    body.data.materials.append(m)
for poly in body.data.polygons:
    loc, _, index, _ = src_tree.find_nearest(poly.center)
    poly.material_index = src_mat[index] if index is not None else 0
    poly.use_smooth = True
srcbody = part_object(comps[0], 'SourceBody')
for g in src.vertex_groups:
    body.vertex_groups.new(name=g.name)
dt = body.modifiers.new('Weights', 'DATA_TRANSFER'); dt.object = srcbody; dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
select_only(body); bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.ops.object.vertex_group_limit_total(limit=8)
bpy.ops.object.vertex_group_normalize_all(lock_active=False)
assert all(v.groups for v in body.data.vertices)
for m in src.data.materials:
    tobj.data.materials.append(m)
for p in tobj.data.polygons:
    p.material_index = 1; p.use_smooth = True

# ---- remodel spikes (user, 2026-10-13): back spines, tail spikes, head crest and horns are cut from the remesh and
# rebuilt as clean tapered tubes along their measured centreline (sharp tips, far fewer triangles). A spike is a
# connected cluster of body vertices standing more than SPIKE_MIN off a smooth reference surface (the Instant
# Meshes body, which rounds every spike off). Paw clusters (toes, claws) and clusters with several tips stay.
SPIKE_MIN = float(os.environ.get('REA_SPIKE_MIN', '0.003'))
# Tried on the Wyrm (2026-10-13): no triangle saving (the a14 spines are not dense) and rebuilt blades left stumps
# beside the new cones near the tail base, so the remodel is off by default (REA_SPIKES=1 enables it).
SPIKES_ON = os.environ.get('REA_SPIKES', '0') == '1'
# reference: morphological opening of the body (open_reference.py): spikes, horns and tail spikes removed
ref = np.load(os.path.join(HERE, 'work', f'body_{TAG}_open.npz'))
rme = bpy.data.meshes.new('Ref'); rme.from_pydata([tuple(v) for v in ref['verts'].tolist()], [],
                                                  [tuple(dict.fromkeys(f)) for f in ref['faces'].tolist()])
rbm = bmesh.new(); rbm.from_mesh(rme); ref_tree = BVHTree.FromBMesh(rbm)
bm = bmesh.new(); bm.from_mesh(body.data); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
deform = bm.verts.layers.deform.active
name_of = {g.index: g.name for g in body.vertex_groups}
height = {}
for v in bm.verts:
    loc, nrm, _, dist = ref_tree.find_nearest(v.co)
    outside = (v.co - loc).dot(nrm) > 0 if nrm is not None else True
    height[v.index] = dist if (dist is not None and outside) else 0.0
spike_v = {i for i, h in height.items() if h > SPIKE_MIN}
clusters = []
left = set(spike_v)
while left:
    s = left.pop(); comp = {s}; stack = [s]
    while stack:
        x = stack.pop()
        for e in bm.verts[x].link_edges:
            w = e.other_vert(bm.verts[x]).index
            if w in left:
                left.remove(w); comp.add(w); stack.append(w)
    clusters.append(comp)


def dominant_bone(vids):
    acc = {}
    for i in vids:
        for gi, wt in bm.verts[i][deform].items():
            acc[name_of[gi]] = acc.get(name_of[gi], 0) + wt
    return max(acc, key=acc.get) if acc else ''


if os.environ.get('REA_DEBUG'):
    for comp in sorted(clusters, key=len, reverse=True)[:40]:
        top = max(comp, key=lambda i: height[i])
        print('CLUSTER', len(comp), dominant_bone(comp), 'max h', round(height[top], 4),
              'at', [round(c, 3) for c in bm.verts[top].co])
spike_parts = []          # (vertex set incl. base ring, base ring, centreline pts, radii, weights, mat, kind)
ALLOWED = ('Spine', 'Neck', 'Tail', 'Head') if SPIKES_ON else ()


def nbrs(i):
    return [e.other_vert(bm.verts[i]).index for e in bm.verts[i].link_edges]


for comp in clusters:
    if len(comp) < 6:
        continue
    # split merged clusters by steepest ascent to their peaks (one region per tip)
    climb = {}
    for i in comp:
        x = i
        path = []
        while x not in climb:
            path.append(x)
            up = max([n for n in nbrs(x) if n in comp] + [x], key=lambda n: height[n])
            if up == x:
                climb[x] = x
                break
            x = up
        for p in path:
            climb[p] = climb[x]
    regions = {}
    for i in comp:
        regions.setdefault(climb[i], set()).add(i)
    # a minor bump near a taller tip belongs to that spike (one spine, one cone)
    for peak in sorted(regions, key=lambda k: height[k]):
        taller = [q for q in regions if q != peak and height[q] >= height[peak]
                  and ((bm.verts[q].co - bm.verts[peak].co).length < 0.012
                       or ((bm.verts[q].co - bm.verts[peak].co).length < 0.02 and height[peak] < 0.7 * height[q]))]
        if taller:
            regions[min(taller, key=lambda q: (bm.verts[q].co - bm.verts[peak].co).length)] |= regions.pop(peak)
    for peak, reg in regions.items():
        hp = height[peak]
        if hp < 0.008:
            continue
        bone = dominant_bone(reg)
        if not bone.startswith(ALLOWED):
            continue
        def reject(reason):
            if os.environ.get('REA_DEBUG'):
                print('REJECT', reason, bone, round(hp, 4), [round(c, 3) for c in bm.verts[peak].co])
        core = {i for i in reg if height[i] > 0.15 * hp}
        ring = {n for i in core for n in nbrs(i)} - core
        if len(core) < 5 or len(ring) < 4:
            reject('small'); continue
        base = sum((bm.verts[i].co for i in ring), Vector()) / len(ring)
        apex = bm.verts[peak].co.copy()
        axis = apex - base; L = axis.length
        if L < 0.008 or L > 0.08:
            reject(f'length {L:.3f}'); continue
        d = axis.normalized()
        rb = sum(((bm.verts[i].co - base) - d * (bm.verts[i].co - base).dot(d)).length for i in ring) / len(ring)
        if rb > 0.6 * L or rb > 0.018:             # stubby or wide: not a spike (blades are broad at the base)
            reject(f'stubby rb {rb:.4f} L {L:.3f}'); continue
        pts, radii = [base.copy()], [rb]
        ok = True
        for t in (0.33, 0.66):
            band = [bm.verts[i].co for i in core if abs((bm.verts[i].co - base).dot(d) / L - t) < 0.12]
            if len(band) < 3:
                pts.append(base + d * L * t); radii.append(rb * (1 - t))
                continue
            c = sum(band, Vector()) / len(band)
            r = sum(((q - c) - d * (q - c).dot(d)).length for q in band) / len(band)
            if r > radii[-1] * 1.15:               # widening toward the tip: not a cone
                ok = False
            pts.append(c); radii.append(min(r, radii[-1]))
        if not ok:
            reject('widening'); continue
        pts.append(apex); radii.append(0.0)
        weights = {}
        for i in ring:
            for gi, wt in bm.verts[i][deform].items():
                weights[gi] = weights.get(gi, 0) + wt / len(ring)
        _, _, fi, _ = src_tree.find_nearest(base)
        mat = src_mat[fi] if fi is not None else 0
        kind = 6 if (bone == 'Head' and L > 0.03) else 5      # 6 horn, 5 spike
        # blade cross-section: principal axes of the base ring perpendicular to the spike axis
        offs = [((bm.verts[i].co - base) - d * (bm.verts[i].co - base).dot(d)) for i in ring]
        M = np.array([[o.x, o.y, o.z] for o in offs]); C = M.T @ M / len(M)
        w_, V_ = np.linalg.eigh(C)
        e1 = Vector(V_[:, 2]); e1 = (e1 - d * e1.dot(d)).normalized()
        e2 = d.cross(e1)
        r1 = float(np.mean(np.abs(M @ np.array(e1[:])))) * 1.5
        r2 = float(np.mean(np.abs(M @ np.array(e2[:])))) * 1.5
        aspect = max(0.3, min(1.0, r2 / max(r1, 1e-6)))
        spike_parts.append((core | ring, ring, pts, radii, weights, mat, kind, (e1, e2, aspect)))
        if os.environ.get('REA_DEBUG'):
            print('SPIKE', bone, 'L', round(L, 4), 'rb', round(rb, 4), 'kind', kind, 'at', [round(c, 3) for c in apex])
# cut the spikes and close each base
cut_faces = set()
for region, ring, *_ in spike_parts:
    for i in region - ring:
        cut_faces.update(f.index for f in bm.verts[i].link_faces)
before_tris = len(bm.faces)
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in cut_faces], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
holes = [e for e in bm.edges if e.is_boundary]
filled = bmesh.ops.holes_fill(bm, edges=holes, sides=200)['faces']
bmesh.ops.triangulate(bm, faces=filled)
part_layer = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
# rebuild each spike as a tapered tube: base ring sunk below the skin, then the measured centreline to a sharp tip
SIDES = 6
for region, ring, pts, radii, weights, mat, kind, shape in spike_parts:
    d0 = (pts[1] - pts[0]).normalized()
    e1, e2, aspect = shape
    a = (e1 - d0 * e1.dot(d0)).normalized(); b = d0.cross(a)
    rings = []
    sunk = pts[0] - d0 * radii[0] * 0.5
    stations = [(sunk, radii[0] * 1.08)] + list(zip(pts[1:-1], radii[1:-1]))
    for p, r in stations:
        rv = []
        for k in range(SIDES):
            t = 2 * math.pi * k / SIDES
            v = bm.verts.new(p + (a * math.cos(t) + b * math.sin(t) * aspect) * r)
            for gi, wt in weights.items():
                v[deform][gi] = wt
            rv.append(v)
        rings.append(rv)
    tip = bm.verts.new(pts[-1])
    for gi, wt in weights.items():
        tip[deform][gi] = wt
    new_faces = []
    for r0, r1 in zip(rings, rings[1:]):
        for k in range(SIDES):
            k2 = (k + 1) % SIDES
            new_faces.append(bm.faces.new((r0[k], r0[k2], r1[k2], r1[k])))
    for k in range(SIDES):
        new_faces.append(bm.faces.new((rings[-1][k], rings[-1][(k + 1) % SIDES], tip)))
    for f in new_faces:
        f.material_index = mat; f.smooth = True; f[part_layer] = kind
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
bm.to_mesh(body.data); bm.free(); rbm.free()
print('SPIKES remodelled', len(spike_parts), 'horns', sum(1 for s in spike_parts if s[6] == 6),
      'body tris', before_tris, '->', len(body.data.polygons))

# ---- part attribute, join into 'Wyrm'
def tag(obj, value):
    attr = obj.data.attributes.get('part') or obj.data.attributes.new('part', 'INT', 'FACE')
    for item in attr.data:
        if item.value not in (5, 6):          # keep spike/horn tags written by the remodel
            item.value = value
tag(body, 0); tag(tobj, 4)
for o in kept['tongue']: tag(o, 1)
for o in kept['eye']: tag(o, 2)
for o in kept['cheek']: tag(o, 3)
bpy.data.objects.remove(srcbody, do_unlink=True)
select_only(body)
for o in [tobj] + kept['tongue'] + kept['eye'] + kept['cheek']:
    o.select_set(True)
bpy.ops.object.join()
old_name = src.name
bpy.data.objects.remove(src, do_unlink=True)
body.name = 'Wyrm'; body.data.name = 'Wyrm'
body.parent = rig
arm = body.modifiers.new('Armature', 'ARMATURE'); arm.object = rig
if not body.data.uv_layers:
    body.data.uv_layers.new(name='UVMap')
tris = sum(len(p.vertices) - 2 for p in body.data.polygons)
print('FINAL tris', tris, 'verts', len(body.data.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'final_geometry.blend'))
