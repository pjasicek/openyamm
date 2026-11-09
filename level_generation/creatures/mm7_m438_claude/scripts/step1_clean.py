"""Step 1 of the m438 Smart Topology return (work/st_v1_parts.blend, loose parts P00..P15, 1.75 m, faces -Y, +X = the
zombie's left). Parts: P00 skin (head, torso, both arms; the right arm ends below the elbow; open at the waist inside
the trousers), P01 trousers (closed tube legs; the right leg ends at the knee, z 0.29-0.35), P02 right foot (a wrapped
foot up to z 0.16), P03 left foot (up to the calf inside the trousers), P04 rope belt, P05 rope ends, P06-P09 the four
bone tips of the right-arm stump, P10-P12 three bone rods of the right shin, P13 teeth, P14/P15 eyes.

Repairs:
- P00 has a 5-edge hole on the right flank (z 1.18): filled.
- The right shin has no volume: Smart Topology returned only three bone rods between the trouser cuff and the foot,
  while every native frame (m438sa0..4) shows a full shin, red with ivory bone showing. A closed elliptical lathe P16
  (12 sides, 10 rings, z 0.13 inside the foot -> 0.40 inside the trouser leg, measured from the cuff and foot
  sections) restores the leg; the rods stay half embedded as the visible bone.
Joins the parts into 'Body' with a 'piece' point attribute (part index) and 'orig_co' (rest positions, for the
nearest-vertex weight transfer from Meshy's rigged copy). Args: -- <in blend> <out blend>"""
import bpy, bmesh, sys, os, math
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
P = {o.name: o for o in bpy.data.objects if o.type == 'MESH'}

# ---------------------------------------------------------------- P00: fill the small flank hole
bm = bmesh.new(); bm.from_mesh(P['P00'].data)
be = [e for e in bm.edges if e.is_boundary]
adj = {}
for e in be:
    a, b = e.verts; adj.setdefault(a, []).append(b); adj.setdefault(b, []).append(a)
seen, filled = set(), 0
for v in list(adj):
    if v in seen:
        continue
    comp, st = [], [v]
    while st:
        x = st.pop()
        if x in seen:
            continue
        seen.add(x); comp.append(x); st.extend(adj[x])
    if len(comp) <= 8:                                          # the waist opening (35 edges) stays open
        edges = [e for e in be if e.verts[0] in comp and e.verts[1] in comp]
        bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        filled += 1
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(P['P00'].data); bm.free()

# ---------------------------------------------------------------- P16: the right shin
# (z, centre x, centre y, half-width x, half-depth y); the calf bulges backward (+Y)
PROF = [(0.13, -0.266, 0.026, 0.026, 0.027), (0.16, -0.266, 0.027, 0.030, 0.031), (0.19, -0.264, 0.029, 0.033, 0.035),
        (0.22, -0.261, 0.031, 0.037, 0.040), (0.25, -0.257, 0.034, 0.041, 0.045), (0.28, -0.252, 0.037, 0.044, 0.049),
        (0.31, -0.247, 0.039, 0.046, 0.051), (0.34, -0.242, 0.040, 0.047, 0.051), (0.37, -0.238, 0.041, 0.047, 0.050),
        (0.40, -0.234, 0.042, 0.046, 0.048)]
NS = 12
bm = bmesh.new()
rings = []
for z, cx, cy, rx, ry in PROF:
    rings.append([bm.verts.new((cx + rx * math.cos(2 * math.pi * k / NS), cy + ry * math.sin(2 * math.pi * k / NS), z))
                  for k in range(NS)])
for a, b in zip(rings[:-1], rings[1:]):
    for k in range(NS):
        bm.faces.new((a[k], a[(k + 1) % NS], b[(k + 1) % NS], b[k]))
for r, z, flip in ((rings[0], PROF[0][0], True), (rings[-1], PROF[-1][0], False)):
    c = bm.verts.new((sum(v.co.x for v in r) / NS, sum(v.co.y for v in r) / NS, z))
    for k in range(NS):
        f = (r[(k + 1) % NS], r[k], c) if flip else (r[k], r[(k + 1) % NS], c)
        bm.faces.new(f)
bmesh.ops.triangulate(bm, faces=bm.faces[:])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
me = bpy.data.meshes.new('P16'); bm.to_mesh(me); bm.free()
shin = bpy.data.objects.new('P16', me); bpy.context.scene.collection.objects.link(shin)
for p in me.polygons:
    p.use_smooth = True
P['P16'] = shin

for o in bpy.data.objects:
    o.select_set(False)
for n, o in P.items():
    o.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [int(n[1:])] * len(o.data.vertices))
    o.data.materials.clear()
    o.select_set(True)
bpy.context.view_layer.objects.active = P['P00']
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
body.name = body.data.name = 'Body'
me = body.data
co = np.array([tuple(v.co) for v in me.vertices])
me.attributes.new('orig_co', 'FLOAT_VECTOR', 'POINT').data.foreach_set('vector', co.ravel())
print('CLEAN parts', len(P), 'holes filled', filled, 'shin tris', 2 * NS * (len(PROF) - 1) + 2 * NS,
      'tris', sum(len(p.vertices) - 2 for p in me.polygons), 'verts', len(co),
      'height', round(float(co[:, 2].max() - co[:, 2].min()), 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
