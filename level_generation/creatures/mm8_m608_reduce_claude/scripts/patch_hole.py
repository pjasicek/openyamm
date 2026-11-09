"""Close the body's open 28-edge loop on the chest behind the left shoulder: blender -b -P patch_hole.py -- <Cand_xx>
(on work/ladder.blend, saved in place). The installed model has it too: the engine culls back faces, so in the Attack
wind-up the background shows through the chest beside the raised left arm (review/hole/sheet_src.png). The loop
becomes one polygon wound against its rim faces, triangulated (no new vertices, so the rim's Chest weights carry the
patch), and its corners are mapped by planar projection inside one of the body's large stone UV islands at the rim's texel density (the
stone atlas has no free cell; a rim-UV copy would stretch across islands, playbook section 3)."""
import os, sys, bpy, bmesh
from mathutils import Vector, Matrix
cn = sys.argv[sys.argv.index('--') + 1]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); path = os.path.join(HERE, 'work', 'ladder.blend')
bpy.ops.wm.open_mainfile(filepath=path); o = bpy.data.objects[cn]
bm = bmesh.new(); bm.from_mesh(o.data); uvl = bm.loops.layers.uv.active
target = Vector((0.134, 0.077, 0.768))
edges = [e for e in bm.edges if e.is_boundary]
# loops of boundary edges; take the one around the target with more than 3 edges
loops, seen = [], set()
for e in edges:
    if e in seen: continue
    stack, loop = [e], []
    while stack:
        x = stack.pop()
        if x in seen: continue
        seen.add(x); loop.append(x); stack += [y for v in x.verts for y in v.link_edges if y.is_boundary and y not in seen]
    loops.append(loop)
loop = min((l for l in loops if len(l) > 3), key=lambda l: (sum((v.co for x in l for v in x.verts), Vector()) / (2 * len(l)) - target).length)
# patch winding: each rim face uses its boundary edge a->b, the patch uses b->a
nxt = {}
for e in loop:
    f = e.link_faces[0]; lp = next(l for l in f.loops if l.edge == e)
    a, b = lp.vert, lp.link_loop_next.vert
    nxt[b] = a
start = next(iter(nxt)); ring = [start]
while nxt[ring[-1]] != start:
    ring.append(nxt[ring[-1]])
assert len(ring) == len(loop), (len(ring), len(loop))
rim_faces = {e.link_faces[0] for e in loop}
face = bm.faces.new(ring); face.material_index = next(iter(rim_faces)).material_index; face.smooth = True
res = bmesh.ops.triangulate(bm, faces=[face], quad_method='BEAUTY', ngon_method='BEAUTY'); new = res['faces']
# planar projection onto the loop's best-fit plane, mapped into the largest adjacent face's UV triangle
ctr = sum((v.co for v in ring), Vector()) / len(ring)
n = sum((f.normal for f in new), Vector()).normalized(); u = (ring[0].co - ctr); u = (u - n * u.dot(n)).normalized(); w = n.cross(u)
# texel density of the rim faces; the patch goes where all its projected corners land inside one stone UV island
def uv_area(f):
    a, b, c = [l[uvl].uv for l in f.loops][:3]; return abs((b - a).cross(c - a)) / 2
dens = (sum(uv_area(f) for f in rim_faces) / sum(f.calc_area() for f in rim_faces)) ** .5
key = lambda l: (round(l[uvl].uv.x, 5), round(l[uvl].uv.y, 5))
def island(f0):
    out, stack = {f0}, [f0]
    while stack:
        f = stack.pop()
        for l in f.loops:
            for m in l.edge.link_loops:
                g = m.face
                if g in out or g.material_index != f0.material_index: continue
                if {key(l), key(l.link_loop_next)} == {key(m), key(m.link_loop_next)}: out.add(g); stack.append(g)
    return out
def inside(pt, faces):
    for f in faces:
        a, b, c = [l[uvl].uv for l in f.loops][:3]; d1, d2, d3 = (b - a).cross(pt - a), (c - b).cross(pt - b), (a - c).cross(pt - c)
        if (d1 >= 0 and d2 >= 0 and d3 >= 0) or (d1 <= 0 and d2 <= 0 and d3 <= 0): return True
    return False
proj = {l: Vector(((l.vert.co - ctr).dot(u), (l.vert.co - ctr).dot(w))) for f in new for l in f.loops}
best = None
islands, done = [], set()
for f in bm.faces:  # every stone island of the body (the rim's own islands are slivers)
    if f in done or f in new: continue
    isl = [g for g in island(f) if g not in new]; done |= set(isl); islands.append(isl)
islands.sort(key=lambda isl: -sum(uv_area(g) for g in isl))
for scale in (1.0, .7, .5):
    for isl in islands[:30]:
        for g in sorted(isl, key=lambda f: -uv_area(f))[:60]:
            uc = sum((l[uvl].uv for l in g.loops), Vector((0, 0))) / 3
            if all(inside(uc + p * dens * scale, isl) for p in proj.values()):
                best = (uc, dens * scale, len(isl)); break
        if best: break
    if best: break
assert best, 'no island holds the patch'
uc, s, nisl = best
for l, p in proj.items():
    l[uvl].uv = uc + p * s
print('UV patch at', tuple(round(x, 4) for x in uc), 'scale', round(s / dens, 2), 'of the rim texel density; island faces', nisl)
open_after = sum(1 for e in bm.edges if e.is_boundary)
outward = sum(1 for f in new if f.normal.dot(sum((g.normal for g in rim_faces), Vector()).normalized()) > 0)
bm.to_mesh(o.data); bm.free(); o.data.update()
print('PATCHED', len(loop), 'edges ->', len(new), 'faces; open edges left', open_after, '; faces along the rim normal', outward, 'of', len(new))
bpy.ops.wm.save_as_mainfile(filepath=path)
