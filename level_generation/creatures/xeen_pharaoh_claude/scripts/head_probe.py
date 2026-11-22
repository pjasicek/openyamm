"""Rest-pose head study of mm8_m404: connected components of LOD0 near the head, bone frames (B_Head, B_Neck,
B_L_Hand, B_R_Hand) in glTF model space. Usage: blender -b --python head_probe.py -- <glb> <out.json>"""
import bpy, bmesh, json, sys
from mathutils import Vector
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=argv[0])
sc = bpy.context.scene
arm = next(o for o in sc.objects if o.type == 'ARMATURE')
arm.animation_data_clear() if arm.animation_data else None
for pb in arm.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
out = {'bones': {}}
for name in ('B_Head', 'B_Neck', 'B_L_Hand', 'B_R_Hand', 'B_Spine2', 'B_L_Forearm', 'B_R_Forearm', 'B_Pelvis'):
    pb = arm.pose.bones[name]
    m = arm.matrix_world @ pb.matrix
    out['bones'][name] = {'head': list(arm.matrix_world @ pb.head), 'tail': list(arm.matrix_world @ pb.tail),
                          'matrix': [list(r) for r in m]}
body = next(o for o in sc.objects if o.type == 'MESH' and o.name in ('M404',))
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bm.verts.ensure_lookup_table()
mw = body.matrix_world
vg = {g.index: g.name for g in body.vertex_groups}
# component labels
seen = {}
comps = []
for v in bm.verts:
    if v.index in seen: continue
    stack = [v]; seen[v.index] = len(comps); members = []
    while stack:
        x = stack.pop(); members.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen[y.index] = len(comps); stack.append(y)
    comps.append(members)
hz = out['bones']['B_Head']['head'][2]
res = []
for i, mem in enumerate(comps):
    pts = [mw @ v.co for v in mem]
    lo = Vector(map(min, *pts)) if len(pts) > 1 else pts[0]
    hi = Vector(map(max, *pts)) if len(pts) > 1 else pts[0]
    nf = len({f.index for v in mem for f in v.link_faces})
    res.append({'i': i, 'verts': len(mem), 'faces': nf, 'lo': list(lo), 'hi': list(hi)})
res.sort(key=lambda r: -r['faces'])
out['components'] = res
out['n_components'] = len(comps)
json.dump(out, open(argv[1], 'w'), indent=1)
print('COMPONENTS', len(comps), [ (r['faces'], [round(x,2) for x in r['lo']], [round(x,2) for x in r['hi']]) for r in res[:40]])
print('HEAD', out['bones']['B_Head']['head'], out['bones']['B_Head']['tail'])
