"""Make the rigged armadillo PartUV-valid (PartUV said "Invalid mesh" on rig_v1 and uv_dillo.py fell back to xatlas
charts, which left 4.5 % of the surface on fragments). Reads work/rig_v1.blend, writes work/rig_v2.blend and
work/partuv_test.npz (positions, triangles, skin weights for a direct partuv_charts.py check).

- body (part 0): the hole fill of clean.py left duplicate faces, zero-length edges, 6 degenerate triangles and 17
  non-manifold edges in the mouth and under the rump. Delete duplicate faces, merge coincident vertices (1e-5 m),
  dissolve degenerates, then repeatedly delete the faces on non-manifold edges and fill the holes again;
- face caps (part 1: eye and nostril caps, 1,205 triangles for 0.5 % of the surface): decimated to CAP_RATIO;
- spikes (part 2): rebuilt as SPIKE_SEG-sided open cones (the base sits inside the ball and is never seen), so each
  spike is one developable chart of SPIKE_SEG triangles instead of three fragments; same positions as clean.py,
  rigid on the Spikes bone, flat shaded.
Weights of every kept vertex are unchanged."""
import bpy, bmesh, os, math, json
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAP_RATIO = 0.25
SPIKE_SEG = 8
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
ob = bpy.data.objects['Dillo']
parts = json.load(open(os.path.join(HERE, 'work', 'parts.json')))
BC = Vector(parts['ball_centre']); BR = parts['ball_radius']
gi = {g.name: g.index for g in ob.vertex_groups}


def report(bm, tag):
    pl = bm.faces.layers.int.get('part')
    nm = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    bd = {}
    for e in bm.edges:
        if len(e.link_faces) == 1:
            p = e.link_faces[0][pl]; bd[p] = bd.get(p, 0) + 1
    dg = sum(1 for f in bm.faces if f.calc_area() < 1e-10)
    cnt = {}
    for f in bm.faces:
        cnt[f[pl]] = cnt.get(f[pl], 0) + 1
    print('MESH', tag, 'faces', dict(sorted(cnt.items())), 'nonmanifold', nm, 'boundary', bd, 'degenerate', dg)


bm = bmesh.new(); bm.from_mesh(ob.data)
pl = bm.faces.layers.int.get('part'); dl = bm.verts.layers.deform.verify()
report(bm, 'before')

# ---- body cleanup
seen = {}
dup = []
for f in bm.faces:
    k = tuple(sorted(v.index for v in f.verts))
    if k in seen:
        dup.append(f)
    else:
        seen[k] = f
bmesh.ops.delete(bm, geom=dup, context='FACES_ONLY')
body_v = list({v for f in bm.faces if f[pl] == 0 for v in f.verts})
bmesh.ops.remove_doubles(bm, verts=body_v, dist=1e-5)
bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=[e for e in bm.edges
                                                    if e.link_faces and e.link_faces[0][pl] == 0])
for it in range(6):
    bad = [e for e in bm.edges if len(e.link_faces) > 2 or (len(e.link_faces) == 2 and e.link_faces[0][pl] == 0
                                                             and e.calc_length() < 1e-6)]
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
    bnd = [e for e in bm.edges if len(e.link_faces) == 1 and e.link_faces[0][pl] == 0]
    if not bad and not bnd:
        break
    if bad:
        kill = list({f for e in bad for f in e.link_faces})
        bmesh.ops.delete(bm, geom=kill, context='FACES_ONLY')
        bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
    bnd = [e for e in bm.edges if len(e.link_faces) == 1 and e.link_faces[0][pl] == 0]
    res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    new = res['faces']
    bmesh.ops.triangulate(bm, faces=new)
    for f in bm.faces:
        if f[pl] not in (0, 1, 2, 3):
            f[pl] = 0
    # holes_fill gives new faces the default layer value 0 already; make sure they face out like their neighbours
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f[pl] == 0])
    report(bm, f'pass{it}')

# ---- spikes: rebuild
old = [f for f in bm.faces if f[pl] == 2]
old_v = list({v for f in old for v in f.verts})
bmesh.ops.delete(bm, geom=old_v, context='VERTS')
N = 16
axis_back = Vector((0, 1, 0))
nsp = 0
for i in range(N):
    zf = 1 - 2 * (i + 0.5) / N
    r = math.sqrt(1 - zf * zf); th = math.pi * (3 - math.sqrt(5)) * i
    d = Vector((r * math.cos(th), zf, r * math.sin(th))).normalized()
    if d.dot(-axis_back) > 0.85:
        continue
    m = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
    length = 1.45 * BR; base_r = 0.30 * BR
    before = set(bm.faces)
    res = bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=SPIKE_SEG, radius1=base_r, radius2=0.0,
                                depth=length, matrix=Matrix.Translation(BC + d * (0.85 * BR + length / 2)) @ m)
    vs = res['verts']
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-7)          # the apex ring of radius 0 -> one vertex
    nf = [f for f in bm.faces if f not in before]
    bmesh.ops.triangulate(bm, faces=nf)
    nf = [f for f in bm.faces if f not in before]
    for f in nf:
        f[pl] = 2; f.smooth = False
    for v in {v for f in nf for v in f.verts}:
        v[dl].clear(); v[dl][gi['Spikes']] = 1.0
    # outward normals: the face normal must point away from the spike axis
    for f in nf:
        c = f.calc_center_median() - BC
        axial = d * c.dot(d)
        if f.normal.dot(c - axial) < 0:
            f.normal_flip()
    nsp += 1
print('SPIKES', nsp, 'cones of', SPIKE_SEG)
report(bm, 'spikes')
bm.to_mesh(ob.data); bm.free()

# ---- face caps: decimate
me = ob.data
bpy.context.view_layer.objects.active = ob
for o in bpy.data.objects: o.select_set(o == ob)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
for p in me.polygons:
    p.select = me.attributes['part'].data[p.index].value == 1
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.decimate(ratio=CAP_RATIO)
bpy.ops.mesh.select_all(action='DESELECT')
bpy.ops.object.mode_set(mode='OBJECT')
bm = bmesh.new(); bm.from_mesh(me)
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
report(bm, 'final')
bm.to_mesh(me); bm.free()
empty = [v.index for v in me.vertices if not any(g.weight > 1e-4 for g in v.groups)]
print('UNWEIGHTED', len(empty), 'TRIS', len(me.polygons))
pos = np.array([v.co[:] for v in me.vertices]); tri = np.array([p.vertices[:] for p in me.polygons])
w = np.zeros((len(pos), len(ob.vertex_groups)), np.float32)
for v in me.vertices:
    for g in v.groups:
        w[v.index, g.group] = g.weight
np.savez(os.path.join(HERE, 'work', 'partuv_test.npz'), pos=pos, tri=tri, weights=w)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v2.blend'))
