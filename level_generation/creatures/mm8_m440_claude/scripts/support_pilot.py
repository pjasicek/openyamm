"""Ground the source motion and plant the ready stance with unchanged leg lengths."""
from pathlib import Path
import bpy,sys,numpy as np,math
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot_carried.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
parts=np.array([a.value for a in body.data.attributes['piece'].data]);feet={s:np.flatnonzero(parts==part) for s,part in [('L',4),('R',5)]}
# Bare feet end below the ankle: calf weights and inherited toe curls lifted their soles.
for side,ids in feet.items():
 for group in body.vertex_groups:group.remove(ids.tolist())
 for i in ids:
  toe=float(np.clip((-.04-body.data.vertices[int(i)].co.y)/.10,0,1))
  body.vertex_groups[f'B_{side}_Foot'].add([int(i)],1-toe,'REPLACE')
  body.vertex_groups[f'B_{side}_Toe0'].add([int(i)],toe,'REPLACE')
def action(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
def coords():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return co
rest=np.array([tuple(v.co) for v in body.data.vertices]);sole_ids={s:ix[rest[ix,2]<rest[ix,2].min()+.005] for s,ix in feet.items()}
def leg(side,target):
 ua,fa,hd=[f'B_{side}_{x}' for x in ('Thigh','Calf','Foot')];Mu,Mf,Mh=[armik.W(rig,n) for n in (ua,fa,hd)];S,E,W=[m.translation.copy() for m in (Mu,Mf,Mh)]
 L1,L2=(E-S).length,(W-E).length;d=target-S;dist=min(d.length,(L1+L2)*.998);u=d.normalized();r=(W-S).normalized();pole=E-S-r*(E-S).dot(r);pole=r.rotation_difference(u)@pole;v=(pole-u*pole.dot(u)).normalized();ca=np.clip((L1*L1+dist*dist-L2*L2)/(2*L1*dist),-1,1);K=S+L1*(u*ca+v*math.sqrt(max(0,1-ca*ca)))
 q=(E-S).normalized().rotation_difference((K-S).normalized());armik.set_world(rig,ua,armik.rot_world(Mu,q.to_matrix()@Mu.to_3x3()))
 F=armik.W(rig,fa);q=(armik.W(rig,hd).translation-F.translation).normalized().rotation_difference((target-F.translation).normalized());armik.set_world(rig,fa,armik.rot_world(F,q.to_matrix()@F.to_3x3()))
 armik.set_world(rig,hd,armik.rot_world(armik.W(rig,hd),Mh.to_3x3()))
for name in ('Standing','Walking','Attack'):
 a=bpy.data.actions[name];frames=[];lift_peaks={}
 if name=='Walking':
  lifts={s:[] for s in 'LR'}
  for f in range(int(a.frame_range[1])+1):
   action(a);sc.frame_set(f);co=coords();lo={s:float(co[ix,2].min()) for s,ix in feet.items()};base=min(lo.values())
   for side in 'LR':lifts[side].append(lo[side]-base)
  lift_peaks={s:max(v) for s,v in lifts.items()}
 for f in range(int(a.frame_range[1])+1):
  action(a);sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};action(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  for side in 'LR':rig.pose.bones[f'B_{side}_Toe0'].matrix_basis=Matrix()
  co=coords();low=min(co[ix,2].min() for ix in feet.values());M=armik.W(rig,'B_Pelvis');M.translation.z-=float(low);armik.set_world(rig,'B_Pelvis',M)
  if name in ('Standing','Walking'):
   for side in 'LR':
    # Level the sole plane in both axes, then hold each foot at its first-frame position.
    co=coords();ix=feet[side];sole=co[sole_ids[side]]
    F=armik.W(rig,f'B_{side}_Foot')
    if name=='Standing':
     normal=Vector(np.linalg.svd(sole-sole.mean(0))[2][-1]);normal=normal if normal.z>0 else -normal;q=normal.rotation_difference(Vector((0,0,1)));armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,q.to_matrix()@F.to_3x3()))
    co=coords();rs=rest[sole_ids[side],1];heel=co[sole_ids[side][rs>=np.quantile(rs,.7)]].mean(0);toe=co[sole_ids[side][rs<=np.quantile(rs,.3)]].mean(0);d=toe-heel;yaw=math.atan2(d[0],-d[1]);want=math.radians(8 if side=='L' else -8)
    F=armik.W(rig,f'B_{side}_Foot');armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,Matrix.Rotation(want-yaw,3,'Z')@F.to_3x3()))
    co=coords();F=armik.W(rig,f'B_{side}_Foot');target=F.translation.copy()
    if name=='Standing':target.z-=float(co[ix,2].min())
    else:
     lift=max(0,float(co[ix,2].min()));peak=lift_peaks[side];target.z+=max(0,.09-peak)*min(1,lift/max(peak,1e-6))**1.5
    leg(side,target)
  # Leave 2 mm for linear interpolation between the 30 Hz support samples.
  M=armik.W(rig,'B_Pelvis');M.translation.z+=.002;armik.set_world(rig,'B_Pelvis',M)
  frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 action(a)
 for f,snap in enumerate(frames):
  for n,m in snap.items():
   b=rig.pose.bones[n];b.matrix_basis=m;b.keyframe_insert('rotation_quaternion',frame=f)
   if n=='B_Pelvis':b.keyframe_insert('location',frame=f)
 print('SUPPORTED',name,flush=True)
action(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/pilot_supported.blend'))
