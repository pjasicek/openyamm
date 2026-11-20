"""Widest cloak tears of a clip on the master (edges stretched > 2x, by their opening in cm): per frame the worst edge
with both vertices' rest positions and dominant bones. Args: blend clip [top]."""
import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Cleric_Rig']; mesh = bpy.data.objects['Cleric']; me = mesh.data
act = bpy.data.actions[a[1]]; arm.animation_data.action = act; arm.animation_data.action_slot = act.slots[0]
PARTS = json.loads(bpy.context.scene['cle_parts'])
part = np.zeros(len(me.polygons), np.int32); me.attributes['part'].data.foreach_get('value', part)
cv = {v for p in me.polygons if PARTS[part[p.index]] == 'Cloak' for v in p.vertices}
E = np.array([tuple(e.vertices) for e in me.edges if e.vertices[0] in cv and e.vertices[1] in cv])
R = np.array([tuple(mesh.matrix_world @ v.co) for v in me.vertices]); rl = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1)
G = {g.index: g.name for g in mesh.vertex_groups}
dom = lambda v: max(me.vertices[v].groups, key=lambda g: g.weight)
f0, f1 = (int(round(x)) for x in act.frame_range)
worst = []
for f in range(f0, f1 + 1):
    bpy.context.scene.frame_set(f)
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(mesh.matrix_world @ v.co) for v in m.vertices]); ev.to_mesh_clear()
    dl = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
    k = dl / np.maximum(rl, 1e-6)
    gain = np.where(k > 2, dl - rl, 0)                       # opening of edges stretched > 2x
    i = int(np.argmax(gain))
    worst.append((float(gain[i]) * 100, f, int(E[i, 0]), int(E[i, 1]), int((k > 2).sum()), float(k[i])))
for s, f, v0, v1, nbad, kk in sorted(worst, reverse=True)[:int(a[2]) if len(a) > 2 else 6]:
    w = lambda v: sorted(((round(g.weight, 2), G[g.group]) for g in me.vertices[v].groups), reverse=True)[:3]
    print('TEAR %.1f cm (x%.1f) frame %d edges>2x %d' % (s, kk, f, nbad), R[v0].round(3), w(v0), '|', R[v1].round(3), w(v1))
