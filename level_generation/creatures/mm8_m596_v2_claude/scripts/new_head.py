"""Round 3 head (user: "please completely re-do, this is ugly"): remove the Meshy head and crown, cap the neck, and
author a gem-cut wedge head in its place, after the native frames (flattened angular wedge pointing forward, a crown
of shards fanning backward and out like a star from the front, bright eye facets):
- skull and muzzle: the convex hull of a few deliberate points (large flat facets, sharp brow and jaw ridges);
- eye sockets: an angular pocket cut under each brow (exact boolean with a faceted cutter), a smaller faceted gem
  set inside each pocket, recessed below the surface;
- crown: eight diamond-section shards (base, shoulder, tip) sweeping back and radiating.
Coordinates are local to the head joint (0, -0.17, 1.60): x across (+ = the creature's left), f forward, z up.
Faces get the int attribute 'part' (0 body, 1 eye gem, 2 socket, 3 head and crown) and the head vertices the group
'HeadRigid' (rig.py weights them wholly to Head). Usage: blender -b -P new_head.py -- <in.blend> <out.blend>"""
import math, os, sys, bpy, bmesh
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(P, a[0]))
body = bpy.data.objects['CrystalWalker']; me = body.data
H = Vector((0, -.17, 1.60))
def W(x, f, z):
    return Vector((H.x + x, H.y - f, H.z + z))

# hull points (step 2), needed by the cut
PTS = [(0, .31, -.035), (0, .21, .03), (0, .26, -.075), (0, .125, .088), (0, .02, .128), (0, -.09, .095),
       (0, -.15, -.07), (0, .21, -.135)]   # last: the throat, so the jaw's underside runs down into the neck
for s in (1, -1):
    PTS += [(s * .036, .25, -.004), (s * .056, .17, -.085), (s * .078, .02, -.098), (s * .088, .105, .084),
            (s * .108, .02, .066), (s * .108, .07, -.012), (s * .078, -.105, .025), (s * .066, -.085, -.098),
            (s * .05, .17, .055), (s * .05, .12, -.13)]
# --- 1. remove the Meshy head and crown, cap the neck -------------------------------------------------------------
hb0 = bmesh.new()
for p in PTS:
    hb0.verts.new(W(*p))
bmesh.ops.convex_hull(hb0, input=hb0.verts); hb0.normal_update()
HULL_PLANES = [(f.calc_center_median(), f.normal.copy()) for f in hb0.faces]; hb0.free()
def in_hull(c, margin=.012):
    return max(n.dot(c - q) for q, n in HULL_PLANES) < margin
bm = bmesh.new(); bm.from_mesh(me)
def in_head(c):
    if in_hull(c):
        return True
    if c.z > 1.62 and abs(c.x) < .30 and c.y < .08:          # old head top and crown
        return True
    if c.z > 1.54 and abs(c.x) < .16 and c.y < -.04:          # old face, in front of the kept back of the neck
        return True
    return c.z > 1.50 and c.y < -.24 and abs(c.x) < .16          # the snout's underside
dead = [f for f in bm.faces if in_head(f.calc_center_median())]
bmesh.ops.delete(bm, geom=dead, context='FACES')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
seen = set(); comps = []                       # leftover islands of the old head (a jaw fragment)
for f in bm.faces:
    if f in seen:
        continue
    st = [f]; comp = []; seen.add(f)
    while st:
        g = st.pop(); comp.append(g)
        for e in g.edges:
            for h in e.link_faces:
                if h not in seen:
                    seen.add(h); st.append(h)
    comps.append(comp)
comps.sort(key=len, reverse=True)
bmesh.ops.delete(bm, geom=[f for c in comps[1:] for f in c], context='FACES')
print('ISLANDS removed', [len(c) for c in comps[1:]][:8])
edges = [e for e in bm.edges if e.is_boundary]
res = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
# the neck cap: a fan from a point inside the new head, so the cap rises from the cut edge into the head (no flat
# plate behind it, and no folds outside it: an apex raised in place folded into a dark crease under the muzzle)
poked = bmesh.ops.poke(bm, faces=res['faces'], offset=0.0)
for v in poked['verts']:
    v.co = W(0, .0, -.03)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
print('CUT faces', len(dead), 'holes filled', len(res['faces']))
bm.to_mesh(me); bm.free()

# --- 2. skull and muzzle hull ---------------------------------------------------------------------------------------
hb = bmesh.new()
for p in PTS:
    hb.verts.new(W(*p))
