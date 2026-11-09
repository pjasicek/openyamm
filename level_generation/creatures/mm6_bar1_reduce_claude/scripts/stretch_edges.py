"""Bridge faces: edges of work/source.blend Body that stretch under animation (max posed length over every 2nd frame of
every clip vs rest length; > 2x and > 10 mm) in the hands; faces on them join surfaces that move apart (the left
thumb tip was fused to the ring finger). -> work/bridge_faces.npy (face indices), prints edges with bones."""
import os, bpy, bmesh, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
names = {g.index: g.name for g in body.vertex_groups}
dom = [max(((g.weight, names[g.group]) for g in v.groups if names[g.group] != 'ReduceProtect'), default=(0, '-'))[1] for v in me.vertices]
E = np.array([e.vertices[:] for e in me.edges]); hand = np.array([('_Hand' in dom[a] or '_Finger' in dom[a] or '_Hand' in dom[b] or '_Finger' in dom[b]) for a, b in E])
rest = np.array([v.co[:] for v in me.vertices]); L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
Lmax = L0.copy(); where = [''] * len(E)
for act in bpy.data.actions:
    rig.animation_data.action = act
    for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1, 2):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        P = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', P); P = P.reshape(-1, 3); ev.to_mesh_clear()
        L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1); up = L > Lmax; Lmax[up] = L[up]
        for i in np.where(up & hand)[0]: where[i] = f'{act.name}:{f}'
bad = np.where(hand & (Lmax > 2 * L0) & (Lmax > .01))[0]
for i in bad[np.argsort(-Lmax[bad])]:
    a, b = E[i]; print('EDGE', a, b, dom[a], dom[b], 'rest %.1f max %.1f mm' % (L0[i] * 1000, Lmax[i] * 1000), where[i])
es = {tuple(sorted(E[i])) for i in bad}
faces = [p.index for p in me.polygons if any(tuple(sorted(k)) in es for k in p.edge_keys)]
np.save(os.path.join(HERE, 'work/bridge_faces.npy'), np.array(faces, int)); print('BRIDGE EDGES', len(bad), 'faces', len(faces))
