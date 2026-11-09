"""Print a blend's Body UV layers, attributes and the shell's wrist boundary loops (analysis for wrist_fill.py). Args: <blend>"""
import bpy, bmesh, sys
import numpy as np
IN = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
print('PROBE uv', [u.name for u in me.uv_layers], 'active', me.uv_layers.active.name)
print('PROBE attrs', [(a.name, a.domain, a.data_type) for a in me.attributes])
bm = bmesh.new(); bm.from_mesh(me)
lp, lk = bm.faces.layers.int['part'], bm.faces.layers.int['hand']
for s in 'LR':
    fa = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Forearm'].head_local); hd = np.array(rig.matrix_world @ rig.data.bones[f'Bip01 {s} Hand'].head_local)
    ax = (hd - fa) / np.linalg.norm(hd - fa)
    be = [e for e in bm.edges if e.is_boundary and e.link_faces[0][lp] == 1 and not e.link_faces[0][lk]]
    near = [e for e in be if all(abs((np.array(v.co) - hd) @ ax) < 0.06 and np.linalg.norm(np.cross(np.array(v.co) - hd, ax)) < 0.06 for v in e.verts)]
    seen = set(); loops = []
    for e in near:
        if e in seen: continue
        st = [e]; comp = []
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x)
            for v in x.verts: st += [y for y in v.link_edges if y in near and y not in seen]
        loops.append(comp)
    for c in loops:
        vs = list({v for e in c for v in e.verts}); Q = np.array([v.co[:] for v in vs])
        t = (Q - hd) @ ax; r = np.linalg.norm(np.cross(Q - hd, ax), axis=1)
        print('PROBE', s, 'loop edges', len(c), 'verts', len(vs), 't', round(t.min(), 4), round(t.max(), 4), 'r', round(r.min(), 4), round(r.max(), 4),
              'closed', all(sum(1 for y in v.link_edges if y in c) == 2 for v in vs))
