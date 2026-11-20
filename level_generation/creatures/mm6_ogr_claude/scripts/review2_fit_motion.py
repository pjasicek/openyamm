"""Proportion fitting only: library head/arm clearance, planted soles, and cloth following the retained source motion."""
from pathlib import Path
import bpy,sys,ast,math,json,numpy as np
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
from g6_head_clearance import Clearance
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9h.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones];W_=rig.matrix_world
# Existing proportion-clearance fitter; no authored stance, fidget, or death keyframes are executed.
tree=ast.parse((p/'scripts/author_clips.py').read_text());want={'set_act','sample','write','turn_world','head_fix'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in want],type_ignores=[]),'clearance_fit','exec'),globals())
# Fit the new skull pivot to the cranial base without altering its rest appearance.
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
# Original source-frame head pivot preserves the retained Attack/Hit fit.
bpy.ops.object.mode_set(mode='OBJECT');CL=Clearance(body)
act=bpy.data.actions['Death'];poses=[sample(act,f) for f in range(int(act.frame_range[1])+1)];set_act(None)
def pose_at(pose):
 for n,(q,l) in pose.items():
  pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.location=l
 bpy.context.view_layer.update()
def fitted(pose,degrees):
 pose_at(pose);lat=(rig.pose.bones['B_L_UpperArm'].head-rig.pose.bones['B_R_UpperArm'].head).normalized()
 turn_world('B_Neck',lat,math.radians(degrees*.5));turn_world('B_Head',lat,math.radians(degrees*.5))
probes=[]
for degrees in sorted(range(-30,31,5),key=abs):
 worst=0
 for pose in poses:
  fitted(pose,degrees);worst=max(worst,CL.measure()[0])
 probes.append((degrees,worst));print('DEATH_FIT_PROBE',degrees,worst,flush=True)
 if worst<.01:break
best=min(probes,key=lambda row:(row[1]>.01,abs(row[0]) if row[1]<.01 else row[1]))
assert best[1]<.01,probes
out=[]
for pose in poses:
 fitted(pose,best[0]);out.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in names})
write('Death',out);print('DEATH_FIT_SELECTED',best)

# Attach the rear panel to its existing cloth hinge; formerly it was split between the thighs.
ids=[v.index for v in body.data.vertices if body.data.attributes['piece'].data[v.index].value==14]
for g in body.vertex_groups:g.remove(ids)
(body.vertex_groups.get('LoinBack') or body.vertex_groups.new(name='LoinBack')).add(ids,1,'REPLACE')
# Refit the existing cloth hinges to each source pose, including the new death source.
set_act(None);pelrest=rig.data.bones['B_Pelvis'].matrix_local
axes={n:(rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0))).normalized() for n in ['LoinFront','LoinBack']}
restangles={}
for side in 'LR':
 d=rig.data.bones[f'B_{side}_Calf'].head_local-rig.data.bones[f'B_{side}_Thigh'].head_local;restangles[side]=math.atan2(-d.y,-d.z)
for act in [a for a in bpy.data.actions if a.use_fake_user]:
 set_act(act)
 for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
  scene.frame_set(f);undo=(rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()).inverted().to_3x3();angles=[]
  for side in 'LR':
   d=undo@(rig.pose.bones[f'B_{side}_Calf'].head-rig.pose.bones[f'B_{side}_Thigh'].head);angles.append(math.atan2(-d.y,-d.z)-restangles[side])
  for bn,angle in [('LoinFront',-max(0,*angles)*1.12-math.radians(12)),('LoinBack',-min(0,*angles)*1.12+math.radians(12))]:
   pb=rig.pose.bones[bn];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(axes[bn],angle);pb.keyframe_insert('rotation_quaternion',frame=f)
# Preserve airborne run phases; lift only the low part of the source root trajectory above the fitted soles.
report={}
for name in ['Standing','Running','Fidget','Death']:
 act=bpy.data.actions[name];set_act(act);n=int(act.frame_range[1]);poses=[sample(act,f) for f in range(n+1)];low=[]
 for f in range(n+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low.append(min(v.co.z for v in me.vertices));ev.to_mesh_clear()
 shifts=np.maximum(0,-np.array(low))
 if name=='Standing':shifts[:]=shifts.max()
 else:
  # Hold over neighbours before smoothing so the filtered lift never permits floor penetration.
  held=np.array([shifts[max(0,i-1):i+2].max() for i in range(len(shifts))]);k=np.array([1,2,1])/4;shifts=np.maximum(shifts,np.convolve(np.pad(held,1,mode='edge'),k,mode='valid'))
 if name in ['Standing','Running']:shifts[0]=shifts[-1]=max(shifts[0],shifts[-1])
 set_act(None)
 for f,pose in enumerate(poses):
  for bn,(q,l) in pose.items():
   pb=rig.pose.bones[bn];pb.rotation_quaternion=q;pb.location=l
  bpy.context.view_layer.update();root=rig.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=float(shifts[f]);root.matrix=m;bpy.context.view_layer.update()
  poses[f]={bn:(rig.pose.bones[bn].rotation_quaternion.copy(),rig.pose.bones[bn].location.copy()) for bn in names}
 write(name,poses);report[name]={'root_floor_lift_max_m':float(shifts.max()),'raw_min_z':float(min(low))}
# Keep the death endpoint exactly as the settled library pose.
write('Dead',[sample(bpy.data.actions['Death'],int(bpy.data.actions['Death'].frame_range[1]))]*31)
# Recompute fitted twist channels after clavicle compensation.
FA=.5;UA=.5;tree=ast.parse((p/'scripts/twist_bones.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist_bake','exec'),globals())
for name in ['Standing','Running','Fidget','Death','Dead']:bake_twist(bpy.data.actions[name])
set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
(p/'revision_02/motion/proportion_fit.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v10.blend'));print('PROPORTION_FIT',report)
