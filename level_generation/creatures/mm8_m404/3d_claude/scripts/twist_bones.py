"""Twist distribution (G1 measured: the source forearm never twists, the hand carries up to 108 deg of roll; the upper
arm rolls up to 107 deg).
Adds per side:
- B_{s}_ForearmTwist (child of B_{s}_Forearm, head at 60 % of the forearm, same frame): its pose = a rotation about
  the forearm axis by 0.6 x the hand's twist relative to the forearm;
- B_{s}_UpperArmTwist (child of B_{s}_UpperArm, head at 25 % of the upper arm): rotation about the upper-arm axis by
  -0.5 x the upper arm's own twist relative to its parent (the skin next to the shoulder rolls half as much).
Weights: forearm skin ramps from B_Forearm to B_ForearmTwist between 15 % and 85 % of the forearm (the wrist band and
the hand stay as they are); upper-arm skin ramps from B_UpperArmTwist (shoulder end) to B_UpperArm between 0 % and
30 % - the transition must not pass under a rigid ring (the armlet sits at 32-51 %). The twist poses are baked per frame into every action (bake_twist()).
Order: build_rig -> retarget -> twist_bones -> weights_fix (accessories copy the final skin weights).
Args: -- <in blend> <out blend>"""
import bpy, sys, os, math
import numpy as np
from mathutils import Vector, Quaternion, Matrix
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
# goblin: the iron bracer covers the forearm from ~10 % to past the wrist, so the forearm twist cannot ramp along the
# forearm (bar1: 15-85 %): the transition sits in the elbow band above the bracer and the hand roll is split evenly
# between that band and the wrist (FA 0.5); the bracer rides rigidly on the twist bone (weights_fix.py)
FA = float(os.environ.get('FA', '0.5')); HA, UA = 0.6, 0.5
FA_RAMP = tuple(float(x) for x in os.environ.get('FA_RAMP', '0.0,0.12').split(','))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones
for s in ('L', 'R'):
    for base, child, t, name in (('Forearm', 'Hand', HA, 'ForearmTwist'), ('UpperArm', 'Forearm', 0.25, 'UpperArmTwist')):
        b = eb[f'B_{s}_{base}']; c = eb[f'B_{s}_{child}']
        n = eb.get(f'B_{s}_{name}') or eb.new(f'B_{s}_{name}')
        p = b.head + (c.head - b.head) * t
        n.head = p; n.tail = p + (b.tail - b.head) * 0.5; n.roll = b.roll
        n.parent = b; n.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
co = np.array([tuple(body.matrix_world @ v.co) for v in me.vertices])
gi = {g.name: g for g in body.vertex_groups}


def weights(name):
    g = gi[name]; w = np.zeros(len(co))
    for v in me.vertices:
        for e in v.groups:
            if e.group == g.index:
                w[v.index] = e.weight
    return w


for s in ('L', 'R'):
    for base, child, a0, a1, name, toward_child in (('Forearm', 'Hand', FA_RAMP[0], FA_RAMP[1], 'ForearmTwist', True),
                                                     ('UpperArm', 'Forearm', 0.0, 0.60, 'UpperArmTwist', False)):   # under the pauldron (t 0-0.5)
        h = np.array(rig.data.bones[f'B_{s}_{base}'].head_local); c = np.array(rig.data.bones[f'B_{s}_{child}'].head_local)
        L = np.linalg.norm(c - h); d = (c - h) / L
        t = (co - h) @ d / L
        w = weights(f'B_{s}_{base}')
        ramp = np.clip((t - a0) / (a1 - a0), 0, 1)
        share = ramp if toward_child else 1 - ramp
        moved = w * share
        tg = gi.get(f'B_{s}_{name}') or body.vertex_groups.new(name=f'B_{s}_{name}'); gi[tg.name] = tg
        for i in np.nonzero(moved > 1e-4)[0]:
            tg.add([int(i)], float(moved[i]), 'REPLACE')
            gi[f'B_{s}_{base}'].add([int(i)], float(w[i] - moved[i]), 'REPLACE')
        print('TWIST', s, name, 'vertices', int((moved > 1e-4).sum()))


def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); a = 2 * math.atan2(v.dot(axis), q.w)
    return (a + math.pi) % (2 * math.pi) - math.pi


def bake_twist(act):
    rig.animation_data.action = act
    if getattr(act, 'slots', None) is not None and len(act.slots):
        rig.animation_data.action_slot = act.slots[0]
    f0, f1 = (int(x) for x in act.frame_range)
    previous={}
    for f in np.arange(f0, f1 + .01, .25):
        bpy.context.scene.frame_set(int(f),subframe=float(f%1))
        for s in ('L', 'R'):
            # forearm twist: the hand's rotation relative to the forearm, twist part about the forearm axis (Y of the
            # twist bone = forearm frame, so local Y is not the segment; use the segment in the forearm's local frame)
            fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
            seg_local = (fb.matrix_local.inverted() @ hb.head_local).normalized()
            rel = (rig.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion()
            rest_rel = (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion()
            dq = rel @ rest_rel.inverted()
            angle=twist_about(dq,seg_local);key=s+'forearm'
            if key in previous:angle=previous[key]+(angle-previous[key]+math.pi)%(2*math.pi)-math.pi
            previous[key]=angle;tw=angle*FA
            p = rig.pose.bones[f'B_{s}_ForearmTwist']; p.rotation_mode = 'QUATERNION'
            p.rotation_quaternion = Quaternion(seg_local, tw)
            p.keyframe_insert('rotation_quaternion', frame=f)
            # upper arm counter twist near the shoulder
            ub = rig.data.bones[f'B_{s}_UpperArm']
            useg = (ub.matrix_local.inverted() @ rig.data.bones[f'B_{s}_Forearm'].head_local).normalized()
            uq = rig.pose.bones[f'B_{s}_UpperArm'].matrix_basis.to_quaternion()
            p = rig.pose.bones[f'B_{s}_UpperArmTwist']; p.rotation_mode = 'QUATERNION'
            angle=twist_about(uq,useg);key=s+'upper'
            if key in previous:angle=previous[key]+(angle-previous[key]+math.pi)%(2*math.pi)-math.pi
            previous[key]=angle;p.rotation_quaternion=Quaternion(useg,-UA*angle)
            p.keyframe_insert('rotation_quaternion', frame=f)
    rig.animation_data.action = None


for act in [a for a in bpy.data.actions if a.use_fake_user]:
    bake_twist(act)
    print('BAKED twist', act.name)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
