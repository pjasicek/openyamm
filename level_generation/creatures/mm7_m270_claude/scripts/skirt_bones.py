"""Skirt bones for the m430 robe (first build: in the death the pelvis share of the skirt held the hem as a stiff cone,
so the lying corpse rested on a bell 0.75 m high and the floor pass lifted the body by that much).
Adds B_Skirt0..7 (children of B_Pelvis) radiating at 45-degree steps around the body axis: head on the robe at hip
height, tail at the hem. Every skirt vertex (robe below the hip joints, the inner hem) moves its PELVIS share onto the
two skirt bones nearest its angle (linear by angle); its leg share stays. At rest the bones carry the pelvis exactly,
so every clip deforms as before. In Death the bones fold the hem toward the legs as the body tilts: per frame the
target direction of each bone is from its head to the ankles' midpoint, 6 cm toward the floor, the fold factor is
the body's tilt (pelvis up-axis from vertical) mapped 15..70 degrees -> 0..1, smoothed. The lying robe then wraps the
legs and hangs to the floor instead of standing up as a bell. Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Matrix, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data; sc = bpy.context.scene
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
NB = 8
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices]); nv = len(co)
gv = np.zeros(nv, np.int32); me.attributes['garment'].data.foreach_get('value', gv)
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
pel = rig.data.bones['B_Pelvis']; P0 = np.array(pel.head_local)
zh = rig.data.bones['B_L_Thigh'].head_local.z
skirt = (gv == 3) & (co[:, 2] < zh)                 # m270: the chain skirt piece
# robe radius at hip height and hem height per angle, for the bone heads/tails
ang = np.arctan2(co[:, 0] - P0[0], -(co[:, 1] - P0[1]))           # 0 = front (-Y), positive toward +X (its left)
heads, tails = [], []
for k in range(NB):
    a = 2 * math.pi * k / NB
    d = np.abs((ang - a + math.pi) % (2 * math.pi) - math.pi) < math.pi / NB
    hip = d & (np.abs(co[:, 2] - zh) < 0.04) & (gv == 3)
    hem = d & skirt & (co[:, 2] < 0.12)
    r_hip = np.median(np.hypot(co[hip, 0] - P0[0], co[hip, 1] - P0[1])) if hip.any() else 0.15
    r_hem = np.median(np.hypot(co[hem, 0] - P0[0], co[hem, 1] - P0[1])) if hem.any() else 0.4
    u = Vector((math.sin(a), -math.cos(a), 0))
    heads.append(Vector((P0[0], P0[1], zh)) + u * float(r_hip)); tails.append(Vector((P0[0], P0[1], 0.04)) + u * float(r_hem))
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
for k in range(NB):
    n = f'B_Skirt{k}'
    eb = rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n)
    eb.head = heads[k]; eb.tail = tails[k]; eb.parent = rig.data.edit_bones['B_Pelvis']; eb.use_deform = True
    eb.align_roll(Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')
for k in range(NB):
    if f'B_Skirt{k}' not in body.vertex_groups:
        body.vertex_groups.new(name=f'B_Skirt{k}')
names = [g.name for g in body.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
W = np.zeros((nv, len(names)))
for v in me.vertices:
    for e in v.groups:
        W[v.index, e.group] = e.weight
idx = np.where(skirt)[0]
pw = W[idx, gi['B_Pelvis']].copy()
t = ((ang[idx] % (2 * math.pi)) / (2 * math.pi / NB))
k0 = np.floor(t).astype(int) % NB; k1 = (k0 + 1) % NB; f = t - np.floor(t)
W[idx, gi['B_Pelvis']] = 0
for k in range(NB):
    W[idx, gi[f'B_Skirt{k}']] = pw * ((k0 == k) * (1 - f) + (k1 == k) * f)
for i in idx:
    for j in np.nonzero(W[i] > 1e-4)[0]:
        body.vertex_groups[j].add([int(i)], float(W[i, j]), 'REPLACE')
    for n in ('B_Pelvis',) + tuple(f'B_Skirt{k}' for k in range(NB)):
        if W[i, gi[n]] <= 1e-4:
            body.vertex_groups[n].remove([int(i)])
print('SKIRT bones', NB, 'vertices', len(idx), 'pelvis share moved mean', round(float(pw.mean()), 3))


def set_act(a):
    rig.animation_data.action = a
    if a is not None and len(a.slots):
        rig.animation_data.action_slot = a.slots[0]


# key every action: the skirt bones at rest (identity) except in Death
for act in bpy.data.actions:
    set_act(act); f0, f1 = (int(x) for x in act.frame_range)
    for k in range(NB):
        pb = rig.pose.bones[f'B_Skirt{k}']; pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
        pb.keyframe_insert('rotation_quaternion', frame=f0); pb.keyframe_insert('rotation_quaternion', frame=f1)
pel = rig.data.bones['B_Pelvis']                      # re-fetched: edit mode invalidates the earlier reference
act = bpy.data.actions['Death']; set_act(act); f0, f1 = (int(x) for x in act.frame_range)
fold = []
for fr in range(f0, f1 + 1):
    sc.frame_set(fr)
    Mp = rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix
    up = (Mp.to_3x3() @ (pel.matrix_local.to_3x3().inverted() @ Vector((0, 0, 1)))).normalized()
    tilt = math.degrees(math.acos(max(-1, min(1, up.z))))
    fold.append(min(1.0, max(0.0, (tilt - 15) / 55)))
fold = np.array(fold); gk = np.exp(-0.5 * (np.arange(-4, 5) / 2.0) ** 2); gk /= gk.sum()
fold = np.convolve(np.concatenate([np.repeat(fold[:1], 4), fold, np.repeat(fold[-1:], 4)]), gk, 'valid')
fold = fold * fold * (3 - 2 * fold)
for i, fr in enumerate(range(f0, f1 + 1)):
    sc.frame_set(fr)
    for k in range(NB):
        rig.pose.bones[f'B_Skirt{k}'].rotation_quaternion = Quaternion()
    bpy.context.view_layer.update()
    P = (rig.matrix_world @ rig.pose.bones['B_Pelvis'].matrix).translation
    A = sum(((rig.matrix_world @ rig.pose.bones[f'B_{s}_Foot'].matrix).translation for s in 'LR'), Vector()) / 2
    for k in range(NB):
        pb = rig.pose.bones[f'B_Skirt{k}']
        Mw = rig.matrix_world @ pb.matrix; cur = (Mw.to_3x3() @ Vector((0, 1, 0))).normalized()
        # each bone aims at the ankles, slightly toward the floor: the hem closes around the legs like a shroud (aiming
        # only along the leg direction kept the cone open; its lower half sank under the legs and the floor pass then
        # propped the whole corpse up into a bow)
        tgt = (A + Vector((0, 0, -0.06)) - Mw.translation).normalized()
        q = Quaternion().slerp(cur.rotation_difference(tgt), float(fold[i]))
        R = (q.to_matrix() @ Mw.to_3x3()).to_4x4(); R.translation = Mw.translation
        pb.matrix = rig.matrix_world.inverted() @ R; bpy.context.view_layer.update()
        pb.keyframe_insert('rotation_quaternion', frame=fr)
set_act(None)
print('SKIRT death fold max', round(float(fold.max()), 2), 'from frame', int(np.argmax(fold > 0.05)) if (fold > 0.05).any() else None)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
