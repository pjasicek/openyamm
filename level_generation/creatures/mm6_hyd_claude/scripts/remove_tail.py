"""Meshy built two tails (the left and right reference views put the tail on opposite sides). Remove the second one, a
branch leaving the body's right side (x > X_CUT, Y_MIN < y < Y_MAX, low), on work/hd_base.blend in place (run
prepare_hyd.py first; it also saves the uncut work/hd_source.blend used as the bake source):
delete it, cap the hole (cap loops take the UVs of their boundary corners), relax the cap and a ring around it.
The original native hydra has one tail."""
import bpy, bmesh, os
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_CUT, Y_MIN, Y_MAX, Z_MAX = 0.075, 0.58, 0.89, 0.3
RING, SMOOTH = 3, 8          # light relax: heavier smoothing shrank the body there below the bake cage
o = bpy.data.objects['Hydra']; me = o.data
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
uv = bm.loops.layers.uv.active
def in_tail(c):
    # the branch's root starts further forward where the body widens: a slanted cut x > X_CUT + (Y_MIN - y) * 0.9
    return c.z < Z_MAX and c.y < Y_MAX and c.y > Y_MIN - 0.12 and c.x > X_CUT + max(0.0, Y_MIN - c.y) * 0.9
doomed = [v for v in bm.verts if in_tail(v.co)]
print('TAIL vertices removed', len(doomed))
# the source already has small open holes elsewhere (mouths, crest tips): only the cut's own boundary is capped
rim = {e.other_vert(v) for v in doomed for e in v.link_edges} - set(doomed)
bmesh.ops.delete(bm, geom=doomed, context='VERTS')
# keep only the largest connected piece (drop crumbs the cut may leave)
bm.verts.ensure_lookup_table(); seen = set(); pieces = []
for v in bm.verts:
    if v in seen:
        continue
    stack = [v]; piece = []; seen.add(v)
    while stack:
        a = stack.pop(); piece.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b not in seen:
                seen.add(b); stack.append(b)
    pieces.append(piece)
pieces.sort(key=len)
bmesh.ops.delete(bm, geom=[v for p in pieces[:-1] for v in p], context='VERTS')
boundary_uv = {}
for e in bm.edges:
    if e.is_boundary and e.verts[0] in rim and e.verts[1] in rim:
        for loop in e.link_loops:
            boundary_uv.setdefault(loop.vert, loop[uv].uv.copy())
            boundary_uv.setdefault(loop.link_loop_next.vert, loop.link_loop_next[uv].uv.copy())
edges = [e for e in bm.edges if e.is_boundary and e.verts[0] in rim and e.verts[1] in rim]
print('BOUNDARY edges', len(edges))
filled = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
bmesh.ops.triangulate(bm, faces=filled)
cap = [f for f in bm.faces if all(l.vert in boundary_uv for l in f.loops)]
for f in cap:
    for loop in f.loops:
        loop[uv].uv = boundary_uv[loop.vert]
ring = {v for f in cap for v in f.verts}
for _ in range(RING):
    ring |= {e.other_vert(v) for v in list(ring) for e in v.link_edges}
for _ in range(SMOOTH):
    bmesh.ops.smooth_vert(bm, verts=list(ring), factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(me); bm.free(); me.update()
print('CAP faces', len(cap), 'tris now', sum(len(p.vertices) - 2 for p in me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'hd_base.blend'))
# The bake source keeps the uncut surface: the cap then receives the scales of the old tail root, not stretched UVs.
