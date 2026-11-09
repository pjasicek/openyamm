"""Graft the head-only Smart Topology (meshy/head_smart_v1, from the Codex head turnaround) onto the cleaned body.

The full-body return gave a soft generic face and a lopsided horn layout (two tall horns off-centre, fangs and spikes
scattered); the head-only model follows the symmetric head references. On work/step1.blend:
  - old head: every body vertex above the narrowest neck ring (CUT) and every separate piece above it (horns, spikes,
    fangs) is removed,
  - new head: scaled so its neck-to-skull-top height equals the old head's, centred on the body's neck ring, kept down
    to BAND below the cut, keeping only its neck tube there (its bust, shoulders and strap studs are dropped); the neck
    band overlaps the body's neck,
  - seam: body vertices within BAND below the cut that stand outside the head's neck surface, and head band vertices
    outside the body's neck surface, are moved INSET inside the other surface, so neither edge shows,
  - the head joins the body object 'Queen' with the face attribute part = 1 (body 0) for the separate head texture set.
Writes work/step2.blend and review/graft_<view>.png."""
import bpy, bmesh, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import common
BAND = 0.06
NECK_KEEP = 1.4
INSET = 0.002
J = json.loads((P / 'work' / 'joints.json').read_text())
CUT = J['report']['torso']['neck_z']
SKULL = J['report']['torso']['skull_top_z']
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'step1.blend'))
body = bpy.data.objects['Queen']


def ring_at(co, z, centre, radius=0.15, tol=0.008):
    """Horizontal ring of a vertex cloud near height z around centre: (centre xy, mean radius)."""
    band = co[(np.abs(co[:, 2] - z) < tol) & (np.hypot(co[:, 0] - centre[0], co[:, 1] - centre[1]) < radius)]
    c = band[:, :2].mean(0)
    return c, float(np.hypot(band[:, 0] - c[0], band[:, 1] - c[1]).mean())


bco = np.array([tuple(v.co) for v in body.data.vertices])
neck_c, neck_r = ring_at(bco, CUT, J['joints']['Neck'][:2])
# ---- new head: import, normalise
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P / 'meshy/head_smart_v1/model_urls_glb.glb'))
new = [o for o in set(bpy.data.objects) - before if o.type == 'MESH']
for o in bpy.data.objects:
    o.select_set(o in new)
bpy.context.view_layer.objects.active = new[0]
if len(new) > 1:
    bpy.ops.object.join()
head = bpy.context.view_layer.objects.active
head.name = 'HeadSource'; head.parent = None
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
hco = np.array([tuple(v.co) for v in head.data.vertices])
# its neck: the narrowest horizontal section in the lower half (above the bust's shoulder stub)
lo_z, hi_z = hco[:, 2].min(), hco[:, 2].max()
best = None
for z in np.linspace(lo_z + 0.15 * (hi_z - lo_z), lo_z + 0.5 * (hi_z - lo_z), 40):
    sl = hco[np.abs(hco[:, 2] - z) < 0.004 * (hi_z - lo_z)]
    if len(sl) < 6:
        continue
    w = sl[:, 0].max() - sl[:, 0].min()
    if best is None or w < best[1]:
        best = (z, w)
h_neck_z = best[0]
hc, hr = ring_at(hco, h_neck_z, hco[np.abs(hco[:, 2] - h_neck_z) < 0.01][:, :2].mean(0), radius=1e9,
                 tol=0.004 * (hi_z - lo_z))
# skull top: highest vertex within the neck radius of the head's axis (the horns rise beside and above it)
col = hco[np.hypot(hco[:, 0] - hc[0], hco[:, 1] - hc[1]) < hr * 0.9]
h_skull = float(col[:, 2].max())
s = (SKULL - CUT) / (h_skull - h_neck_z)
M = Matrix.Translation(Vector((neck_c[0], neck_c[1], CUT))) @ Matrix.Scale(s, 4) @ \
    Matrix.Translation(Vector((-hc[0], -hc[1], -h_neck_z)))
head.data.transform(M); head.data.update()
hco = np.array([tuple(v.co) for v in head.data.vertices])
report = {'cut_z': CUT, 'body_neck_radius': neck_r, 'head_scale': s, 'head_neck_radius': hr * s,
          'head_triangles': sum(len(p.vertices) - 2 for p in head.data.polygons)}
# ---- remove the old head and the bust
def delete_where(ob, mask_fn):
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
    # whole pieces above the cut (horns, fangs, spikes) go with it
    label = {}
    for v in bm.verts:
        if v in label:
            continue
        stack = [v]; comp = []
        label[v] = len(comp)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w not in label:
                    label[w] = 0; stack.append(w)
        cz = np.mean([x.co.z for x in comp])
        for x in comp:
            label[x] = cz
    doomed = [v for v in bm.verts if mask_fn(v.co, label[v])]
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    return len(doomed)
report['body_removed'] = delete_where(body, lambda c, piece_z: c.z > CUT or piece_z > CUT)
# below the cut only the neck tube stays (within NECK_KEEP x its radius of the axis): the bust's shoulders and strap
# studs reach up into the band and would poke through the body's shoulders
h_r = hr * s
report['head_removed'] = delete_where(head, lambda c, piece_z: (c.z < CUT - BAND and piece_z < CUT) or (
    c.z < CUT and np.hypot(c.x - neck_c[0], c.y - neck_c[1]) > NECK_KEEP * h_r))
# ---- seam: tuck each overlapping band inside the other surface
def tuck(moving, against, zmin, zmax):
    bm = bmesh.new(); bm.from_mesh(against.data)
    tree = BVHTree.FromBMesh(bm)
    n = 0
    for v in moving.data.vertices:
        if not (zmin <= v.co.z <= zmax):
            continue
        hit = tree.find_nearest(v.co)
        if hit[0] is None:
            continue
        loc, nrm = hit[0], hit[1]
        if (v.co - loc).dot(nrm) > -INSET:
            v.co = loc - nrm * INSET; n += 1
    bm.free(); moving.data.update()
    return n
report['body_tucked'] = tuck(body, head, CUT - BAND, CUT + 0.001)
report['head_tucked'] = tuck(head, body, CUT - BAND - 0.001, CUT - 0.005)
# ---- join, part attribute
for ob, part in ((body, 0), (head, 1)):
    a = ob.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [part] * len(ob.data.polygons))
for o in bpy.data.objects:
    o.select_set(o in (body, head))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body = bpy.context.view_layer.objects.active
report['triangles'] = sum(len(p.vertices) - 2 for p in body.data.polygons)
print('GRAFT', json.dumps(report))
(P / 'work' / 'graft_report.json').write_text(json.dumps(report, indent=1))
scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(str(P / 'review' / 'graft'), 1.95, 0.9, views=('front', 'left', 'three_quarter', 'back'),
                    resolution=(600, 600))
common.render_views(str(P / 'review' / 'graft_body'), 1.2, 2.6, views=('front', 'left'), resolution=(500, 750))
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work' / 'step2.blend'))
