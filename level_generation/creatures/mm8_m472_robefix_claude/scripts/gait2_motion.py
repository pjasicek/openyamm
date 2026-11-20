"""gait2 (2026-10-21), body motion of the new walk and run: work/rig_textured_uv.blend (the fitted animation/UV master)
-> work/gait2_motion.blend with two new actions; every existing action is left as it is.
  Walk2 <- Mixamo "Walking (10)", Run2 <- Mixamo "Running (4)" (chosen by their measured stride on this body, G1 in
  README: the installed Walking slerps the legs 45 % toward Standing and has no planted phase).
Steps: retarget (gait2_retarget_mixamo.py) -> exact loop (last key = first) -> floor pass -> constant foot tilt levelled
(gait2_foot_level.py :const, keeps heel strike and toe-off) -> robe fit of stride, lift and timing (gait2_fit.py) -> floor pass on the lowest shoe point per frame (run: up
to 6 cm of flight kept, as time_and_ground.py) -> twist bake (twist_bones.py rule, FA 0.6) -> linear keys.
The robe, cuffs, hair and tassels are simulated next by garment_sim.py (gait2_cloth.py)."""
from pathlib import Path
import runpy, sys, math
import os
p = Path(__file__).resolve().parents[1]; lib = p.parents[2] / 'anim_library/mixamo'; W0 = p / 'work'
# robefix (2026-11-12): Run2 only; every output of one candidate goes to work/<RF_TAG>/
W = W0 / os.environ.get('RF_TAG', 'cand'); W.mkdir(parents=True, exist_ok=True)
CLIPS = {'Run2': 'Running (4)'}


def run(name, *args):
    s = p / 'scripts' / name; sys.argv = [str(s), '--', *map(str, args)]; runpy.run_path(str(s), run_name='__main__')


run('gait2_retarget_mixamo.py', W0 / 'rig_textured_uv.blend', W / 'gait2_retarget.blend',
    *[f'{lib}/{f}.fbx:{n}' for n, f in CLIPS.items()])

import bpy
import numpy as np
from mathutils import Vector, Quaternion


def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


def fcurves(a):
    return [fc for layer in a.layers for strip in layer.strips for cb in strip.channelbags for fc in cb.fcurves]


def open_blend(path):
    global rig, body, sc, feet
    bpy.ops.wm.open_mainfile(filepath=str(path))
    rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; sc = bpy.context.scene; sc.render.fps = 30
    pv = np.array([a.value for a in body.data.attributes['piece'].data]); vg = [g.name for g in body.vertex_groups]
    feet = (pv == 12) & np.array([sum(e.weight for e in v.groups if 'Foot' in vg[e.group] or 'Toe' in vg[e.group]) > .5
                                  for v in body.data.vertices])


def ground(name):
    act = bpy.data.actions[name]; set_act(act); end = int(act.frame_range[1]); lows = []
    for f in range(end + 1):
        sc.frame_set(f); ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
        z = np.array([v.co.z for v in m.vertices]); ev.to_mesh_clear(); lows.append(float(z[feet].min()))
    off = np.array(lows)
    if name.startswith('Run'): off -= np.clip(off - np.quantile(off, .25), 0, .06)
    for f in range(end + 1):
        sc.frame_set(f); b = rig.pose.bones['B_Pelvis']; M = b.matrix.copy(); M.translation.z -= float(off[f]); b.matrix = M
        b.keyframe_insert('location', frame=f)
    return off


# exact loop (the Mixamo cycle's last key repeats its first within a few tenths of a degree), then a first floor pass so
# the constant foot tilt is measured on grounded soles
open_blend(W / 'gait2_retarget.blend')
for name in CLIPS:
    for fc in fcurves(bpy.data.actions[name]):
        k = fc.keyframe_points
        if len(k) > 1: k[-1].co[1] = k[0].co[1]
    ground(name)
set_act(None)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'gait2_grounded0.blend'))
run('gait2_foot_level.py', W / 'gait2_grounded0.blend', W / 'gait2_feet.blend', *[f'{n}:const' for n in CLIPS])
run('gait2_fit.py', W / 'gait2_feet.blend', W / 'gait2_fit.blend')
open_blend(W / 'gait2_fit.blend')
FA, UA = 0.6, 0.5


def twist_about(q, axis):
    v = Vector((q.x, q.y, q.z)); a = 2 * math.atan2(v.dot(axis), q.w)
    return (a + math.pi) % (2 * math.pi) - math.pi


for name in CLIPS:
    off = ground(name); act = bpy.data.actions[name]; set_act(act); end = int(act.frame_range[1])
    # twist bones (twist_bones.py bake_twist, the production FA 0.6 / UA 0.5)
    for f in range(end + 1):
        sc.frame_set(f)
        for s in 'LR':
            fb, hb = rig.data.bones[f'B_{s}_Forearm'], rig.data.bones[f'B_{s}_Hand']
            seg = (fb.matrix_local.inverted() @ hb.head_local).normalized()
            rel = (rig.pose.bones[f'B_{s}_Forearm'].matrix.inverted() @ rig.pose.bones[f'B_{s}_Hand'].matrix).to_quaternion()
            dq = rel @ (fb.matrix_local.inverted() @ hb.matrix_local).to_quaternion().inverted()
            pb = rig.pose.bones[f'B_{s}_ForearmTwist']; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion(seg, twist_about(dq, seg) * FA); pb.keyframe_insert('rotation_quaternion', frame=f)
            ub = rig.data.bones[f'B_{s}_UpperArm']
            useg = (ub.matrix_local.inverted() @ rig.data.bones[f'B_{s}_Forearm'].head_local).normalized()
            uq = rig.pose.bones[f'B_{s}_UpperArm'].matrix_basis.to_quaternion()
            pb = rig.pose.bones[f'B_{s}_UpperArmTwist']; pb.rotation_mode = 'QUATERNION'
            pb.rotation_quaternion = Quaternion(useg, -UA * twist_about(uq, useg)); pb.keyframe_insert('rotation_quaternion', frame=f)
    for fc in fcurves(act):
        for k in fc.keyframe_points: k.interpolation = 'LINEAR'
    print('GAIT2_MOTION', name, 'frames', end + 1, 'floor offset cm', round(off.min() * 100, 2), round(off.max() * 100, 2))
set_act(None)
for b in rig.pose.bones: b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'gait2_motion.blend'))
