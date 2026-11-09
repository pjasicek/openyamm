"""Heavy anticipation, unchanged strike speed, measured club impact and native-compatible clip joins."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_fitted.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones];body=bpy.data.objects['Body']
def set_act(a):
    rig.animation_data_create(); rig.animation_data.action = a
    if a is not None and len(a.slots): rig.animation_data.action_slot = a.slots[0]


def sample(act, f):
    set_act(act); scene.frame_set(int(f), subframe=f - int(f))
    return {n: (rig.pose.bones[n].rotation_quaternion.copy(), rig.pose.bones[n].location.copy()) for n in names}


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


def write(name, frames):
    old = bpy.data.actions.get(name)
    if old: bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name); act.use_fake_user = True; set_act(act); prev = {}
    for i, pose in enumerate(frames):
        for n, (q, l) in pose.items():
            pb = rig.pose.bones[n]; pb.rotation_mode = 'QUATERNION'
            if n in prev and q.dot(prev[n]) < 0: q = -q
            prev[n] = q; pb.rotation_quaternion = q; pb.location = l
            pb.keyframe_insert('rotation_quaternion', frame=i)
            if n == 'B_Pelvis': pb.keyframe_insert('location', frame=i)
    act.use_frame_range = True; act.frame_start, act.frame_end = 0, len(frames) - 1
    set_act(None); return act


def blend(a, b, w):
    return {k: ((a[k][0] if a[k][0].dot(b[k][0]) >= 0 else -a[k][0]).slerp(b[k][0], w), a[k][1].lerp(b[k][1], w)) for k in a}



ST=sample(bpy.data.actions['Standing'],0)
# The compact source has a 0.23 s lift. Give this heavy club a 0.83 s anticipation,
# retaining the source's downward strike and recovery at their original speed.
a=bpy.data.actions['Attack'];n=int(a.frame_range[1]);poses=[]
for f in range(n+18+1):
 sf=f*7/25 if f<=25 else f-18
 poses.append(sample(a,sf))
write('Attack',poses)
for name,fi,fo in [('Hit',.10,.12),('Fidget',.20,.20),('Death',.20,0)]:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];res=[]
 for f,pose in enumerate(poses):
  w=smooth(f/(fi*30)) if fi else 1
  if fo:w=min(w,smooth((len(poses)-1-f)/(fo*30)))
  res.append(blend(ST,pose,w))
 write(name,res)
# Re-ground blended one-shots; preserve the authored fall once the body reaches the ground.
vg=[g.name for g in body.vertex_groups];feet=np.array([sum(e.weight for e in v.groups if 'Foot' in vg[e.group] or 'Toe' in vg[e.group])>.5 for v in body.data.vertices])
for name in ['Hit','Fidget','Death']:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
 for f,pose in enumerate(poses):
  set_act(a);scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([(body.matrix_world@v.co).z for v in m.vertices]);ev.to_mesh_clear()
  low=z.min() if name=='Death' else z[feet].min();M=rig.pose.bones['B_Pelvis'].matrix.copy();M.translation.z-=float(low);rig.pose.bones['B_Pelvis'].matrix=M
  pose['B_Pelvis']=(rig.pose.bones['B_Pelvis'].rotation_quaternion.copy(),rig.pose.bones['B_Pelvis'].location.copy())
 write(name,poses)
G=json.loads((p/'work/grip_pose.json').read_text());a=bpy.data.actions['Attack'];set_act(a);points=[]
for f in range(int(a.frame_range[1])+1):
 scene.frame_set(f);M=rig.pose.bones['B_L_Hand'].matrix;c=M@Vector(G['handle_centre_hand_local']);axis=(M.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();points.append(np.array(c+axis*.52))
points=np.array(points);v=np.diff(points,axis=0)*30
candidate=(v[:,1]<0)&(points[:-1,2]>.45)&(np.arange(len(v))>=25)
speed=np.linalg.norm(v,axis=1);speed[~candidate]=0;k=int(np.argmax(speed));impact=(k+.5)/30
assert .8<=impact<=1.2,impact
report={'attack_impact_s':impact,'attack_peak_strike_speed_m_s':float(speed[k]),'attack_duration_s':a.frame_range[1]/30,'attack_anticipation_s':25/30,'native_attack_s':1.,'note':'Only the lift was authored longer; source strike and follow-through rate retained.','clip_durations':{a.name:a.frame_range[1]/30 for a in bpy.data.actions}}
(p/'work/clip_timing.json').write_text(json.dumps(report,indent=2));print('TIMING',report)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
set_act(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v5.blend'))
