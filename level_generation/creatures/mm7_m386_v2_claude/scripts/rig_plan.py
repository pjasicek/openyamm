"""Robot rig plan from the Meshy return (work/raw_st1.npz, Meshy frame; 305 separate pieces), rigid binding:
- Body (root, chassis) -> Gun (ball + blue emitter under the chassis), Neck1-2 -> Head, Tail1-7 (vertebra chain);
- per leg Leg_XX (sleeve, arm plate; rotates about the sleeve centre) -> Spike_XX (the spike, slides through the
  sleeve along its axis: native walk frames shift the spikes in their sleeves);
- each piece is bound 100 % to one bone: spikes and sleeves by piece id, gun/head by region, neck/tail vertebrae to
  the nearest chain segment (piece centroid), pieces near a sleeve to that leg, the rest to Body; cables that run
  from the chassis to a sleeve blend per vertex from Body to the leg over 3-9 cm from the sleeve centre.
Joints were read from point plots of the mesh (plot_views.py) and refined to local centroids.
Writes work/rig_plan.json and work/weights.npz."""
import json
from pathlib import Path
import numpy as np
P = Path(__file__).resolve().parents[1]
d = np.load(P / 'work/raw_st1.npz'); co, part = d['co'], d['part']
n = part.max() + 1
LEGS = {'FL': (38, 5), 'FR': (33, 6), 'RL': (37, 2), 'RR': (32, 3)}   # spike piece, sleeve piece
TAIL = [(-0.01, 0.07, 0.014), (-0.001, 0.169, 0.0), (-0.019, 0.258, 0.009), (-0.02, 0.325, 0.049), (-0.014, 0.385, 0.106),
        (0.017, 0.43, 0.17), (0.063, 0.447, 0.228), (0.035, 0.415, 0.288), (0.195, 0.402, 0.287)]
NECK = [(0.01, -0.202, 0.05), (0.013, -0.271, 0.053), (0.022, -0.33, 0.072)]
HEAD_END = (0.06, -0.47, 0.06)
bones = [('Body', None, (0.0, 0.0, -0.03), (0.0, -0.12, -0.03)),
         ('Gun', 'Body', (0.0, -0.11, -0.138), (0.0, -0.256, -0.136))]
bones.append(('Neck1', 'Body', NECK[0], NECK[1])); bones.append(('Neck2', 'Neck1', NECK[1], NECK[2]))
bones.append(('Head', 'Neck2', NECK[2], HEAD_END))
for k in range(len(TAIL) - 1):
    bones.append((f'Tail{k + 1}', 'Body' if k == 0 else f'Tail{k}', TAIL[k], TAIL[k + 1]))
legs = {}
for name, (sp, sl) in LEGS.items():
    s = co[part == sp]; tip = s[np.argmin(s[:, 2])]; top = s[np.argmax(s[:, 2])]
    c = co[part == sl].mean(0)
    axis = (tip - top) / np.linalg.norm(tip - top)
    hip = top + axis * ((c - top) @ axis)          # sleeve centre projected on the spike axis
    legs[name] = (hip, tip, top)
    bones.append((f'Leg_{name}', 'Body', tuple(hip), tuple(tip)))
    bones.append((f'Spike_{name}', f'Leg_{name}', tuple(top), tuple(tip)))
names = [b[0] for b in bones]
idx = {nm: i for i, nm in enumerate(names)}
W = np.zeros((len(co), len(names)), np.float32)
def seg_dist(p, a, b):
    a, b = np.array(a), np.array(b); ab = b - a
    t = np.clip(((p - a) @ ab) / (ab @ ab), 0, 1); return np.linalg.norm(p - (a + np.outer(t, ab)), axis=1)
spike_of = {sp: nm for nm, (sp, sl) in LEGS.items()}; sleeve_of = {sl: nm for nm, (sp, sl) in LEGS.items()}
chain = [b for b in bones if b[0].startswith(('Tail', 'Neck'))]
report = {}
for k in range(n):
    sel = np.nonzero(part == k)[0]; p = co[sel]; c = p.mean(0)
    if k in spike_of:
        W[sel, idx['Spike_' + spike_of[k]]] = 1; report[k] = 'spike'; continue
    if k in sleeve_of:
        W[sel, idx['Leg_' + sleeve_of[k]]] = 1; report[k] = 'sleeve'; continue
    if c[1] < -0.322 and c[2] > -0.02:
        W[sel, idx['Head']] = 1; report[k] = 'head'; continue
    if c[2] < -0.095 and abs(c[0]) < 0.06 and -0.27 < c[1] < 0.03:
        W[sel, idx['Gun']] = 1; report[k] = 'gun'; continue
    dleg = {nm: np.linalg.norm(c - legs[nm][0]) for nm in legs}
    near = min(dleg, key=dleg.get)
    dchain = {b[0]: float(seg_dist(c[None], b[2], b[3])[0]) for b in chain}
    nb = min(dchain, key=dchain.get)
    if (c[1] > 0.08 or c[1] < -0.19) and dchain[nb] < min(dleg.values()) and dchain[nb] < 0.08:
        W[sel, idx[nb]] = 1; report[k] = nb; continue
    if k == 0:
        W[sel, idx['Body']] = 1; report[k] = 'body'; continue
    span = np.ptp(p, axis=0).max()
    if dleg[near] < 0.06 and span < 0.09:
        W[sel, idx['Leg_' + near]] = 1; report[k] = 'leg ' + near; continue
    # cables / plates reaching from the chassis to a sleeve: per vertex blend by distance to the nearest sleeve
    dv = np.stack([np.linalg.norm(p - legs[nm][0], axis=1) for nm in legs], 1)
    j = dv.argmin(1); f = np.clip((0.09 - dv[np.arange(len(p)), j]) / 0.06, 0, 1)
    for i_, v in enumerate(sel):
        W[v, idx['Leg_' + list(legs)[j[i_]]]] = f[i_]; W[v, idx['Body']] = 1 - f[i_]
    report[k] = 'blend' if f.max() > 0 else 'body'
assert np.allclose(W.sum(1), 1)
np.savez(P / 'work/weights.npz', W=W, names=np.array(names))
json.dump({'bones': [(nm, p_, list(map(float, h)), list(map(float, t))) for nm, p_, h, t in bones],
           'legs': {nm: {'hip': legs[nm][0].tolist(), 'tip': legs[nm][1].tolist(), 'top': legs[nm][2].tolist()} for nm in legs},
           'pieces': {int(k): v for k, v in report.items()}}, open(P / 'work/rig_plan.json', 'w'), indent=1)
from collections import Counter
print('PLAN', len(names), 'bones', Counter(v.split()[0] if v.startswith('leg') else v for v in report.values()))
