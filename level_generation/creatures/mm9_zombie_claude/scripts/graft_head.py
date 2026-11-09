"""Step B: the head-only Meshy parts on the posed body. The face surface is cut at the neck, its ring moved onto the body's ring with a soft falloff, and bridged, so
head and body are one connected skin. Face/Hair/Teeth/Eyes go in as parts (part ids 10 face, 11 hair locks, 12 teeth, 13 eyes). Hair locks are reduced here.
Args: <pose blend> <head blend> <out blend> <report>"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
POSE, HEAD, OUT = sys.argv[sys.argv.index('--') + 1:]
CUT = 0.797
BODYCUT = 0.815
DROP = BODYCUT - CUT
bpy.ops.wm.open_mainfile(filepath=POSE)
body = bpy.data.objects['Body']
with bpy.data.libraries.load(HEAD) as (src, dst):
    dst.objects = [n for n in src.objects]
parts = {o.name: o for o in dst.objects}
Fc = parts['Face']
co = np.array([tuple(v.co) for v in Fc.data.vertices])
crown = co[:, 2].max(); 
J = np.load(POSE + '.joints.npz')
# place: crown on MM9's, front of the face over MM9's
OFF = np.array([0.0, 0.0, 1.0376 - crown])
OFF[1] = 0.022
print('OFFSET', OFF)
pid = {'Face': 10, 'Hair': 11, 'Teeth': 12, 'Eyes': 13}
bm = bmesh.new(); bm.from_mesh(body.data)
lay = bm.verts.layers.int['part']
# the shoulders' slope comes down from the neck: Meshy's trapezius stands 6 cm above MM9's and left no neck under the chin
for v in bm.verts:
    if v[lay] == 0 and v.co.z > 0.70:
        t = min(1.0, (v.co.z - 0.70) / (BODYCUT - 0.70)); t = t * t * (3 - 2 * t)
        fx = max(0.0, min(1.0, (0.24 - abs(v.co.x)) / 0.14)); fx = fx * fx * (3 - 2 * fx)
        v.co.z -= DROP * t * fx
# Meshy's pectorals read as a woman's breasts: flatten the mounds toward a gaunt male chest (the abs and ribs are paint)
bm.verts.ensure_lookup_table()
for _ in range(30):
    mv = {}
    for v in bm.verts:
        if v[lay] == 0 and v.co.y < 0.03 and 0.5 < v.co.z < 0.72 and abs(v.co.x) < 0.2:
            nb = [e.other_vert(v).co for e in v.link_edges]
            w = min(1.0, (0.2 - abs(v.co.x)) / 0.05) * min(1.0, (v.co.z - 0.5) / 0.05) * min(1.0, (0.72 - v.co.z) / 0.05)
            mv[v] = (sum(nb, Vector()) / len(nb), w)
    for v, (c, w) in mv.items():
        x0 = v.co.x
        v.co = v.co * (1 - 0.6 * w) + c * 0.6 * w
        if abs(x0) < 1e-5: v.co.x = 0
# a dimple at the back's centreline, from the mirror seam
for _ in range(14):
    mv = {}
    for v in bm.verts:
        if v[lay] == 0 and v.co.y > 0.03 and 0.43 < v.co.z < 0.72 and abs(v.co.x) < 0.07 and not v.is_boundary:
            nb = [e.other_vert(v).co for e in v.link_edges]
            mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items():
        x0 = v.co.x
        v.co = v.co * 0.45 + c * 0.55
        if abs(x0) < 1e-5: v.co.x = 0
# the mirrored chest keeps a thin ridge at the centreline under the neck
for _ in range(10):
    mv = {}
    for v in bm.verts:
        if v[lay] == 0 and v.co.z > 0.70 and abs(v.co.x) < 0.03 and v.co.y < 0.03 and not v.is_boundary:
            nb = [e.other_vert(v).co for e in v.link_edges]
            mv[v] = sum(nb, Vector()) / len(nb)
    for v, c in mv.items():
        x0 = v.co.x
        v.co = v.co * 0.5 + c * 0.5
        if abs(x0) < 1e-5: v.co.x = 0
for nm, ob in parts.items():
    t = bmesh.new(); t.from_mesh(ob.data)
    for v in t.verts: v.co += Vector(OFF)
    if nm == 'Face':
        bmesh.ops.holes_fill(t, edges=[e for e in t.edges if e.is_boundary], sides=24)
        r = bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=(0, 0, CUT), plane_no=(0, 0, 1))
        on = [e for e in r['geom_cut'] if isinstance(e, bmesh.types.BMEdge)]
        bmesh.ops.split_edges(t, edges=on)
        # below the plane: delete the components that hold the flared neck base; nape hair layers that hang free stay
        t.verts.ensure_lookup_table()
        seen = set(); dead = []
        for v in t.verts:
            if v in seen or v.co.z > CUT - 1e-5: continue
            st = [v]; seen.add(v); cc = [v]
            while st:
                x = st.pop()
                for e in x.link_edges:
                    y = e.other_vert(x)
                    if y not in seen and y.co.z < CUT + 1e-5: seen.add(y); st.append(y); cc.append(y)
            lo = min(q.co.z for q in cc)
            print('BELOW comp', len(cc), 'zmin %.3f' % lo)
            dead += cc
        bmesh.ops.delete(t, geom=dead, context='VERTS')
        bmesh.ops.remove_doubles(t, verts=t.verts, dist=1e-5)
    if nm == 'Hair':
        bmesh.ops.bisect_plane(t, geom=list(t.verts) + list(t.edges) + list(t.faces), plane_co=(0, 0, 0.805), plane_no=(0, 0, 1), clear_inner=True)
        bmesh.ops.remove_doubles(t, verts=t.verts, dist=0.0008)
        # the voxel lock edges are stair-stepped: relax the boundary verts along their boundary neighbours
        for _ in range(12):
            mv = {}
            for v in t.verts:
                if v.is_boundary and v.co.z > 0.8051:
                    nb = [e.other_vert(v) for e in v.link_edges if e.is_boundary]
                    if len(nb) == 2: mv[v] = (nb[0].co + nb[1].co) * 0.5
            for v, c in mv.items(): v.co = v.co * 0.4 + c * 0.6

    tm = bpy.data.meshes.new('t'); t.to_mesh(tm); t.free()
    nv = len(bm.verts)
    bm.from_mesh(tm)
    bm.verts.ensure_lookup_table()
    for v in bm.verts[nv:]: v[lay] = pid[nm]
    bpy.data.meshes.remove(tm)
bm.verts.ensure_lookup_table()
# rings
def loops(edges):
    edges = set(edges); out = []
    while edges:
        st = [edges.pop()]; cur = {st[0]}
        while st:
            e = st.pop()
            for v in e.verts:
                for f in v.link_edges:
                    if f in edges: edges.remove(f); cur.add(f); st.append(f)
        out.append(list(cur))
    return sorted(out, key=len, reverse=True)


body_ring = loops([e for e in bm.edges if e.is_boundary and e.verts[0][lay] == 0 and abs(e.verts[0].co.z - CUT) < 0.003 and abs(e.verts[1].co.z - CUT) < 0.003])
print('body loops', [len(l) for l in body_ring]); body_ring = body_ring[0]
fl = loops([e for e in bm.edges if e.is_boundary and e.verts[0][lay] == 10 and abs(e.verts[0].co.z - CUT) < 0.002 and abs(e.verts[1].co.z - CUT) < 0.002])
print('face loops', [(len(l), np.round(np.mean([v.co[:] for e in l for v in e.verts], 0), 3).tolist(), np.round(np.ptp([v.co[:] for e in l for v in e.verts], 0), 3).tolist()) for l in fl])
face_ring = max(fl, key=lambda l: np.ptp([v.co.x for e in l for v in e.verts]) if np.mean([v.co.y for e in l for v in e.verts]) > -0.05 else 0)
bv = list({v for e in body_ring for v in e.verts}); fv = list({v for e in face_ring for v in e.verts})
B = np.array([v.co[:] for v in bv]); F = np.array([v.co[:] for v in fv])
print('rings body', len(bv), 'centre', B.mean(0).round(3), 'r', np.ptp(B, 0).round(3), 'face', len(fv), F.mean(0).round(3), np.ptp(F, 0).round(3))
cb, cf = 0.5 * (B.min(0) + B.max(0)), 0.5 * (F.min(0) + F.max(0))


def polar(Q, c):
    a = np.arctan2(Q[:, 1] - c[1], Q[:, 0] - c[0]); r = np.hypot(Q[:, 1] - c[1], Q[:, 0] - c[0]); o = np.argsort(a)
    return a[o], r[o]


ab, rb = polar(B, cb)
# displacement of the face neck: each lower-neck vertex moves to the body ring's polar radius at its angle, falling to 0 over 4 cm
FALL = 0.045
for v in bm.verts:
    if v[lay] != 10 or v.co.z > CUT + FALL: continue
    a = np.arctan2(v.co.y - cf[1], v.co.x - cf[0]); r = np.hypot(v.co.y - cf[1], v.co.x - cf[0])
    w = 1 - (v.co.z - CUT) / FALL; w = w * w * (3 - 2 * w)
    # only the surface of the neck tube
    rt = np.interp(a, np.r_[ab - 2 * np.pi, ab, ab + 2 * np.pi], np.r_[rb, rb, rb])
    af, rf = polar(F, cf)
    r0 = np.interp(a, np.r_[af - 2 * np.pi, af, af + 2 * np.pi], np.r_[rf, rf, rf])
    k = rt / max(r0, 1e-4)
    nx = cb[0] + np.cos(a) * r * k; ny = cb[1] + np.sin(a) * r * k
    v.co.x = v.co.x + (nx - v.co.x) * w; v.co.y = v.co.y + (ny - v.co.y) * w
    v.co.z = v.co.z + (CUT - 0.7 * (CUT - 0.775) - CUT) * 0 
ret = bmesh.ops.bridge_loops(bm, edges=body_ring + face_ring)
print('BRIDGE faces', len(ret['faces']))
bm.to_mesh(body.data); bm.free()
for p in body.data.polygons: p.use_smooth = True
for o in list(bpy.data.objects):
    if o is not body: bpy.data.objects.remove(o)
c = np.array([v.co[:] for v in body.data.vertices])
print('FINAL verts', len(c), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons), 'bbox', c.min(0).round(3), c.max(0).round(3))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
