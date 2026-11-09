"""Add a grounded casting step while preserving the fitted library upper-body channels."""
from pathlib import Path
import ast, json, math, sys
import bpy
import numpy as np
from mathutils import Vector, Matrix
p = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(p / 'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p / 'work/pre_cast_step.blend'))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; scene = bpy.context.scene
scene.render.fps = 30

def attach(action):
    rig.animation_data.action = None
    for pb in rig.pose.bones: pb.matrix_basis.identity()
    if action:
        rig.animation_data.action = action; rig.animation_data.action_slot = action.slots[0]

def snap(): return {b.name: b.matrix_basis.copy() for b in rig.pose.bones}
def apply(row):
    attach(None)
    for n, m in row.items(): rig.pose.bones[n].matrix_basis = m
    bpy.context.view_layer.update()
def coords():
    ob = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); mesh = ob.to_mesh()
    result = np.array([v.co[:] for v in mesh.vertices]); ob.to_mesh_clear(); return result

def ease(x):
    x = min(1., max(0., x)); return x*x*x*(x*(6*x-15)+10)

def world(name, matrix):
    rig.pose.bones[name].matrix = matrix
    bpy.context.view_layer.update()

attach(bpy.data.actions['Standing']); scene.frame_set(0); ready = snap()
feet = {s: rig.pose.bones[f'B_{s}_Foot'].matrix.copy() for s in 'LR'}
toes = {s: rig.pose.bones[f'B_{s}_Toe0'].head.copy() for s in 'LR'}
knees = {s: rig.pose.bones[f'B_{s}_Calf'].head.copy() for s in 'LR'}
base = coords(); pv = np.array([v.value for v in body.data.attributes['piece'].data])
cloth = np.where(np.isin(pv, [2, 5, 12, 13, 14, 15, 16]))[0]
cloth_bones = [b.name for b in rig.data.bones if b.name.startswith('Robe_')]
W = np.zeros((len(cloth), len(cloth_bones))); indexes = {n: i for i, n in enumerate(cloth_bones)}
for row, i in enumerate(cloth):
    for g in body.data.vertices[int(i)].groups:
        n = body.vertex_groups[g.group].name
        if n in indexes: W[row, indexes[n]] = g.weight
pinv = np.linalg.solve(W.T @ W + .002*np.eye(len(cloth_bones)), W.T)
# The fitted robe follows the waist above the knees and the supporting legs below them.
height = np.clip(base[cloth, 2] / 1.13, 0., 1.)
left = np.clip((base[cloth, 0] + .20)/.40, 0., 1.)
waist = height**4
front = np.clip((.13-base[cloth, 1])/.30, 0., 1.)
foot_follow = front*(.35+.65*left)
foot_masks = {s: np.array([sum(g.weight for g in v.groups if body.vertex_groups[g.group].name in
    [f'B_{s}_Foot', f'B_{s}_Toe0']) > .5 for v in body.data.vertices]) for s in 'LR'}

# Reuse the playbook's monotone timing curve; the library cast's 2.7-second timing stays intact.
tree = ast.parse((p.parent/'mm6_natm_claude/scripts/author_attack.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'pchip'],
                       type_ignores=[]), 'cast_step_curve', 'exec'))
ts = [0., .35, .75, 1.2, 1.55, 1.95, 2.45, 2.7]
hip = [pchip(ts, vs) for vs in [
    [0., -.018, -.012, .025, .025, -.012, 0., 0.],
    [0., .022, .010, -.090, -.085, -.025, 0., 0.],
    [0., -.020, -.035, -.032, -.015, -.020, 0., 0.]]]

def foot_plan(t):
    out = ease((t-.52)/.48); back = ease((t-1.92)/.48)
    u = out*(1-back); lift = 0.
    for a, b in [(.52, 1.0), (1.92, 2.4)]:
        if a < t < b: lift = .045*math.sin(math.pi*(t-a)/(b-a))**2
    return Vector((.025*u, -.20*u, lift))

def leg_ik(side, target, rotation):
    th, ca, ft = [f'B_{side}_{part}' for part in ['Thigh', 'Calf', 'Foot']]
    h = rig.pose.bones[th].head.copy(); k = rig.pose.bones[ca].head.copy(); a = rig.pose.bones[ft].head.copy()
    l1, l2 = (k-h).length, (a-k).length
    d = target-h; dist = min(d.length, (l1+l2)*.99999); u = d.normalized()
    pole = knees[side] - (feet[side].translation + rig.pose.bones[th].head)*.5
    pole.z = 0
    if pole.length < .01: pole = Vector((0, -1, 0))
    v = (pole-u*pole.dot(u)).normalized()
    c = max(-1., min(1., (l1*l1+dist*dist-l2*l2)/(2*l1*dist)))
    knee = h + l1*(u*c+v*math.sqrt(max(0., 1-c*c)))
    for bone, child, point in [(th, ca, knee), (ca, ft, h+u*dist)]:
        m = rig.pose.bones[bone].matrix.copy(); origin = m.translation.copy()
        current = rig.pose.bones[child].head-origin
        m = current.rotation_difference(point-origin).to_matrix().to_4x4() @ m
        m.translation = origin; world(bone, m)
    m = rotation.to_4x4(); m.translation = rig.pose.bones[ft].head; world(ft, m)
    return max(0., d.length-(l1+l2))