bmesh.ops.convex_hull(hb, input=hb.verts)
bmesh.ops.triangulate(hb, faces=[f for f in hb.faces if len(f.verts) > 3])
hm = bpy.data.meshes.new('HeadHull'); hb.to_mesh(hm); hb.free()
head = bpy.data.objects.new('HeadHull', hm); bpy.context.scene.collection.objects.link(head)

def bipyramid(name, centre, axis, rx, ry, depth, sides=6, roll=.0):
    ax = axis.normalized(); up = Vector((0, 0, 1)); side = ax.cross(up).normalized(); up2 = side.cross(ax).normalized()
    b = bmesh.new()
    ring = [b.verts.new(centre + side * (math.cos(t) * rx) + up2 * (math.sin(t) * ry))
            for t in [i * math.tau / sides + roll for i in range(sides)]]
    tip = b.verts.new(centre + ax * depth); back = b.verts.new(centre - ax * depth)
    for i in range(sides):
        p, q = ring[i], ring[(i + 1) % sides]
        b.faces.new((p, q, tip)); b.faces.new((q, p, back))
    bmesh.ops.recalc_face_normals(b, faces=b.faces)
    m = bpy.data.meshes.new(name); b.to_mesh(m); b.free()
    o = bpy.data.objects.new(name, m); bpy.context.scene.collection.objects.link(o); return o

# --- 3. eye sockets: an angular pocket under each brow, a gem inside --------------------------------------------------
EYE = []; CUT_PLANES = []
for s in (1, -1):
    c = W(s * .072, .124, .036)
    out = Vector((s * .50, -.80, .30)).normalized()          # world: out to the side, forward (-y), a little up
    EYE.append((c, out))
    cutter = bipyramid(f'cut{s}', c, out, .043, .027, .026, sides=6, roll=.25)
    CUT_PLANES.append([(cutter.matrix_world @ f.center, (cutter.matrix_world.to_3x3() @ f.normal).normalized())
                       for f in cutter.data.polygons])
    mod = head.modifiers.new('sock', 'BOOLEAN'); mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'; mod.object = cutter
    bpy.context.view_layer.objects.active = head; bpy.ops.object.modifier_apply(modifier='sock')
    bpy.data.objects.remove(cutter)
gems = [bipyramid(f'gem{i}', c - o * .003, o, .033, .020, .012, sides=6, roll=.25) for i, (c, o) in enumerate(EYE)]

def on_cutter(v):   # a vertex on a convex cutter's surface: its largest plane distance is zero
    return any(abs(max(n.dot(v - c) for c, n in planes)) < 2e-4 for planes in CUT_PLANES)


# --- 3b. body-like facet density (round 4: the hull's few large planes read cruder than the body) -------------------
# split edges over 48 mm until the head's median edge is near the body's (chest/shoulders: 37 mm median), then jitter
# vertices off the planes (+-2.5 mm along the normal, +-2 mm across) so the facets are irregular like the body's;
# vertices on sharp ridges (dihedral over 28 deg) and on the socket cut stay put, keeping brow, jaw and sockets crisp
import random
rng = random.Random(5961)
def densify_and_jitter(obj, max_edge=.048, keep=lambda v: False, amp=(.0025, .002)):
    b = bmesh.new(); b.from_mesh(obj.data)
    for _ in range(8):
        long_e = [e for e in b.edges if e.calc_length() > max_edge]
        if not long_e:
            break
        bmesh.ops.subdivide_edges(b, edges=long_e, cuts=1, use_grid_fill=False)
        bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 3])
    b.normal_update()
    sharp = set()
    for e in b.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(28):
            sharp.update(e.verts)
    moved = 0
    for v in b.verts:
        if v in sharp or keep(v.co):
            continue
        n = v.normal; t1 = n.orthogonal().normalized(); t2 = n.cross(t1)
        v.co += n * rng.uniform(-amp[0], amp[0]) + t1 * rng.uniform(-amp[1], amp[1]) + t2 * rng.uniform(-amp[1], amp[1])
        moved += 1
    bmesh.ops.triangulate(b, faces=[f for f in b.faces if len(f.verts) > 3])
    b.to_mesh(obj.data); b.free(); return moved
# round 5: the body reads faceted because neighbouring facets differ by several degrees (chest and shoulders:
# dihedral median 15 deg, p90 39 deg; round 4's head: median 5.5 deg); +-2.5 mm moved too little, so the normal
# offset is tuned until the head's dihedral distribution matches the body's (dihedral.py)
JIT = float(os.environ.get('HEAD_JITTER', .0075))
moved = densify_and_jitter(head, keep=lambda co: on_cutter(co), amp=(JIT, JIT * .5))
print('HULL densified', len(head.data.polygons), 'faces, jittered', moved)

