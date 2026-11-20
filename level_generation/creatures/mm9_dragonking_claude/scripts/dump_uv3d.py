"""Bind-pose triangles (UV, 3D position, normal, part) of named mesh objects -> npz.

Args: <blend|glb> <out npz> <object>[:<part id>] ...
Part: the object's 'piece' attribute when present (0 body, 1 eye, 2 teeth), plus 10 * the given part id.
Also stores per-vertex head weight (Xheadpiv + Xhead + Xjawpiv) and jaw weight when those groups exist, and 'limb'
(the dragon rig's 'chain' group id per vertex: 0 core, 1-2 arms, 3-4 legs, 5-6 wings, 7 tail).
"""
import bpy, sys
import numpy as np

argv = sys.argv[sys.argv.index('--') + 1:]
src, out, specs = argv[0], argv[1], argv[2:]
if src.endswith('.blend'):
    bpy.ops.wm.open_mainfile(filepath=src)
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=src)
for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    if arm.animation_data:
        arm.animation_data.action = None
    for b in arm.pose.bones:
        b.matrix_basis.identity()
bpy.context.view_layer.update()
U, X, N, P, H, J, L = [], [], [], [], [], [], []
for spec in specs:
    name, _, pid = spec.partition(':')
    ob = next(o for o in bpy.data.objects if o.name == name or o.name.startswith(name))
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    piece = me.attributes.get('piece')
    chain = me.attributes.get('chain')
    gi = {g.name: g.index for g in ob.vertex_groups}
    head = {gi[n] for n in ('Xheadpiv', 'Xhead', 'Xjawbase', 'Xjawpivot', 'Xjaw', 'Xtongpiv', 'Xtong') if n in gi}
    jaw = {gi[n] for n in ('Xjawpivot', 'Xjaw', 'Xtongpiv', 'Xtong') if n in gi}
    hw = [sum(g.weight for g in v.groups if g.group in head) for v in me.vertices]
    jw = [sum(g.weight for g in v.groups if g.group in jaw) for v in me.vertices]
    mw = ob.matrix_world
    for t in me.loop_triangles:
        U.append([tuple(uv[l].uv) for l in t.loops])
        X.append([tuple(mw @ me.vertices[v].co) for v in t.vertices])
        N.append(tuple((mw.to_3x3() @ t.normal).normalized()))
        P.append(10 * int(pid or 0) + (max(piece.data[v].value for v in t.vertices) if piece else 0))
        H.append([hw[v] for v in t.vertices])
        J.append([jw[v] for v in t.vertices])
        L.append([float(chain.data[v].value) if chain else -1.0 for v in t.vertices])
np.savez(out, uv=np.array(U, np.float32), xyz=np.array(X, np.float32), normal=np.array(N, np.float32),
         part=np.array(P, np.int32), head=np.array(H, np.float32), jaw=np.array(J, np.float32), limb=np.array(L, np.float32))
print('DUMPED', len(U))
