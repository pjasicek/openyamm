"""Bind-pose triangles (UV, 3D position, normal, part) of named mesh objects -> npz.

Args: <blend|glb> <out npz> <object>[:<part id>] ...
Part: the object's 'piece' attribute when present (0 body, 1 eye, 2 teeth), plus 10 * the given part id.
Also stores per-vertex head weight (Xheadpiv + Xhead + Xjawpiv) and jaw weight when those groups exist, and 'limb'
(1 where the fit's 'chain' attribute marks a limb/stalk vertex), 'chain' (max chain id of the triangle's vertices, -1
core), 'grp' (per-vertex summed weight of the groups listed in $DUMP_GROUPS) and 'comp' (welded connected component, 0 = largest).
"""
import bmesh
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
U, X, N, P, H, J, L, CH, CP, G = [], [], [], [], [], [], [], [], [], []
for spec in specs:
    name, _, pid = spec.partition(':')
    ob = next(o for o in bpy.data.objects if o.name == name or o.name.startswith(name))
    me = ob.data
    me.calc_loop_triangles()
    uv = me.uv_layers.active.data
    piece = me.attributes.get('piece')
    chain = me.attributes.get('chain')
    gi = {g.name: g.index for g in ob.vertex_groups}
    head = {gi[n] for n in ('Xheadpiv', 'Xhead', 'Xjawpiv') if n in gi}
    jaw = {gi[n] for n in ('Xjawpiv',) if n in gi}
    import os
    grp = {gi[n] for n in os.environ.get('DUMP_GROUPS', '').split(',') if n in gi}
    gw = [sum(g.weight for g in v.groups if g.group in grp) for v in me.vertices]
    hw = [sum(g.weight for g in v.groups if g.group in head) for v in me.vertices]
    jw = [sum(g.weight for g in v.groups if g.group in jaw) for v in me.vertices]
    mw = ob.matrix_world
    bmc = bmesh.new(); bmc.from_mesh(me)
    bmesh.ops.remove_doubles(bmc, verts=bmc.verts, dist=1e-6)
    bmc.verts.ensure_lookup_table()
    # remove_doubles keeps the first vertex of each cluster: map every original vertex through position
    from mathutils.kdtree import KDTree
    kd = KDTree(len(bmc.verts))
    for v in bmc.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    lab = {}
    sizes = []
    for v in bmc.verts:
        if v.index in lab:
            continue
        st = [v]; lab[v.index] = len(sizes); n = 0
        while st:
            x = st.pop(); n += 1
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in lab:
                    lab[y.index] = len(sizes); st.append(y)
        sizes.append(n)
    rank = {c: r for r, c in enumerate(sorted(range(len(sizes)), key=lambda c: -sizes[c]))}
    vcomp = [rank[lab[kd.find(v.co)[1]]] for v in me.vertices]
    for t in me.loop_triangles:
        U.append([tuple(uv[l].uv) for l in t.loops])
        X.append([tuple(mw @ me.vertices[v].co) for v in t.vertices])
        N.append(tuple((mw.to_3x3() @ t.normal).normalized()))
        P.append(10 * int(pid or 0) + (max(piece.data[v].value for v in t.vertices) if piece else 0))
        H.append([hw[v] for v in t.vertices])
        J.append([jw[v] for v in t.vertices])
        L.append([1.0 if chain and chain.data[v].value >= 0 else 0.0 for v in t.vertices])
        G.append([gw[v] for v in t.vertices])
        CH.append(max(chain.data[v].value for v in t.vertices) if chain else -1)
        CP.append(vcomp[t.vertices[0]] + 1000 * int(pid or 0))
np.savez(out, uv=np.array(U, np.float32), xyz=np.array(X, np.float32), normal=np.array(N, np.float32),
         part=np.array(P, np.int32), head=np.array(H, np.float32), jaw=np.array(J, np.float32), limb=np.array(L, np.float32),
         chain=np.array(CH, np.int32), comp=np.array(CP, np.int32), grp=np.array(G, np.float32))
print('DUMPED', len(U))