attach(bpy.data.actions['Attack']); original = []
for f in range(82):
    scene.frame_set(f); original.append(snap())
rows = []; report = []
for f, pose in enumerate(original):
    t = f/30; apply(pose)
    before_cloth = coords()[cloth]
    delta = Vector(tuple(fn(t) for fn in hip)); step = foot_plan(t)
    pelvis = rig.pose.bones['B_Pelvis'].matrix.copy(); pelvis.translation += delta; world('B_Pelvis', pelvis)
    targets = {s: feet[s].translation + (step if s == 'L' else Vector()) for s in 'LR'}
    for iteration in range(3):
        miss = max(leg_ik(s, targets[s], feet[s].to_3x3()) for s in 'LR')
        if miss < .0001: break
        pelvis = rig.pose.bones['B_Pelvis'].matrix.copy(); pelvis.translation.z -= miss+.001
        delta.z -= miss+.001; world('B_Pelvis', pelvis)
    for s in 'LR': rig.pose.bones[f'B_{s}_Toe0'].matrix_basis = ready[f'B_{s}_Toe0']
    bpy.context.view_layer.update()
    # Preserve the existing cloth surface and fit its broad displacement with the existing robe controls.
    displacement = waist[:, None]*np.array(delta)[None, :]
    hem_motion = np.array(step); hem_motion[2] *= .25
    displacement += ((1-waist)*foot_follow)[:, None]*hem_motion[None, :]
    # Keep the rear hem over the planted leg as the front of the robe follows the step.
    widen = ease(t/.30)*ease((2.7-t)/.30)
    radial = before_cloth[:, :2].copy()
    radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-6)
    displacement[:, :2] += radial * (.025*widen*(1-height**3))[:, None]
    target_cloth = before_cloth + displacement
    target_cloth[:, 2] = np.maximum(target_cloth[:, 2], .008)
    for iteration in range(2):
        offsets = pinv @ (target_cloth-coords()[cloth])
        matrices = {n: rig.pose.bones[n].matrix.copy() for n in cloth_bones}
        for i, n in enumerate(cloth_bones):
            m = matrices[n]; m.translation += Vector(offsets[i]); world(n, m)
    row = snap()
    if f in [0, 81]: row = original[f]
    rows.append(row)
    current = coords(); floor = {s: float(current[foot_masks[s], 2].min()) for s in 'LR'}
    report.append({'frame': f, 'hip_offset_m': list(delta), 'left_step_m': list(step), 'sole_m': floor,
                   'cloth_fit_error_m': float(np.linalg.norm(current[cloth]-target_cloth, axis=1).max())})
    if f in [0, 20, 30, 36, 48, 65, 81]: print('STEP', report[-1], flush=True)

changed = ['B_Pelvis'] + [f'B_{s}_{part}' for s in 'LR' for part in ['Thigh', 'Calf', 'Foot', 'Toe0']] + cloth_bones
for role in ['Attack', 'Cast']:
    action = bpy.data.actions[role]; attach(action); previous = {}
    for f, row in enumerate(rows):
        for n in changed:
            pb = rig.pose.bones[n]; m = row[n]; q = m.to_quaternion()
            if n in previous and q.dot(previous[n]) < 0: q = -q
            previous[n] = q; pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=f)
            if n == 'B_Pelvis' or n.startswith('Robe_'):
                pb.location = m.translation; pb.keyframe_insert('location', frame=f)
    for layer in action.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points: key.interpolation = 'LINEAR'
attach(None)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cast_step.blend'))
(p/'review/cast_step/fit.json').write_text(json.dumps(report, indent=2)+'\n')
assert max(r['left_step_m'][1] for r in report) <= 1e-6
assert min(r['left_step_m'][1] for r in report) < -.19
common.workbench_clay(scene); attach(bpy.data.actions['Attack'])
for f in [0, 20, 27, 36, 48, 65, 81]:
    scene.frame_set(f)
    common.render_views(str(p/f'review/cast_step/pose_{f:02d}'), .9, 2.7,
                        views=('front', 'left', 'three_quarter'), resolution=(440, 560))
