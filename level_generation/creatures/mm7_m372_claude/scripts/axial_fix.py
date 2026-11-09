"""Axial joints of m372 (after joints_fix.py; edits work/joints_final.json in place). The veil fooled Meshy's
auto-rig: Spine2 sat 8 cm in front of the chest centre and the neck 4 cm to the side, so the neck -> head segment
leaned 40 deg forward and 23 deg sideways and the source-frame rig tilted the head back by that much in every clip.
Each axial joint keeps its height; its x/y become the centre of the body's cross-section there: the head skin piece
(creature.json hands/garments: garment 0 piece 1) for the neck and head, the gown torso (piece 0 within |x| < TORSO_X
of the centre line, i.e. without the sleeves) for the pelvis and spine joints. Args: -- <step1 blend>"""
import bpy, sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(sys.argv[sys.argv.index('--') + 1]))
ob = bpy.data.objects['Body']
co = np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])
pv = np.zeros(len(co), np.int32); ob.data.attributes['piece'].data.foreach_get('value', pv)
p = os.path.join(HERE, 'work', 'joints_final.json'); d = json.load(open(p)); J = d['joints']
HEADP, GOWNP, TORSO_X, BAND = 1, 0, 0.13, 0.012


def centre(piece, z, xlim=None):
    m = (pv == piece) & (np.abs(co[:, 2] - z) < BAND)
    if xlim:
        m &= np.abs(co[:, 0]) < xlim
    pts = co[m]
    return (pts[:, :2].max(0) + pts[:, :2].min(0)) / 2 if len(pts) > 8 else None


zmin = co[pv == HEADP, 2].min()
for k, piece, xl in (('Pelvis', GOWNP, TORSO_X), ('Spine', GOWNP, TORSO_X), ('Spine1', GOWNP, TORSO_X),
                     ('Spine2', GOWNP, TORSO_X), ('Neck', HEADP, None), ('Head', HEADP, None)):
    z = max(J[k][2], zmin + 0.015) if piece == HEADP else J[k][2]
    c = centre(piece, z, xl)
    if c is None:
        print('AXIAL', k, 'no section at z', round(z, 3)); continue
    old = list(J[k]); J[k] = [float(c[0]), float(c[1]), float(J[k][2])]
    print('AXIAL', k, 'moved cm', round(float(np.linalg.norm(np.array(J[k]) - np.array(old))) * 100, 1), 'to', np.round(J[k], 3).tolist())
# the head joint sits at the skull base, where the section also takes in the occiput (leaned 32 deg back): it goes
# above the neck along the source's own neck -> head direction instead
S = json.load(open(os.path.join(HERE, 'work', 'source_rest.json')))
sd = np.array(S['B_Head']['head']) - np.array(S['B_Neck']['head']); sd /= np.linalg.norm(sd)
dz = J['Head'][2] - J['Neck'][2]
J['Head'] = [float(J['Neck'][0] + sd[0] / sd[2] * dz), float(J['Neck'][1] + sd[1] / sd[2] * dz), float(J['Head'][2])]
n = np.array(J['Head']) - np.array(J['Neck']); print('AXIAL neck->head dir', np.round(n / np.linalg.norm(n), 3).tolist())
json.dump(d, open(p, 'w'), indent=1)
