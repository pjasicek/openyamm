"""Death ends prone with straight legs (user review 1, image 4: the thighs came through the cloak). The Relax lay-down
ends with the legs bent sideways while the cloak lies straight down the body; the native corpse (dru1dy f) lies prone
under the cloak, legs straight. From frame F0 to F1 every thigh/calf rotation eases (smoothstep) toward the rest basis
(legs along the pelvis axis) by AMOUNT, the feet toward a pointed foot (FOOT_POINT deg plantarflexion, toes back);
held to the end. Then per frame the pelvis is raised so the lowest body vertex (cloak excluded) stays >= 0.
Args: -- <in> <out>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Quaternion, Matrix, Vector  # noqa
src, out = sys.argv[sys.argv.index('--') + 1:]
THIGH_Z = float(os.environ.get("THIGH_Z", "0.10"))
F0, F1, AMOUNT, FOOT_POINT = 24, 46, float(os.environ.get('DEATH_LEGS', '0.85')), 50.0
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
scene = bpy.context.scene
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
act = bpy.data.actions['Death']; rig.animation_data_create(); rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
f0, f1 = (int(x) for x in act.frame_range)
LEG = [f'B_{s}_{b}' for s in 'LR' for b in ('Thigh', 'Calf')]
FOOT = ['B_L_Foot', 'B_R_Foot']


def sm(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# foot: plantarflex about the foot's local X (the bone frames are cloned source frames: measure the sign once)
src_keys = {}
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    src_keys[f] = {n: rig.pose.bones[n].rotation_quaternion.copy() for n in LEG + FOOT}
rig.animation_data.action = None
fb = rig.data.bones['B_L_Foot']; toe = rig.data.bones['B_L_Toe0']
toe_dir = (fb.matrix_local.inverted() @ toe.head_local).normalized()
calf_dir_in_foot = (fb.matrix_local.inverted() @ rig.data.bones['B_L_Calf'].head_local).normalized()
axis = toe_dir.cross(calf_dir_in_foot).normalized()        # rotating toe toward -calf direction = pointing the foot
point = Quaternion(axis, -math.radians(FOOT_POINT))
rig.animation_data.action = act
if len(act.slots):
    rig.animation_data.action_slot = act.slots[0]
def thigh_target(side, f):
    """Local quaternion of the thigh that points it backward along the body and level (dir z = -0.06): the rest basis
    under the pitched pelvis pointed the legs ~25 deg into the floor (the floor lift then lifted her 37 cm)."""
    scene.frame_set(f)
    P = rig.pose.bones['B_Pelvis'].matrix
    tb = rig.data.bones[f'B_{side}_Thigh']; pbm = rig.data.bones['B_Pelvis'].matrix_local
    Mr = P @ (pbm.inverted() @ tb.matrix_local)                       # thigh with the rest basis (armature space)
    d = Mr.to_3x3().col[1].normalized()
    t = Vector((d.x, d.y, 0.0)).normalized(); t.z = THIGH_Z; t.normalize()
    S = d.rotation_difference(t).to_matrix()
    Mt = (S @ Mr.to_3x3()).to_4x4(); Mt.translation = Mr.translation
    rest_rel = pbm.inverted() @ tb.matrix_local
    return (rest_rel.inverted() @ (P.inverted() @ Mt)).to_quaternion()


targets = {f: {s_: thigh_target(s_, f) for s_ in 'LR'} for f in range(f0, f1 + 1) if AMOUNT * sm((f - F0) / (F1 - F0)) > 0}
for f in range(f0, f1 + 1):
    w = AMOUNT * sm((f - F0) / (F1 - F0))
    if w <= 0:
        continue
    for n in LEG:
        tq = targets[f][n[2]] if 'Thigh' in n else Quaternion()
        q = src_keys[f][n]; p = rig.pose.bones[n]; p.rotation_mode = 'QUATERNION'
        if q.dot(tq) < 0:
            tq = -tq
        p.rotation_quaternion = q.slerp(tq, w); p.keyframe_insert('rotation_quaternion', frame=f)
    for n in FOOT:
        q = src_keys[f][n]; p = rig.pose.bones[n]; p.rotation_mode = 'QUATERNION'
        p.rotation_quaternion = q.slerp(point, w); p.keyframe_insert('rotation_quaternion', frame=f)
# floor
pv = np.zeros(len(body.data.vertices), np.int32); body.data.attributes['piece'].data.foreach_get('value', pv)
keep = ~np.isin(pv, (100, 2, 6, 7, 11))   # torso, arms, head: the legs lie under the cloak (the source pose already sank
# the thigh 6 cm into the floor; lifting the whole body for the legs left the hands and chest floating)
pel = rig.pose.bones['B_Pelvis']; lifts = []
for f in range(f0, f1 + 1):
    scene.frame_set(f)
    ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(body.matrix_world @ v.co).z for v in m.vertices])[keep]; ev.to_mesh_clear()
    lift = max(0.0, -z.min())
    lifts.append(lift)
    if lift > 1e-4:
        M = pel.matrix.copy(); M.translation.z += lift
        pel.matrix = M; bpy.context.view_layer.update(); pel.keyframe_insert('location', frame=f)
rig.animation_data.action = None
print('DEATHLEGS legs straightened', AMOUNT, 'frames', F0, '-', F1, 'floor lift cm per 4 frames', [round(x * 100, 1) for x in lifts[::4]])
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
