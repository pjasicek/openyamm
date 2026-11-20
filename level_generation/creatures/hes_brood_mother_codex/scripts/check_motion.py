"""Seated upper-body GLB checks using the shared evaluator and actual mesh surfaces."""
import json
import sys
from pathlib import Path

import numpy as np

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P.parent / 'claude_shared/gates'))
from run_gates import Glb, Surface, load_meshes, sample_grid, swing_twist, unit

args = sys.argv[sys.argv.index('--') + 1:]
glb = Glb(P / args[0])
meshes = load_meshes(glb)
queen = next(m for m in meshes if m.label.startswith('BroodMother/'))
report = {'asset': args[0], 'sha256': glb.sha256, 'sample_hz': 60, 'clips': {}, 'failures': []}


def check(name, value, limit, context):
    if value > limit:
        report['failures'].append({'gate': name, 'value': float(value), 'limit': limit, **context})


def samples(mesh, mask, points):
    faces = mesh.faces[np.all(mask[mesh.faces], axis=1)]
    edges = mesh.edges[np.all(mask[mesh.edges], axis=1)]
    return np.concatenate([points[mask], points[faces].mean(1), points[edges].mean(1)])


base = queen.weight(['Base']) > .9999
static = Surface(queen, base).build(queen.rest)
backing = next(m for m in meshes if m.label.startswith('BellyInnerSkin/'))
inner = Surface(backing, np.ones(len(backing.rest), bool)).build(backing.rest)
moving = queen.weight(['B_Head', 'B_Neck', 'B_*_Hand', 'B_*_Finger*', 'B_*_Forearm']) > .9
rest_samples = samples(queen, moving, queen.rest)
rest_d, _ = static.signed(rest_samples)
report['rest_static_penetration_mm'] = float(max(0, -rest_d.min()) * 1000)
report['static_surface_closed'] = static.closed
check('rest_static_penetration_mm', report['rest_static_penetration_mm'], 2, {})
arm = queen.weight(['B_*_UpperArm', 'B_*_Forearm']) > .1
hand = queen.weight(['B_*_Hand', 'B_*_Finger*']) > .1
upper_body = queen.weight(['B_Head', 'B_Neck', 'B_Spine*']) > .1
horn = (queen.rest[:,0] < -2.15) & (queen.rest[:,1] < 1.15) & (queen.rest[:,2] > 3.2)
assert np.all(queen.weight(['B_Head'])[horn] > .9999), 'Horn tip must be rigid on head'
edge_masks = {'upper': np.any(upper_body[queen.edges], axis=1), 'arm': np.any(arm[queen.edges], axis=1), 'hand': np.any(hand[queen.edges], axis=1)}
torso_mask = queen.weight(['B_Spine*', 'B_*_Clavicle']) > .6
torso = Surface(queen, torso_mask)
head_probe = (queen.weight(['B_Head']) > .99) & (queen.rest[:,2] > glb.rest[glb.names['B_Neck'],2,3]+.12)
hand_probe = queen.weight(['B_*_Hand', 'B_*_Finger*']) > .9
ends = {}
for clip, animation, start, end in glb.clips():
    if len(args)>1 and clip not in args[1:]: continue
    times = sample_grid(start, end, 60)
    pose = glb.pose(animation, times)
    values = {'duration_s': float(end - start), 'samples': len(times), 'static_drift_m': 0.,
              'floor_min_m': 100., 'penetration_mm': 0., 'backing_penetration_mm': 0.,
              'upper_p99': 1., 'upper_max': 1., 'torso_penetration_mm': 0., 'extra_hand_max': 1., 'arm_p99': 1., 'arm_max': 1., 'hand_max': 1., 'wrist_swing_deg': 0.,
              'forearm_roll_deg': 0., 'upper_arm_roll_deg': 0., 'rotation_step_deg': 0.}
    for side in 'LR':
        un, fn, hn = [glb.names[f'B_{side}_{n}'] for n in ('UpperArm', 'Forearm', 'Hand')]
        ur, fr, hr = [glb.rest[i, :3, :3] for i in (un, fn, hn)]
        up, fp, hp = [pose[:, i, :3, :3] for i in (un, fn, hn)]
        foreaxis = unit(glb.rest[hn, :3, 3] - glb.rest[fn, :3, 3])
        upperaxis = unit(glb.rest[fn, :3, 3] - glb.rest[un, :3, 3])
        _, roll = swing_twist(np.swapaxes(up @ ur.T @ fr, -1, -2) @ fp, fr.T @ foreaxis)
        values['forearm_roll_deg'] = max(values['forearm_roll_deg'], float(abs(roll).max()))
        fingers = [glb.names[f'B_{side}_Finger{i}'] for i in range(5)]
        handaxis = unit(glb.rest[fingers, :3, 3].mean(0) - glb.rest[hn, :3, 3])
        swing, _ = swing_twist(np.swapaxes(fp @ fr.T @ hr, -1, -2) @ hp, hr.T @ handaxis)
        values['wrist_swing_deg'] = max(values['wrist_swing_deg'], float(swing.max()))
        parent = glb.parents[un]
        neutral = pose[:, parent, :3, :3] @ glb.rest[parent, :3, :3].T @ ur
        _, roll = swing_twist(np.swapaxes(neutral, -1, -2) @ up, ur.T @ upperaxis)
        values['upper_arm_roll_deg'] = max(values['upper_arm_roll_deg'], float(abs(roll).max()))
    rotations = pose[:, :, :3, :3]
    relative = rotations[1:] @ np.swapaxes(rotations[:-1], -1, -2)
    steps = np.degrees(np.arccos(np.clip((np.trace(relative, axis1=-2, axis2=-1) - 1) / 2, -1, 1)))
    values['rotation_step_deg'] = float(steps.max())
    for k, frame in enumerate(pose):
        points = queen.posed(frame)
        values['static_drift_m'] = max(values['static_drift_m'], float(np.linalg.norm(points[base] - queen.rest[base], axis=1).max()))
        for mesh in meshes:
            p = points if mesh is queen else mesh.posed(frame)
            values['floor_min_m'] = min(values['floor_min_m'], float(p[:, 2].min()))
            if mesh.label.startswith('LeftLittleFinger/'):
                stretch = np.linalg.norm(p[mesh.edges[:,0]]-p[mesh.edges[:,1]],axis=1)/mesh.lengths
                values['extra_hand_max'] = max(values['extra_hand_max'],float(stretch.max()))
            if mesh is not queen and mesh is not next((m for m in meshes if m.label.startswith('LeftLittleFinger/')), None):
                values['static_drift_m'] = max(values['static_drift_m'], float(np.linalg.norm(p - mesh.rest, axis=1).max()))
        ratio = np.linalg.norm(points[queen.edges[:, 0]] - points[queen.edges[:, 1]], axis=1) / queen.lengths
        values['upper_p99'] = max(values['upper_p99'],float(np.percentile(ratio[edge_masks['upper']],99)))
        values['upper_max'] = max(values['upper_max'],float(ratio[edge_masks['upper']].max()))
        values['arm_p99'] = max(values['arm_p99'], float(np.percentile(ratio[edge_masks['arm']], 99)))
        values['arm_max'] = max(values['arm_max'], float(ratio[edge_masks['arm']].max()))
        values['hand_max'] = max(values['hand_max'], float(ratio[edge_masks['hand']].max()))
        sampled = samples(queen, moving, points)
        d, _ = static.signed(sampled)
        depth = float(max(0, -d.min()) * 1000)
        if depth > values['penetration_mm']:
            values['penetration_mm'] = depth
            values['worst_contact'] = {'time_s': float(times[k]), 'sample': int(np.argmin(d)),
                                       'point': sampled[np.argmin(d)].tolist()}
        torso.build(points)
        dp, _ = torso.signed(samples(queen, head_probe | hand_probe, points))
        values['torso_penetration_mm'] = max(values['torso_penetration_mm'],float(max(0,-dp.min())*1000))
        di, _ = inner.signed(sampled)
        values['backing_penetration_mm'] = max(values['backing_penetration_mm'], float(max(0, -di.min()) * 1000))
    for key, limit in [('upper_p99', 2), ('upper_max', 4.5), ('torso_penetration_mm', 2), ('extra_hand_max', 4.5), ('static_drift_m', 1e-5), ('arm_p99', 2), ('arm_max', 4.5), ('hand_max', 4.5),
                       ('wrist_swing_deg', 60), ('forearm_roll_deg', 90), ('upper_arm_roll_deg', 60),
                       ('rotation_step_deg', 25), ('penetration_mm', 2), ('backing_penetration_mm', 2)]:
        check(key, values[key], limit, {'clip': clip})
    check('floor_penetration_mm', -values['floor_min_m'] * 1000, 2, {'clip': clip})
    if clip == 'Hit':
        check('hit_duration_s', values['duration_s'], 1.125, {'clip': clip})
    if clip == 'Attack':
        mouth = pose[:,glb.names['Socket_Mouth'],:3,3]
        release = float(times[np.argmax(-mouth[:,1])])
        values['mouth_release_s'] = release
        check('mouth_release_error_s', abs(release-.75), .15, {'clip': clip})
    ends[clip] = pose[[0, -1]]
    report['clips'][clip] = values
    print(clip, json.dumps(values), flush=True)
for name in ('Standing', 'Fidget', 'Attack', 'Hit'):
    if name in ends:
        check('loop_or_return', float(abs(ends[name][0] - ends[name][1]).max()), 1e-5, {'clip': name})
if 'Death' in ends and 'Dead' in ends:
    check('death_dead_continuity', float(abs(ends['Death'][1] - ends['Dead'][0]).max()), 1e-5, {})
    check('dead_held', float(abs(ends['Dead'][1] - ends['Dead'][0]).max()), 1e-5, {})
report['status'] = 'pass' if not report['failures'] else 'needs_revision'
(P / 'review' / (Path(args[0]).stem + '_gates.json')).write_text(json.dumps(report, indent=2) + '\n')
print('STATUS', report['status'], json.dumps(report['failures']))
