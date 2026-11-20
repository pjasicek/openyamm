"""v2: remove the Meshy wing and rebuild a clean shoulder (Blender), before the procedural wing is added.

Deletes the Meshy wing beyond |x| = 0.075 (z > 0.235, -0.36 < y < -0.02), then in the shoulder box every vertex more
than 2.5 mm outside the opened envelope (scripts/shoulder_envelope.py: arm stub and membrane flaps), fills the
holes this leaves, relaxes the fill (boundary fixed) and lifts it onto the envelope. Both sides are processed by |x|
and the result is symmetrized again from +X, so the mesh stays exactly symmetric. Usage: clean_shoulder.py -- <in.blend> <env.npz> <out.blend> <report.json>"""
import bpy, bmesh, json, sys
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); o = bpy.data.objects['Body']; me = o.data
E = np.load(a[1]); ys, zs, env = E['ys'], E['zs'], E['env']
def envelope(y, z):
    fy = (y - ys[0]) / (ys[1] - ys[0]); fz = (z - zs[0]) / (zs[1] - zs[0])
    i = int(np.clip(np.floor(fy), 0, len(ys) - 2)); j = int(np.clip(np.floor(fz), 0, len(zs) - 2)); u = np.clip(fy - i, 0, 1); v = np.clip(fz - j, 0, 1)
    return float((1 - u) * (1 - v) * env[i, j] + u * (1 - v) * env[i + 1, j] + (1 - u) * v * env[i, j + 1] + u * v * env[i + 1, j + 1])
def in_box(c): return abs(c.x) > .04 and -.33 < c.y < -.12 and .25 < c.z < .38
bm = bmesh.new(); bm.from_mesh(me)
wing = [v for v in bm.verts if abs(v.co.x) > .075 and v.co.z > .235 and -.36 < v.co.y < -.02]
bmesh.ops.delete(bm, geom=wing, context='VERTS')
flap = [v for v in bm.verts if in_box(v.co) and abs(v.co.x) > envelope(v.co.y, v.co.z) + .0025]
bmesh.ops.delete(bm, geom=flap, context='VERTS')
loose = [v for v in bm.verts if not v.link_faces]; bmesh.ops.delete(bm, geom=loose, context='VERTS')
# boundary loops whose centre lies at the shoulder (the original mesh has other open holes elsewhere)
seen = set(); edges = []
for e in bm.edges:
    if not e.is_boundary or e in seen: continue
    loop = []; stack = [e]; seen.add(e)
    while stack:
        f = stack.pop(); loop.append(f)
        for v in f.verts:
            for g in v.link_edges:
                if g.is_boundary and g not in seen: seen.add(g); stack.append(g)
    c = sum((v.co for f in loop for v in f.verts), loop[0].verts[0].co * 0) / (2 * len(loop))
    if abs(c.x) > .03 and -.35 < c.y < -.10 and .23 < c.z < .40: edges += loop
filled = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
tri = bmesh.ops.triangulate(bm, faces=filled)['faces']
# subdivide large fill triangles so the patch can relax into a smooth shoulder
for _ in range(2):
    big = [f for f in tri if f.is_valid and f.calc_area() > 1.5e-5]
    if not big: break
    res = bmesh.ops.subdivide_edges(bm, edges=list({e for f in big for e in f.edges}), cuts=1, use_grid_fill=True)
    tri = [f for f in bm.faces if any(v in set(res['geom_inner']) for v in f.verts)] + [f for f in tri if f.is_valid]
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
patch = {v for f in bm.faces for v in f.verts if in_box(f.calc_center_median()) and any(not e.is_boundary for e in v.link_edges)}
boundary_ring = {v for e in edges if e.is_valid for v in e.verts}
free = [v for v in patch if v not in boundary_ring and in_box(v.co) and abs(v.co.x) > .045]
for _ in range(30):
    new = {}
    for v in free:
        nb = [e.other_vert(v).co for e in v.link_edges]
        if nb: new[v] = sum(nb, v.co * 0) / len(nb)
    for v, c in new.items():
        v.co = v.co * .4 + c * .6
        ex = envelope(v.co.y, v.co.z)
        if abs(v.co.x) < ex: v.co.x = ex if v.co.x > 0 else -ex
# the fill triangulation and relaxation are not mirror-exact: symmetrize again from the +X side
bmesh.ops.symmetrize(bm, input=bm.verts[:] + bm.edges[:] + bm.faces[:], direction='X', dist=1e-5)
for v in bm.verts:
    if abs(v.co.x) < 1e-6: v.co.x = 0.
bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
rep = {'meshy_wing_vertices_removed': len(wing), 'flap_vertices_removed': len(flap), 'holes_filled_faces': len(filled),
       'relaxed_vertices': len(free), 'vertices': len(bm.verts), 'boundary_edges': sum(e.is_boundary for e in bm.edges)}
bm.to_mesh(me); bm.free(); me.update()
json.dump(rep, open(a[3], 'w'), indent=2); print('SHOULDER', rep)
bpy.ops.wm.save_as_mainfile(filepath=a[2])
