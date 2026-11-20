"""Motion gate for the candidate attacks, per clip:
- cuts: blade speed per frame (fastest of the two tips of each crescent, m/s); the impact frame is the configured one,
  the cut list is every local speed peak above CUT_MS; each cut's game time once the engine fits [0, impact] to Demon
  A's contact at 0.5 s (harrower_slash's cracks: about 0.12 and 0.55 s);
- edge first: at each cut, the cosine between the convex-edge direction of that crescent and the velocity of its
  fastest tip (> 0: the glowing outer sweep leads; the flat or the back leading reads as a slap);
- feet: slide of each foot's contact: the 10th-percentile horizontal motion of the same foot vertices that are within 1 cm of
  the floor on both frames (the lowest vertex alone hops between claw tips as the foot rolls; a pivot on the ball moves the far claws, not
  the pivot, so a low percentile separates a slide from a pivot), cm summed per clip and
  the worst frame, and the lowest sole;
- jerk at 48 fps (jerk_probe.py's measure) on head, chest, hands and feet, against the same window of the raw source.
Args: -- <blend> <config json> <out json>"""
from pathlib import Path
import sys, json, math
import bpy, numpy as np
from mathutils import Vector, Matrix
P = Path(__file__).resolve().parents[1]
blend, cfgp, outp = sys.argv[sys.argv.index('--') + 1:][:3]
bpy.ops.wm.open_mainfile(filepath=str(Path(blend).resolve()))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene
CFG = {('Harrower_' + c['name']): c for c in json.loads(Path(cfgp).read_text())}
G = {s: json.loads((P / f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
B = {}
for s in 'LR':
    z = Vector(G[s]['handle_axis_hand_local']); x = Vector(G[s]['blade_out_hand_local']); y = z.cross(x)
    if 'glaive' in G[s]:   # the warglaives (install_warglaives.py): x the glowing edge, the left frame mirrored
        x, y = Vector(G[s]['glaive']['edge_hand_local']), Vector(G[s]['glaive']['y_hand_local'])
    M = Matrix((x, y, z)).transposed().to_4x4(); M.translation = Vector(G[s]['handle_centre_hand_local']); B[s] = M
TIPS = {'u': Vector((.22, 0, .36)), 'l': Vector((.22, 0, -.29))}
if 'glaive' in G['R']:
    TIPS = {k: Vector(v) for k, v in zip('ul', G['R']['glaive']['tips_glaive_local']['harrower'])}
CUT_MS = 9.0
VG = [g.name for g in body.vertex_groups]
FOOT = {s: np.array([sum(e.weight for e in v.groups if VG[e.group] in (f'B_{s}_Foot', f'B_{s}_Toe0')) > .5 for v in body.data.vertices]) for s in 'LR'}
JB = ['B_Head', 'B_Spine2', 'B_L_Hand', 'B_R_Hand', 'B_L_Foot', 'B_R_Foot']


def set_action(a):
    rig.animation_data_create(); rig.animation_data.action = a; rig.animation_data.action_slot = a.slots[0]


def mesh():
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get('co', co); ev.to_mesh_clear()
    return co.reshape(-1, 3) @ np.array(body.matrix_world.to_3x3()).T + np.array(body.matrix_world.translation)


def jerk(act, f0, f1):
    set_action(act); ts = np.arange(f0, f1 + 1e-6, 30 / 48); Q = {b: [] for b in JB}
    for f in ts:
        sc.frame_set(int(f), subframe=float(f - int(f)))
        for b in JB: Q[b].append((rig.matrix_world @ rig.pose.bones[b].matrix).to_quaternion())
    out = {}
    for b in JB:
        st = np.array([math.degrees(q0.rotation_difference(q1).angle) for q0, q1 in zip(Q[b][:-1], Q[b][1:])]); st = np.minimum(st, 360 - st)
        out[b] = {'step': round(float(st.max()), 1), 'd2': round(float(np.abs(np.diff(st)).max()), 1)}
    return out


report = {}
for name, c in CFG.items():
    act = bpy.data.actions[name]; set_action(act); n = int(act.frame_range[1]); rows = []
    for f in range(n + 1):
        sc.frame_set(f); r = {}
        for s in 'LR':
            M = rig.matrix_world @ rig.pose.bones[f'B_{s}_Hand'].matrix @ B[s]
            r[s] = {k: np.array(M @ v) for k, v in TIPS.items()}; r[s + 'edge'] = np.array(M.to_3x3() @ Vector((1, 0, 0)))
        V = mesh(); r['feet'] = {s: V[FOOT[s]][np.argmin(V[FOOT[s]][:, 2])] for s in 'LR'}; r['footv'] = {s: V[FOOT[s]] for s in 'LR'}
        rows.append(r)
    speed = {s: np.zeros(n + 1) for s in 'LR'}; lead = {s: np.zeros(n + 1) for s in 'LR'}
    for i in range(1, n + 1):
        for s in 'LR':
            best = None
            for k in TIPS:
                v = (rows[i][s][k] - rows[i - 1][s][k]) * 30; sp = float(np.linalg.norm(v))
                if best is None or sp > best[0]: best = (sp, v)
            speed[s][i] = best[0]
            e = (rows[i][s + 'edge'] + rows[i - 1][s + 'edge']); e /= np.linalg.norm(e)
            lead[s][i] = float(e @ best[1] / max(best[0], 1e-6))
    imp = c['impact'] - c['window'][0]; scale = 0.5 / (imp / 30.0)
    cuts = []
    for s in 'LR':
        a = speed[s]
        for i in range(1, n):
            if a[i] >= a[i - 1] and a[i] >= a[i + 1] and a[i] > CUT_MS:
                cuts.append({'side': s, 'frame': i, 'clip_s': round(i / 30, 3), 'game_s': round(i / 30 * scale if i <= imp else .5 + (i - imp) / 30, 3),
                             'speed_ms': round(float(a[i]), 1), 'edge_lead_cos': round(lead[s][i], 2)})
    cuts.sort(key=lambda x: x['frame'])
    slide = {}
    for s in 'LR':
        tot = 0.0; worst = 0.0
        for i in range(1, n + 1):
            A_, B_ = rows[i - 1]['footv'][s], rows[i]['footv'][s]; m = (A_[:, 2] < .01) & (B_[:, 2] < .01)
            if m.sum() >= 3:
                d = float(np.percentile(np.linalg.norm((B_[m] - A_[m])[:, :2], axis=1), 10)); tot += d; worst = max(worst, d)
        slide[s] = {'planted_slide_cm': round(tot * 100, 1), 'worst_frame_cm': round(worst * 100, 1)}
    soles = [min(r['feet']['L'][2], r['feet']['R'][2]) for r in rows]
    j = jerk(act, 0, n); js = jerk(bpy.data.actions[c['src']], c['window'][0], c['window'][1])
    report[name] = {'source': c['src'], 'window': c['window'], 'seconds': n / 30, 'impact_frame': imp, 'impact_s': round(imp / 30, 3),
                    'windup_fit': round(scale, 2), 'cuts': cuts,
                    'impact_edge_lead_cos': {s: round(float(lead[s][max(1, imp - 1):imp + 2].max()), 2) for s in 'LR'},
                    'feet': slide, 'lowest_sole_cm': [round(min(soles) * 100, 1), round(max(soles) * 100, 1)],
                    'jerk': j, 'jerk_source': js}
    print('MOTION', name, json.dumps({k: v for k, v in report[name].items() if k not in ('jerk', 'jerk_source')}), flush=True)
Path(outp).write_text(json.dumps(report, indent=2) + '\n')
