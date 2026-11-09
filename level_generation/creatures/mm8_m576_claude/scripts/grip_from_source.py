"""H6: derive the left-hand grip (handle axis) of the RPG humanoid set from its own curled fingers.
Each finger chain (index..pinky: B_L_Finger1..4 with two child joints and the tip) wraps the handle, so a circle fitted
through its three joint heads (knuckle and two inner joints; the imported tails are unusable) has its centre on the handle axis. The axis is the line
through the four centres; the handle radius is the mean circle radius minus a finger half-thickness. Reported per
clip/frame for consistency, and the chosen grip is written in B_L_Hand bone space to work/grip_source.json.
Args: -- <set glb> clip:frame [clip:frame ...]   (first entry defines the stored grip)"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index('--') + 1:]
glb, picks = a[0], a[1:]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
acts = {x.name.split('@')[-1].split('|')[-1]: x for x in bpy.data.actions}
W = arm.matrix_world


def circle(pts):
    c = pts.mean(0); u, s, vt = np.linalg.svd(pts - c); e1, e2, nrm = vt[0], vt[1], vt[2]
    xy = np.stack([(pts - c) @ e1, (pts - c) @ e2], 1)
    A = np.column_stack([2 * xy, np.ones(len(xy))]); b = (xy ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = sol[:2]; r = math.sqrt(sol[2] + cx * cx + cy * cy)
    resid = np.abs(np.linalg.norm(xy - [cx, cy], axis=1) - r).max()
    return c + cx * e1 + cy * e2, r, resid, nrm


def chain(i):
    # joint heads only: the importer gives the B_* bones meaningless tails (lengths of tens of metres)
    names = [f'B_L_Finger{i}', f'B_L_Finger{i}1', f'B_L_Finger{i}2']
    return np.array([np.array(W @ arm.pose.bones[n].head) for n in names])


stored = None
for pk in picks:
    clip, frame = pk.rsplit(':', 1)
    act = acts.get(clip) or next(x for k, x in acts.items() if k.endswith(clip))
    arm.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        arm.animation_data.action_slot = act.slots[0]
    bpy.context.scene.frame_set(int(frame))
    centres, radii, res = [], [], []
    for i in (1, 2, 3, 4):
        c, r, rs, _ = circle(chain(i))
        centres.append(c); radii.append(r); res.append(rs)
    centres = np.array(centres); m = centres.mean(0)
    ax = np.linalg.svd(centres - m)[2][0]
    off = np.linalg.norm((centres - m) - np.outer((centres - m) @ ax, ax), axis=1)
    hand = W @ arm.pose.bones['B_L_Hand'].matrix
    thumb = np.array(W @ arm.pose.bones['B_L_Finger0'].head)
    if np.dot(np.array(W @ arm.pose.bones['B_L_Finger1'].head) - np.array(W @ arm.pose.bones['B_L_Finger4'].head), ax) < 0:
        ax = -ax                                               # point the axis out of the index/thumb side
    span = (centres - m) @ ax
    print(f'GRIP {clip}@{frame}: finger circle radii cm {np.round(np.array(radii) * 100, 2)}, fit resid cm '
          f'{np.round(np.array(res) * 100, 2)}, centres off-axis cm {np.round(off * 100, 2)}, centre span cm '
          f'{round(float(span.max() - span.min()) * 100, 1)}, knuckle span cm '
          f'{round(float(np.linalg.norm(chain(1)[0] - chain(4)[0])) * 100, 1)}')
    if stored is None:
        inv = hand.inverted()
        stored = {'source': pk, 'centre_hand': list(inv @ Vector(m)), 'axis_hand': list((inv.to_3x3() @ Vector(ax)).normalized()),
                  'finger_circle_radius_m': float(np.median(radii)), 'scale_note': 'source units (character ~2.4 m tall)'}
out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work', 'grip_source.json')
json.dump(stored, open(out, 'w'), indent=1)
print('STORED', json.dumps(stored))
