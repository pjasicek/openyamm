"""Meshy flaps on the master (2026-11-01, seen in the first viewer shots). Faces are matched by rest-pose centroid (2 mm).
- `delete`: faces deleted with their loose vertices (the two 34 cm slivers running from the jaw to the right collar, a
  lace remnant inside the face/neck shell). Must not open the surface: the boundary-edge count is reported.
- `delete_parts`: [[lo xyz], [hi xyz]] boxes; every loose part wholly inside one is deleted (back-lace stubs on the
  tunic's back, two spikes at the back of the collar).
- `smooth`: folded flaps (pairs of faces back to back, normals opposite: the left armpit fin, two spikes at the back of
  the collar, the fold beside the neck sliver). Their vertices plus `ring` rings around them are relaxed by
  `iterations` passes of umbrella smoothing with everything else fixed, which lays the flap down into the surface
  without opening a hole; UVs, weights and attributes are unchanged (the flap's paint is squeezed with it).
A first version deleted the flaps instead and opened holes at the collar and armpit (viewer shot, magenta render).
Args (Blender): <in blend> <out blend> <config json>"""
import bpy, bmesh, json, sys
import numpy as np
from mathutils import Vector
a = sys.argv[sys.argv.index('--') + 1:]
cfg = json.load(open(a[2]))
bpy.ops.wm.open_mainfile(filepath=a[0])
body = bpy.data.objects['Body']; rig = body.parent
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
me = body.data; mw = body.matrix_world; mwi = mw.inverted()
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
C = np.array([tuple(mw @ f.calc_center_median()) for f in bm.faces])


def match(t):
    d = np.linalg.norm(C - np.array(t), axis=1); i = int(np.argmin(d))
    if d[i] > 0.002:
        raise SystemExit(f'GEOFIX no face within 2 mm of {t} (nearest {d[i]*1000:.1f} mm)')
    return bm.faces[i]


before = sum(1 for e in bm.edges if e.is_boundary)
moved = set()
for t in cfg.get('smooth', []):            # [x, y, z] or [x, y, z, rings]
    grp = {v.index for v in match(t[:3]).verts}
    for _ in range(int(t[3]) if len(t) > 3 else cfg.get('ring', 1)):
        grp |= {w.index for i in list(grp) for e in bm.verts[i].link_edges for w in e.verts}
    moved |= grp
start = {i: bm.verts[i].co.copy() for i in moved}
for _ in range(cfg.get('iterations', 30)):
    new = {}
    for i in moved:
        v = bm.verts[i]
        nb = [e.other_vert(v).co for e in v.link_edges]
        new[i] = sum(nb, Vector()) / len(nb)
    for i, co in new.items():
        bm.verts[i].co = co
shift = max(((bm.verts[i].co - start[i]).length for i in moved), default=0.0)
kill = list({match(t) for t in cfg.get('delete', [])})
# whole loose parts inside a box ([lo, hi]): Meshy's back-lace stubs and the two spikes at the back of the collar
comp = {}
for v in bm.verts:
    if v.index in comp: continue
    st = [v]; comp[v.index] = v.index; members = [v]
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in comp:
                comp[y.index] = v.index; st.append(y); members.append(y)
    P = np.array([tuple(mw @ m.co) for m in members])
    for lo, hi in cfg.get('delete_parts', []):
        if (P > np.array(lo)).all() and (P < np.array(hi)).all():
            kill += [f for m in members for f in m.link_faces]
            print('GEOFIX part', len(members), 'verts at', P.mean(0).round(3))
            break
kill = list(set(kill))
bmesh.ops.delete(bm, geom=kill, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
after = sum(1 for e in bm.edges if e.is_boundary)
bm.to_mesh(me); bm.free()
bpy.ops.wm.save_as_mainfile(filepath=a[1])
print('GEOFIX deleted', len(kill), 'smoothed verts', len(moved), 'max shift mm', round(shift * 1000, 1),
      'boundary edges', before, '->', after, 'faces now', len(me.polygons))
