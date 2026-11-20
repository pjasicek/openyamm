"""Heavy anticipation, unchanged strike speed, measured club impact and native-compatible clip joins."""
import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_cloth_rig.blend'))
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
# Palm travel, not an arbitrary timeline fraction, establishes release in the source casting clip.
a=bpy.data.actions['Attack'];pts=[]
for f in range(int(a.frame_range[1])+1):
 set_act(a);scene.frame_set(f);pts.append(np.mean([np.array(rig.pose.bones[f'B_{s}_Hand'].head) for s in 'LR'],axis=0))
pts=np.array(pts);speed=-np.diff(pts[:,1])*30;speed[:3]=0;release=int(np.argmax(speed))+1
extra=max(0,30-release);lead_end=max(1,release-3)
report={'source_release_frame':release,'anticipation_added_frames':extra,'source_fps':30,'native_attack_s':1.,'clips':{}}
for name in ['Attack','Cast','Hit','Death']:
 a=bpy.data.actions[name];n=int(a.frame_range[1]);out=[]
 if name in ['Attack','Cast']:
  for f in range(n+extra+1):
   sf=f*lead_end/(lead_end+extra) if f<=lead_end+extra else f-extra
   pose=sample(a,sf);w=min(smooth(f/5),smooth((n+extra-f)/6));out.append(blend(ST,pose,w))
  report['attack_impact_s']=(release+extra)/30
 else:
  for f in range(n+1):
   w=smooth(f/4)
   if name=='Hit':w=min(w,smooth((n-f)/4))
   out.append(blend(ST,sample(a,f),w))
 write(name,out)
# A floor-length robe needs short strides; keep the source cadence and upper-body action.
for name,amount in [('Walking',.45),('Running',.35)]:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
 for pose in poses:
  for n in names:
   if any(x in n for x in ['Thigh','Calf','Foot','Toe']):pose[n]=(ST[n][0].slerp(pose[n][0],amount),pose[n][1])
 write(name,poses)
# Keep the two concealed legs together through the backward fall, as in the native robed corpse.
a=bpy.data.actions['Death'];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
for f,pose in enumerate(poses):
 set_act(a);scene.frame_set(f)
 for part in ['Thigh','Calf','Foot','Toe0']:
  left,right=[f'B_{s}_{part}' for s in 'LR'];bL,bR=rig.data.bones[left],rig.data.bones[right]
  dL=(rig.pose.bones[left].matrix.to_3x3()@bL.matrix_local.to_3x3().inverted()).to_quaternion()
  dR=(rig.pose.bones[right].matrix.to_3x3()@bR.matrix_local.to_3x3().inverted()).to_quaternion()
  avg=dL.slerp(dR,.5)
  # Store target world rotations, then solve local rotations in hierarchy order below.
  pose.setdefault('_leg_world',{})[left]=avg.to_matrix()@bL.matrix_local.to_3x3()
  pose['_leg_world'][right]=avg.to_matrix()@bR.matrix_local.to_3x3()
 world=pose.pop('_leg_world');set_act(None)
 for n,(q,l) in pose.items():rig.pose.bones[n].rotation_quaternion=q;rig.pose.bones[n].location=l
 bpy.context.view_layer.update()
 for n in names:
  if n in world:
   b=rig.pose.bones[n];m=world[n].to_4x4();m.translation=b.head;b.matrix=m;bpy.context.view_layer.update();pose[n]=(b.rotation_quaternion.copy(),b.location.copy())
write('Death',poses)
# Contact comes from the concealed shoes and solid body; unbaked garments do not set root height.
pv=np.array([a.value for a in body.data.attributes['piece'].data]);co=np.array([tuple(v.co) for v in body.data.vertices]);vg=[g.name for g in body.vertex_groups]
feet=(pv==12)&np.array([sum(e.weight for e in v.groups if 'Foot' in vg[e.group] or 'Toe' in vg[e.group])>.5 for v in body.data.vertices])
solid=np.isin(pv,[2,3,4,8,9,10,11,12])|((pv==0)&(co[:,2]>1.075)&(abs(co[:,0])<.19))
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:
 a=bpy.data.actions[name];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];low=[]
 for f in range(len(poses)):
  set_act(a);scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();z=np.array([v.co.z for v in m.vertices]);ev.to_mesh_clear();low.append(float(z[solid if name=='Death' else feet].min()))
 offsets=np.array(low)
 if name=='Running':offsets-=np.clip(offsets-np.quantile(offsets,.25),0,.06)
 for f,pose in enumerate(poses):
  set_act(a);scene.frame_set(f);b=rig.pose.bones['B_Pelvis'];M=b.matrix.copy();M.translation.z-=float(offsets[f]);b.matrix=M;pose['B_Pelvis']=(b.rotation_quaternion.copy(),b.location.copy())
 write(name,poses);report['clips'][name]={'duration_s':(len(poses)-1)/30,'floor_offset_cm':[round(float(offsets.min())*100,2),round(float(offsets.max())*100,2)]}
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
assert .8<=report['attack_impact_s']<=1.2
(p/'work/clip_timing.json').write_text(json.dumps(report,indent=2)+'\n');print('TIMING',report)
set_act(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_grounded.blend'))
