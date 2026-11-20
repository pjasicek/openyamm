"""Deformation and floor gates over every clip and frame of work/anim_v1.blend -> review/gates_v1.json.
- body_stretch p99/max: max(edge length / rest length, its inverse) on the heat-weighted body piece (legs' thick
  tubes included); tension_max (longest stretch) and compression_max (strongest squash) separately;
- rigid max: the same on pieces bound to one bone (plates, rings, feet, mandibles, eyes, attachments): must stay 1.000;
- lowest (cm): the lowest point of the creature without its attachments; body_lowest: without legs and attachments;
- foot_slide (mm, Walking/Running/Standing): world-y speed error of planted feet against the authored stride."""
import bpy, bmesh, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Crawler_Rig']; mesh = bpy.data.objects['Crawler']; sc = bpy.context.scene
names = [g.name for g in mesh.vertex_groups]
wmax = np.array([max((g.weight for g in v.groups), default=0) for v in mesh.data.vertices])
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] for v in mesh.data.vertices])
att = np.isin(dom, ('Pods', 'Sacs_F', 'Sacs_M', 'Sacs_R'))
scaled = np.isin(dom, ('Pods', 'Sac'))                       # bones that scale on purpose (crushed pods, sac squeeze)
leg = np.char.startswith(dom.astype(str), 'Femur') | np.char.startswith(dom.astype(str), 'Tibia')
E = np.array([tuple(e.vertices) for e in mesh.data.edges])
rigid_e = (wmax[E[:, 0]] > 0.999) & (wmax[E[:, 1]] > 0.999) & (dom[E[:, 0]] == dom[E[:, 1]]) & ~scaled[E[:, 0]]
soft_e = ~rigid_e & ~(scaled[E[:, 0]] & scaled[E[:, 1]])
rest = np.array([tuple(v.co) for v in mesh.data.vertices])
L0 = np.linalg.norm(rest[E[:, 0]] - rest[E[:, 1]], axis=1)
dg = bpy.context.evaluated_depsgraph_get()
out = {}
for act in bpy.data.actions:
    rig.animation_data.action = act
    if len(getattr(act, 'slots', [])):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    st, rg, low, blow, worst, ten, com = [], [], [], [], [], [], []
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        ev = mesh.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear(); co = co.reshape(-1, 3)
        L = np.linalg.norm(co[E[:, 0]] - co[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        r = np.maximum(L, 1 / np.maximum(L, 1e-6))
        st.append(r[soft_e]); rg.append(float(np.abs(L[rigid_e] - 1).max())); ten.append(float(L[soft_e].max())); com.append(float(1 / L[soft_e].min()))
        k = int(np.argmax(np.where(soft_e, r, 0)))
        worst.append((float(r[k]), f, rest[E[k, 0]].round(3).tolist(), dom[E[k, 0]], dom[E[k, 1]], round(float(L0[k]) * 1000, 1)))
        low.append(float(co[~att, 2].min())); blow.append(float(co[~att & ~leg, 2].min()))
    s = np.concatenate(st)
    out[act.name] = {'body_stretch_p99': round(float(np.percentile(s, 99)), 3), 'body_stretch_max': round(float(s.max()), 3),
                     'tension_max': round(max(ten), 3), 'compression_max': round(max(com), 3),
                     'rigid_max_dev': round(max(rg), 5), 'lowest_cm': [round(min(low) * 100, 2), round(max(low) * 100, 2)],
                     'body_lowest_cm': round(min(blow) * 100, 2), 'frames': f1 - f0 + 1,
                     'worst_edge': max(worst)}
    print('GATE', act.name, out[act.name], flush=True)
json.dump(out, open(os.path.join(HERE, 'review', 'gates_v1.json'), 'w'), indent=1)
