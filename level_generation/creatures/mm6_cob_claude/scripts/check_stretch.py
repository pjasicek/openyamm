"""Edge-stretch check on work/anim_v1.blend: per clip frame, deformed edge length / rest length. Reports the worst
edges (ratio and absolute growth) with their vertices' rest position and top bone weights - a stray weight on a
single vertex shows up as a long spike."""
import bpy
import numpy as np
rig = bpy.data.objects['Cobra_Rig']; mesh = bpy.data.objects['Cobra']; sc = bpy.context.scene; me = mesh.data
rest = np.array([tuple(v.co) for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges])
L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
names = {g.index: g.name for g in mesh.vertex_groups}
worst = {}
GROW = 0.015
for act in ('Standing', 'Walk', 'Attack', 'Hit', 'Death', 'Fidget'):
    A = bpy.data.actions[act]; rig.animation_data.action = A
    f0, f1 = map(int, A.frame_range)
    for f in range(f0, f1 + 1):
        if False:
            break
        sc.frame_set(f)
        ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        co = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear()
        L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1)
        grow = L - L0
        for i in np.nonzero((grow > GROW) & (L > 2.5 * L0))[0]:
            if grow[i] > worst.get(int(i), (0,))[0]:
                worst[int(i)] = (float(grow[i]), act, f)
print('STRETCH edges', len(worst))
verts = set()
for i, (g, act, f) in sorted(worst.items(), key=lambda kv: -kv[1][0])[:12]:
    a, b = E[i]; verts |= {int(a), int(b)}
    print(f'STRETCH edge {i} verts {a},{b} grows {g * 100:.1f} cm ({act} f{f}) rest {rest[a].round(3)} {rest[b].round(3)}')
for v in sorted(verts):
    ws = sorted(((g.weight, names[g.group]) for g in me.vertices[v].groups), reverse=True)[:4]
    print('STRETCH vert', v, rest[v].round(3), [(n, round(w, 2)) for w, n in ws])
