"""G4/G5 edge stretch over whole clips (m178: rigid clawed hands, so G5's finger check reduces to the wrist band):
every 2nd frame of each action, posed/rest length of every skin edge (garment 0), grouped by the dominant bone of the
edge's first vertex into regions arm (clavicle..hand incl. twist), hand, leg, trunk (pelvis..head) and tail. Prints
per action and region p99 / max and the worst frame and bone; writes work/stretch_all.json.
Args: -- <blend> action [...]"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
names = [g.name for g in body.vertex_groups]
gv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', gv)
dom = np.array([names[max(v.groups, key=lambda e: e.weight).group] if len(v.groups) else '' for v in me.vertices])
E = np.array([tuple(e.vertices) for e in me.edges]); E = E[(gv[E[:, 0]] == 0) & (gv[E[:, 1]] == 0)]
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
def posed():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    P = np.array([tuple(v.co) for v in m.vertices]); ev.to_mesh_clear(); return P
R = posed(); L0 = np.linalg.norm(R[E[:, 0]] - R[E[:, 1]], axis=1)
def region(n):
    if 'Hand' in n or 'Finger' in n: return 'hand'
    if any(k in n for k in ('Clavicle', 'UpperArm', 'Forearm')): return 'arm'
    if any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')): return 'leg'
    if 'Tail' in n: return 'tail'
    return 'trunk'
reg = np.array([region(dom[i]) for i in E[:, 0]])
out = {}
for an in a[1:]:
    act = bpy.data.actions[an]; rig.animation_data.action = act; rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); res = {}
    for f in range(f0, f1 + 1, 2):
        sc.frame_set(f); P = posed()
        r = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1) / np.maximum(L0, 1e-6)
        for g in ('arm', 'hand', 'leg', 'trunk', 'tail'):
            m = reg == g
            if not m.any(): continue
            rr = r[m]; k = int(np.argmax(rr)); p99 = float(np.percentile(rr, 99)); mx = float(rr[k])
            cur = res.get(g)
            if cur is None or mx > cur['max']:
                res[g] = {'max': round(mx, 2), 'frame': f, 'bone': str(dom[E[m][k, 0]]), 'p99': round(max(p99, cur['p99'] if cur else 0), 2)}
            else:
                cur['p99'] = round(max(cur['p99'], p99), 2)
    out[an] = res
    print('G4', an, ' '.join(f"{g}: p99 {v['p99']} max {v['max']} (f{v['frame']} {v['bone']})" for g, v in res.items()))
json.dump(out, open(os.path.join(HERE, 'work', 'stretch_all.json'), 'w'), indent=1)
