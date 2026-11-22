"""Clean the Smart Topology v2 armadillo (work/clean_v1.blend, pieces ranked by vertex count as prep.py lists them):
- keep piece 0 (the body: head, banded shell, four clawed legs, the tail and its ball) and the face pieces 1-8 (eye
  and nostril caps on the snout); drop the 3-5 vertex slivers 9-15 under the rump;
- fill the body's holes (boundary loops of piece 0);
- widen the shell: Xeen draws the beast broader than tall (front sprite about 1.6 wide per height, Meshy's body 1.2):
  x is scaled by WIDEN on the shell and head ring (weight 0 on the head in front of y -0.98, 1 behind -0.86, back to 0
  over the rump y 0.0..0.2), and the feet (below z 0.10) are moved out by the same amount at their own centre instead
  of being stretched (blend over z 0.10..0.18), so the claws keep their shape;
- decimate the body ahead of the tail (y < 0.12) to DECIMATE (the tail keeps its density for the bends);
- add the procedural parts: the tail-ball SPIKES (part 2: 16 cones on a Fibonacci sphere about the ball centre,
  rigged to the Spikes bone that scales them out of the ball) and the forked TONGUE (part 3: a tapered three-sided
  strip forking into two prongs, lying in the mouth along -Y, rigged to the Tongue bone).
Face attribute `part`: 0 body, 1 face caps, 2 spikes, 3 tongue. Writes work/clean_v2.blend and work/parts.json
(ball centre and radius, tongue root)."""
import bpy, bmesh, os, math, json
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDEN = 1.25
DECIMATE = 0.55
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
ob = bpy.data.objects['Dillo']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
label = [-1] * len(bm.verts); pieces = []
for v in bm.verts:
    if label[v.index] >= 0: continue
    st = [v]; label[v.index] = len(pieces); idx = []
    while st:
        x = st.pop(); idx.append(x.index)
        for e in x.link_edges:
            w = e.other_vert(x)
            if label[w.index] < 0: label[w.index] = label[v.index]; st.append(w)
    pieces.append(idx)
