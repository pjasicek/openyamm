"""Rest-pose body measurements for the carapace spec: per dominant bone the vertex bounds; torso cross-sections
(x half width, front -y, back y) every 2 cm from the pelvis to the neck; limb radii along each limb bone.
Writes work/body_probe.json. Args: -- <blend>"""
import bpy, sys, os, json
import numpy as np
from pathlib import Path
P = Path(__file__).resolve().parents[1]
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
CO = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
names = [g.name for g in body.vertex_groups]
W = np.zeros((len(CO), len(names)))
for v in me.vertices:
    for e in v.groups: W[v.index, e.group] = e.weight
DOM = np.array([names[i] for i in W.argmax(1)])
out = {'bones': {}, 'torso': [], 'limbs': {}}
for n in sorted(set(DOM)):
    X = CO[DOM == n]
    out['bones'][n] = {'n': int(len(X)), 'lo': X.min(0).round(3).tolist(), 'hi': X.max(0).round(3).tolist()}
torso = np.isin(DOM, ['B_Pelvis', 'B_Spine', 'B_Spine1', 'B_Spine2', 'B_Neck', 'B_L_Clavicle', 'B_R_Clavicle'])
for z in np.arange(0.80, 1.50, 0.02):
    m = torso & (np.abs(CO[:, 2] - z) < 0.01)
    if m.sum() < 3: continue
    X = CO[m]
    out['torso'].append({'z': round(float(z), 2), 'halfx': round(float(np.abs(X[:, 0]).max()), 3),
                         'front': round(float(X[:, 1].min()), 3), 'back': round(float(X[:, 1].max()), 3)})
for s in 'LR':
    for b, c in [('UpperArm', 'Forearm'), ('Forearm', 'Hand'), ('Thigh', 'Calf'), ('Calf', 'Foot')]:
        h = np.array(rig.data.bones[f'B_{s}_{b}'].head_local); t = np.array(rig.data.bones[f'B_{s}_{c}'].head_local)
        ax = t - h; L = np.linalg.norm(ax); ax /= L
        rel = CO - h; al = rel @ ax; perp = np.linalg.norm(rel - np.outer(al, ax), axis=1)
        rows = []
        for f in np.arange(0.0, 1.01, 0.1):
            m = (np.abs(al / L - f) < 0.05) & (perp < 0.2)
            rows.append([round(float(f), 1), round(float(np.median(perp[m])), 3) if m.any() else None,
                         round(float(perp[m].max()), 3) if m.any() else None])
        out['limbs'][f'{s}_{b}'] = {'len': round(float(L), 3), 'radius_med_max': rows}
(P / 'work/body_probe.json').write_text(json.dumps(out, indent=1))
print('PROBED'); sys.stdout.flush(); os._exit(0)
