"""Replace the broken hub (vertex HUB, default 1693, of work/source_pre_hubfix.blend; scripts/hub_caps.py): the Meshy
source capped twelve left-hand holes with one shared vertex, and some of those caps also doubled existing faces into
zero-thickness fins. Delete the hub and its faces, then fill every loop the deletion opened (bmesh holes_fill,
triangulated; loops it skips are built from the ordered rim); each new corner takes the UV of the same vertex in an adjacent old face. Spike tips left on the hub's rim (angle sum under 150 deg) move to the mean of their neighbours.
Verified by counting boundary
loops before and after. Face attribute src_index keeps each surviving face's original index (new faces -1) ->
work/face_map.npy. Saves work/source.blend."""
import os, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HUB = int(os.environ.get('REA_HUB', '1693'))
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
src = bm.faces.layers.int.new('src_index')
for f in bm.faces: f[src] = f.index
uvl = bm.loops.layers.uv.active
hub = bm.verts[HUB]; c = hub.co.copy()
ring_verts = {v for f in hub.link_faces for v in f.verts if v is not hub}
open_before = {frozenset(v.index for v in e.verts) for e in bm.edges if e.is_boundary}
def loops_near():  # edges opened by the deletion: on the hub's rim (the caps reach up to 10 cm), not open before
    return [e for e in bm.edges if e.is_boundary and all(v in ring_verts for v in e.verts)
            and frozenset(v.index for v in e.verts) not in open_before]
print('BOUNDARY EDGES near hub before', len(loops_near()))
bmesh.ops.delete(bm, geom=[hub], context='VERTS')
edges = loops_near(); print('BOUNDARY EDGES near hub after delete', len(edges))
res = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
new = list(res['faces'])
left = loops_near()
if left:  # holes_fill skips some loops (the index fingertip quad): order the rim, wind it against its neighbours
    nxt = {}
    for e in left:
        l = e.link_loops[0]  # the existing face runs l.vert -> next vert; the new face runs the other way
        nxt[l.link_loop_next.vert] = l.vert
    start = next(iter(nxt)); ring = [start]
    seen = set()
    for start in list(nxt):
        if start in seen: continue
        ring = [start]
        while nxt.get(ring[-1]) is not None and nxt[ring[-1]] is not start and len(ring) < 50: ring.append(nxt[ring[-1]])
        seen |= set(ring)
        if nxt.get(ring[-1]) is start and len(ring) >= 3:
            new.append(bm.faces.new(ring)); print('RING', len(ring), 'vertices')
tri = bmesh.ops.triangulate(bm, faces=new)
newf = tri['faces']
for f in newf:
    f[src] = -1
    for l in f.loops:
        old = [x for x in l.vert.link_loops if x.face[src] >= 0]
        if old: l[uvl].uv = old[0][uvl].uv.copy()
print('FILLED', len(newf), 'faces; boundary edges near hub left', len(loops_near()))
import math
for v in bm.verts:  # rim vertices left as spike tips (the thumb cap's far vertex: two faces, 68 deg) flatten into the surface
    if v not in ring_verts or v.is_boundary or len(v.link_faces) < 2: continue
    total = sum(math.degrees(l.calc_angle()) for l in v.link_loops)
    if total < 150:
        nbs = [e.other_vert(v) for e in v.link_edges]; old = v.co.copy()
        v.co = sum((n.co for n in nbs), old * 0) / len(nbs); print('SPIKE', v.index, round(total), 'moved %.1f mm' % ((v.co - old).length * 1000))
bm.faces.ensure_lookup_table()
fmap = np.array([f[src] for f in bm.faces])
bm.to_mesh(me); bm.free(); me.update()
np.save(os.path.join(HERE, 'work/face_map.npy'), fmap)
print('FACES', len(me.polygons), 'new', int((fmap < 0).sum()), 'removed', 10117 - int((fmap >= 0).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'source.blend'))
