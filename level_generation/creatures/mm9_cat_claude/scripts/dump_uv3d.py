"""Bind-pose triangles (UV, 3D position, normal, part) of named mesh objects -> npz.

Args: <blend|glb> <out npz> <object>[:<part id>] ...
Part: the object's 'piece' attribute when present (0 body, 1 eye, 2 teeth), plus 10 * the given part id.
Also stores per-vertex head weight (Xheadpiv + Xhead + Xjawpiv) and jaw weight when those groups exist, and 'limb'
(1 where the fit's 'chain' attribute marks a limb/stalk vertex).
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
U, X, N, P, H, J, L, HF = [], [], [], [], [], [], [], []
for spec in specs:
    name, _, pid = spec.partition(':')
    ob = next(o for o in bpy.data.objects if o.name == name or o.name.startswith(name))
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    piece = me.attributes.get('piece')
    chain = me.attributes.get('chain')
    gi = {g.name: g.index for g in ob.vertex_groups}
    import os
    head = {gi[n] for n in os.environ.get('HEAD_GROUPS', 'Xheadpiv,Xhead,Xjawpiv').split(',') if n in gi}
    jaw = {gi[n] for n in os.environ.get('JAW_GROUPS', 'Xjawpiv').split(',') if n in gi}
    hf = me.attributes.get('head')
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
        L.append([1.0 if chain and chain.data[v].value >= 0 else 0.0 for v in t.vertices])
        HF.append(hf.data[t.polygon_index].value if hf else 0)
np.savez(out, uv=np.array(U, np.float32), xyz=np.array(X, np.float32), normal=np.array(N, np.float32),
         part=np.array(P, np.int32), head=np.array(H, np.float32), jaw=np.array(J, np.float32), limb=np.array(L, np.float32),
         headface=np.array(HF, np.int32))
print('DUMPED', len(U))