order = sorted(range(len(pieces)), key=lambda i: -len(pieces[i]))
rank = {p: r for r, p in enumerate(order)}
PART = {0: 0, **{k: 1 for k in range(1, 9)}}
vrank = [rank[label[v.index]] for v in bm.verts]
bmesh.ops.delete(bm, geom=[v for v in bm.verts if vrank[v.index] not in PART], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
keep_rank = [r for r in vrank if r in PART]
part_layer = bm.faces.layers.int.new('part')
rank_layer = bm.verts.layers.int.new('rank')
for v, r in zip(bm.verts, keep_rank):
    v[rank_layer] = r
for f in bm.faces:
    f[part_layer] = PART[f.verts[0][rank_layer]]
for r in range(9):
    n = sum(1 for e in bm.edges if e.is_boundary and e.verts[0][rank_layer] == r)
    if n: print('BOUNDARY piece', r, 'edges', n)
bnd = [e for e in bm.edges if e.is_boundary and all(v[rank_layer] == 0 for v in e.verts)]
res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
bmesh.ops.triangulate(bm, faces=res['faces'])
for f in res.get('faces', []):
    f[part_layer] = 0
rest = [e for e in bm.edges if e.is_boundary and all(v[rank_layer] == 0 for v in e.verts)]
if rest:
    tf = bmesh.ops.triangle_fill(bm, edges=rest, use_beauty=True)
    for f in tf.get('geom', []):
        if isinstance(f, bmesh.types.BMFace):
            f[part_layer] = 0
left = sum(1 for e in bm.edges if e.is_boundary and e.verts[0][rank_layer] == 0)
print('FILLED body boundary edges', len(bnd), 'new faces', len(res['faces']), 'left', left)

# ---- widen the shell, move the feet out


def ss(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def wy(y):
    return ss((y + 0.98) / 0.12) * (1 - ss(y / 0.2))


for v in bm.verts:
    x, y, z = v.co
    w = wy(y)
    if w <= 0:
        continue
    k = 1 + (WIDEN - 1) * w
    scaled = x * k
    foot_c = math.copysign(0.22, x)                       # the feet's own centre line (|x| 0.15..0.30)
    moved = x + foot_c * (k - 1)
    f = ss((z - 0.10) / 0.08)
    v.co.x = moved * (1 - f) + scaled * f
bm.to_mesh(ob.data); bm.free()
me = ob.data
if 'rank' in me.attributes:
    me.attributes.remove(me.attributes['rank'])
co = np.array([v.co[:] for v in me.vertices])
print('WIDENED size', [round(float(co[:, i].max() - co[:, i].min()), 3) for i in range(3)])

# ---- decimate the body ahead of the tail
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
t0 = len(me.polygons)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
part = [me.attributes['part'].data[p.index].value for p in me.polygons]
for p in me.polygons:
    p.select = part[p.index] == 0 and all(me.vertices[i].co.y < 0.12 for i in p.vertices)
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.decimate(ratio=DECIMATE)
bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.quads_convert_to_tris(quad_method='BEAUTY', ngon_method='BEAUTY')
bpy.ops.object.mode_set(mode='OBJECT')
me = ob.data
print('DECIMATED', t0, '->', len(me.polygons))

# ---- ball centre from the tail tip vertices (y > 0.95)
co = np.array([v.co[:] for v in me.vertices])
ball = co[co[:, 1] > 0.965]
bc = Vector(((ball[:, 0].max() + ball[:, 0].min()) / 2, (ball[:, 1].max() + ball[:, 1].min()) / 2,
             (ball[:, 2].max() + ball[:, 2].min()) / 2))
br = float(max(ball[:, 2].max() - ball[:, 2].min(), ball[:, 0].max() - ball[:, 0].min()) / 2)
print('BALL centre', [round(c, 3) for c in bc], 'radius', round(br, 3))

# ---- spikes: 16 cones on a Fibonacci sphere, base inside the ball, tip at 2.3 ball radii
sb = bmesh.new()
N = 16; SEG = 6
axis_back = Vector((0, 1, 0))
for i in range(N):
    zf = 1 - 2 * (i + 0.5) / N
    r = math.sqrt(1 - zf * zf); th = math.pi * (3 - math.sqrt(5)) * i
    d = Vector((r * math.cos(th), zf, r * math.sin(th))).normalized()
    if d.dot(-axis_back) > 0.85:          # none straight into the tail
        continue
    m = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    length = 1.45 * br; base_r = 0.30 * br
    res = bmesh.ops.create_cone(sb, cap_ends=True, cap_tris=True, segments=SEG, radius1=base_r, radius2=0.0,
                                depth=length, matrix=Matrix.Translation(bc + d * (0.85 * br + length / 2)) @ m)
bmesh.ops.triangulate(sb, faces=sb.faces)
bmesh.ops.recalc_face_normals(sb, faces=sb.faces)
sme = bpy.data.meshes.new('Spikes'); sb.to_mesh(sme)
spikes = bpy.data.objects.new('Spikes', sme); bpy.context.scene.collection.objects.link(spikes)
pa = sme.attributes.new('part', 'INT', 'FACE')
for i in range(len(sme.polygons)): pa.data[i].value = 2

# ---- tongue: root in the mouth below the snout tip, along -Y and a little down; forks over its last 40 %
tip_y = float(co[:, 1].min())
root = Vector((0.0, -1.04, 0.182))        # inside the snout above its underside (z 0.169 at y -1.04)
L = 0.11
tb = bmesh.new()


def section(c, w, h):
    return [tb.verts.new(c + Vector((-w, 0, 0))), tb.verts.new(c + Vector((w, 0, 0))), tb.verts.new(c + Vector((0, 0, h)))]


def strip(path, w0, w1, h0, h1):
    rings = []
    for k, c in enumerate(path):
        t = k / (len(path) - 1)
        rings.append(section(c, w0 * (1 - t) + w1 * t, h0 * (1 - t) + h1 * t))
    for a, b in zip(rings, rings[1:]):
        for j in range(3):
            tb.faces.new((a[j], a[(j + 1) % 3], b[(j + 1) % 3], b[j]))
    return rings


down = Vector((0, -0.55, -0.83)).normalized()   # out of the mouth and down, as the sprite's
stem = [root + down * (L * 0.6 * k / 4) for k in range(5)]
r0 = strip(stem, 0.011, 0.009, 0.007, 0.006)
tb.faces.new(list(reversed(r0[0])))
fork0 = stem[-1]
for s in (-1, 1):
    pr = [fork0 + down * (L * 0.4 * k / 3) + Vector((s * 0.016 * (k / 3) ** 1.2, 0, 0)) for k in range(4)]
    rr = strip(pr, 0.0055, 0.0015, 0.0045, 0.0012)
    tb.faces.new(rr[-1])
bmesh.ops.remove_doubles(tb, verts=tb.verts, dist=1e-6)
bmesh.ops.triangulate(tb, faces=tb.faces)
bmesh.ops.recalc_face_normals(tb, faces=tb.faces)
tme = bpy.data.meshes.new('Tongue'); tb.to_mesh(tme)
tongue = bpy.data.objects.new('Tongue', tme); bpy.context.scene.collection.objects.link(tongue)
pa = tme.attributes.new('part', 'INT', 'FACE')
for i in range(len(tme.polygons)): pa.data[i].value = 3

for o in bpy.data.objects: o.select_set(o in (ob, spikes, tongue))
bpy.context.view_layer.objects.active = ob
bpy.ops.object.join()
me = ob.data
for p in me.polygons:
    p.use_smooth = me.attributes['part'].data[p.index].value != 2
counts = {}
for p in me.polygons:
    v = me.attributes['part'].data[p.index].value; counts[v] = counts.get(v, 0) + 1
print('CLEAN tris', len(me.polygons), 'by part', dict(sorted(counts.items())))
json.dump({'ball_centre': list(bc), 'ball_radius': br, 'tongue_root': list(root), 'tongue_dir': list(down),
           'tongue_length': L, 'snout_tip_y': tip_y, 'widen': WIDEN}, open(os.path.join(HERE, 'work', 'parts.json'), 'w'),
          indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
