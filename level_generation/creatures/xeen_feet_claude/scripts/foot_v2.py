"""Foot v2: drop the enclosed inner shell of the Smart Topology return (every part came back double-walled: 1,265 of
3,234 triangles, 44 % of the surface, sit inside the outer skin and took 44 % of the paint atlas), then lay new UVs
with claude_shared/uv_atlas.py on the visible surface only. The 4K Meshy paint of the v1 layout is carried over by
UV correspondence (transfer_paint.py), so no new paint is needed.
Hidden face = no point of it sees out of the model along any of 162 directions (visibility, not a single ray: a
single normal ray also removed partly covered skin at the wing roots and between the toes and left holes).
Writes work/foot_v2.blend (UVMap = the new layout), work/uv_v2.npz (per triangle: old UV, new UV, rest xyz, part:
0 skin, 1 medial wing, 2 lateral wing) and texturing/foot_v2_layout.glb (static, for gutter_fill / texture_quality)."""
import bpy, bmesh, os, sys, json, math
import numpy as np
from mathutils.bvhtree import BVHTree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, '..', 'claude_shared'))
import uv_atlas
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'foot_uv.blend'))
ob = bpy.data.objects['Foot']; me = ob.data
bvh = BVHTree.FromObject(ob, bpy.context.evaluated_depsgraph_get())
# hidden face = no sample point of it (centre and three points toward its corners) can see out of the model along
# any of 162 directions in its front hemisphere: the enclosed inner shell, never the partly covered skin at wing roots
from mathutils import Vector
dirs = []
gold = math.pi * (3 - math.sqrt(5))
for i in range(162):
    z = 1 - 2 * (i + 0.5) / 162; r = math.sqrt(1 - z * z)
    dirs.append(Vector((r * math.cos(gold * i), r * math.sin(gold * i), z)))
hidden = []
for p in me.polygons:
    vs = [me.vertices[v].co for v in p.vertices]
    pts = [p.center] + [p.center.lerp(v, 0.75) for v in vs]
    seen = False
    for d in dirs:
        if d.dot(p.normal) <= 0.05:
            continue
        for q in pts:
            if bvh.ray_cast(q + p.normal * 2e-5 + d * 2e-5, d, 2.0)[0] is None:
                seen = True; break
        if seen:
            break
    hidden.append(not seen)
hidden = np.array(hidden)
STAGE = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'all'
# the old (painted) UV per face corner, keyed by the face's corner positions (uv_atlas rebuilds the mesh)
old = np.zeros((len(me.loops), 2), np.float32)
me.uv_layers['UVMap'].data.foreach_get('uv', old.ravel())
key = lambda co: tuple(round(c * 1e5) for c in co)
OLDUV = {}
for p in me.polygons:
    if not hidden[p.index]:
        ks = tuple(sorted(key(me.vertices[v].co) for v in p.vertices))
        OLDUV[ks] = {key(me.vertices[v].co): old[l] for v, l in zip(p.vertices, p.loop_indices)}
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in np.nonzero(hidden)[0]], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
bm.to_mesh(me); bm.free(); me.update()
print('INNER removed', int(hidden.sum()), 'faces; kept', len(me.polygons), 'boundary edges', boundary)
if STAGE == 'mesh':
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'foot_v2_mesh.blend'))
    raise SystemExit
names = [g.name for g in ob.vertex_groups]
PART = {'Foot': 0, 'Toes': 0, 'WingIn': 1, 'WingOut': 2}
report = uv_atlas.unwrap(ob, head_groups=('Toes',), head_factor=1.4)
print('UV', report.get('use'), report.get('charts_used'), report.get('packer_used'), report.get('fallbacks'))
me = ob.data
n = len(me.loops)
new = np.zeros((n, 2), np.float32); me.uv_layers['UVMap'].data.foreach_get('uv', new.ravel())
oldc = np.zeros((n, 2), np.float32); miss = 0
for p in me.polygons:
    ks = tuple(sorted(key(me.vertices[v].co) for v in p.vertices))
    m = OLDUV.get(ks)
    if m is None:
        miss += 1; continue
    for v, l in zip(p.vertices, p.loop_indices):
        oldc[l] = m[key(me.vertices[v].co)]
print('OLDUV matched', len(me.polygons) - miss, 'missed', miss)
if miss: raise SystemExit('old UV match failed')
dom = [PART[names[max(v.groups, key=lambda g: g.weight).group]] for v in me.vertices]
tri_l = np.array([p.loop_indices[:] for p in me.polygons]); tri_v = np.array([p.vertices[:] for p in me.polygons])
xyz = np.array([v.co[:] for v in me.vertices], np.float32)[tri_v]
part = np.array([max(dom[v] for v in t) for t in tri_v], np.int32)
np.savez(os.path.join(HERE, 'work', 'uv_v2.npz'), old=oldc[tri_l], new=new[tri_l], xyz=xyz, part=part)
json.dump({'removed_inner': int(hidden.sum()), 'triangles': len(me.polygons), 'boundary_edges': boundary,
           'uv': {k: report.get(k) for k in ('use', 'charts_used', 'packer_used', 'fallbacks')}},
          open(os.path.join(HERE, 'work', 'foot_v2.json'), 'w'), indent=1, default=str)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'foot_v2.blend'))
for o in bpy.data.objects: o.select_set(o == ob)
bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'texturing', 'foot_v2_layout.glb'), use_selection=True,
                          export_format='GLB', export_yup=True, export_skins=False, export_animations=False,
                          export_materials='NONE', export_attributes=False)
print('SAVED foot_v2.blend tris', len(me.polygons))
