"""hkr skinned-shell stretch: per shell piece and clip, every edge of the piece's outer surface (NV x NU grid of
make_armour.py) posed against rest, r = max(l / l0, l0 / l) per edge and frame; prints p99 and max per piece and clip;
writes review/shell_stretch_<tag>.json. Pass: p99 <= P99 (1.10) and max <= MAXR (1.25): ivory bends at the gaps
between pieces, not inside a piece. Args: -- <blend> <spec json> <tag> <clip> [...]"""
import bpy, sys, os, json
import numpy as np
a = sys.argv[sys.argv.index('--') + 1:]
blend, specp, tag, clips = a[0], a[1], a[2], a[3:]
P99, MAXR = float(os.environ.get('P99', '1.10')), float(os.environ.get('MAXR', '1.25'))
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = json.load(open(specp))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(blend))
rig = bpy.data.objects['Rig']; sc = bpy.context.scene


def ev(ob):
    e = ob.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = e.to_mesh()
    co = np.empty(len(m.vertices) * 3); m.vertices.foreach_get('co', co); e.to_mesh_clear()
    return co.reshape(-1, 3)


rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
pieces = []
for pl in [p for p in SPEC['plates'] if p.get('shell')]:
    ob = bpy.data.objects['Arm_' + pl['name']]; G = pl.get('nu', 9) * pl.get('nv', 8)
    E = np.array([e.vertices[:] for e in ob.data.edges if e.vertices[0] < G and e.vertices[1] < G])
    P0 = ev(ob); L0 = np.linalg.norm(P0[E[:, 0]] - P0[E[:, 1]], axis=1)
    pieces.append((pl['name'], ob, E, L0))
rep, bad = {}, []
for clip in clips:
    act = bpy.data.actions[clip]; rig.animation_data.action = act
    if len(act.slots): rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range); R = {n: [] for n, *_ in pieces}
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        for n, ob, E, L0 in pieces:
            P = ev(ob); L = np.linalg.norm(P[E[:, 0]] - P[E[:, 1]], axis=1)
            R[n].append(np.maximum(L / L0, L0 / np.maximum(L, 1e-9)))
    rep[clip] = {}
    for n in R:
        r = np.concatenate(R[n]); rep[clip][n] = [round(float(np.percentile(r, 99)), 3), round(float(r.max()), 3)]
        if rep[clip][n][0] > P99 or rep[clip][n][1] > MAXR: bad.append(f'{clip}:{n}={rep[clip][n]}')
    w = max(rep[clip].items(), key=lambda kv: kv[1][1])
    print('SHELLSTRETCH', clip, 'worst', w[0], w[1])
json.dump(rep, open(os.path.join(HERE, 'review', f'shell_stretch_{tag}.json'), 'w'), indent=1)
print('SHELLSTRETCH', 'FAIL' if bad else 'PASS', ' '.join(bad))