# --- 4. crown shards ---------------------------------------------------------------------------------------------------
SHARDS = [((0, -.01, .11), (0, -.68, .73), .225, .036), ((0, -.11, .07), (0, -.92, .38), .19, .03)]
for s in (1, -1):
    SHARDS += [((s * .05, -.02, .10), (s * .45, -.55, .70), .24, .031),
               ((s * .09, -.02, .062), (s * .78, -.48, .40), .21, .029),
               ((s * .10, -.05, .005), (s * .88, -.45, -.06), .17, .025)]
sb = bmesh.new()
for base, d, length, r in SHARDS:
    b0 = W(*base); dw = Vector((d[0], -d[1], d[2])).normalized()
    side = dw.cross(Vector((0, 0, 1))); side = side.normalized() if side.length > 1e-3 else Vector((1, 0, 0))
    up2 = side.cross(dw).normalized()
    def ring(at, k):
        return [sb.verts.new(at + (side * math.cos(t) * r * k * (1.0 if i % 2 == 0 else .62)) + up2 * math.sin(t) * r * k * (1.0 if i % 2 == 0 else .62))
                for i, t in enumerate([j * math.tau / 4 + math.pi / 4 for j in range(4)])]
    rings = [ring(b0 - dw * .03, 1.0)]
    for frac, k in ((.28, .92), (.52, .78), (.74, .55)):
        rings.append(ring(b0 + dw * length * frac + side * rng.uniform(-.003, .003), k * rng.uniform(.93, 1.07)))
    # facet breaks along the shard: a slight twist per ring and a jittered corner, so each side is several planes
    for j, rg in enumerate(rings[1:], 1):
        tw = Matrix.Rotation(math.radians(rng.uniform(-9, 9) * j), 3, dw)
        c0 = sum((v.co for v in rg), Vector()) / 4
        for v in rg:
            v.co = c0 + tw @ (v.co - c0) + Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * .003
    tip = sb.verts.new(b0 + dw * length)
    sb.faces.new(list(reversed(rings[0])))
    for ra, rb in zip(rings, rings[1:]):
        for i in range(4):
            sb.faces.new((ra[i], ra[(i + 1) % 4], rb[(i + 1) % 4], rb[i]))
    for i in range(4):
        sb.faces.new((rings[-1][i], rings[-1][(i + 1) % 4], tip))
bmesh.ops.recalc_face_normals(sb, faces=sb.faces)
bmesh.ops.triangulate(sb, faces=[f for f in sb.faces if len(f.verts) > 3])
cm = bpy.data.meshes.new('Crown'); sb.to_mesh(cm); sb.free()
crown = bpy.data.objects.new('Crown', cm); bpy.context.scene.collection.objects.link(crown)

# --- 5. parts and join -------------------------------------------------------------------------------------------------
def tag(o, value_fn):
    attr = o.data.attributes.get('part') or o.data.attributes.new('part', 'INT', 'FACE')
    for p in o.data.polygons:
        attr.data[p.index].value = value_fn(p)
    vg = o.vertex_groups.new(name='HeadRigid'); vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
hull_pts = [Vector(W(*p)) for p in PTS]
def head_part(p):
    return 2 if all(on_cutter(head.data.vertices[i].co) for i in p.vertices) else 3
bpy.ops.object.select_all(action='DESELECT')
tag(head, head_part); tag(crown, lambda p: 3)
for g in gems:
    tag(g, lambda p: 1)
if not me.attributes.get('part'):
    me.attributes.new('part', 'INT', 'FACE')
for o in (head, crown, *gems):
    for poly in o.data.polygons:
        poly.use_smooth = False
    o.select_set(True)
body.select_set(True); bpy.context.view_layer.objects.active = body
counts = {o.name: len(o.data.polygons) for o in (head, crown, *gems)}
bpy.ops.object.join()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3]); bm.to_mesh(me); bm.free()
for p in me.polygons:
    p.use_smooth = False
part = me.attributes['part']
print('HEAD parts', counts, 'head tris', sum(1 for p in me.polygons if part.data[p.index].value), 'total', len(me.polygons),
      'sockets', sum(1 for p in me.polygons if part.data[p.index].value == 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, a[1]))
bpy.ops.export_scene.gltf(filepath=os.path.join(P, a[1].replace('.blend', '.glb')), export_format='GLB', export_materials='NONE')
