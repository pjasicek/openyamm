"""Fit elbow planes around the full shell with the hands and weapon fixed in world space."""
import bpy,sys,math,json,runpy
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
src=P/'work/lancer_review2.blend'
for script,args in [('armour_spec_lancer.py',[]),('make_armour.py',[P/'work/lancer_complete.blend',P/'scripts/armour_lancer.json',src]),('skin_shell.py',[src,P/'scripts/armour_lancer.json',src])]:
 sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
sys.argv=['armour_gate.py','--',str(src),'pole_probe',str(P/'scripts/armour_lancer.json')];gate=runpy.run_path(str(P/'scripts/armour_gate.py'),run_name='__main__')
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
clips=['Carbine_Standing','Carbine_Fidget','Carbine_Attack','Lancer_Running','Carbine_Walking','Carbine_Hit','Carbine_Death','Carbine_Dead']
names=[g.name for g in body.vertex_groups];W=np.zeros((len(body.data.vertices),len(names)))
for v in body.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
rest=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
head=W[:,[i for i,n in enumerate(names) if n in ('B_Head','B_Neck','Bone_025','headfront')]].sum(1)>.5
headfaces=[tuple(f.vertices) for f in body.data.polygons if all(head[i] for i in f.vertices)]
arm={};faces={};mask={}
for side in 'RL':
 arm[side]=W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{side}_') and any(t in n for t in ('UpperArm','Forearm'))]].sum(1)>.3
 hand=W[:,[i for i,n in enumerate(names) if n.startswith(f'B_{side}_') and any(t in n for t in ('Hand','Finger'))]].sum(1)>.25
 mask[side]=(arm[side]&~hand)[edges].all(1)
 faces[side]=[tuple(f.vertices) for f in body.data.polygons if any(arm[side][i] for i in f.vertices) and not any(hand[i] for i in f.vertices)]
def evaluated(ob):
 e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();v=np.array([ob.matrix_world@v.co for v in m.vertices]);f=[tuple(p.vertices) for p in m.polygons];e.to_mesh_clear();return v,f
def tree(parts):
 vv=[];ff=[];off=0
 for v,f in parts:
  vv.extend(v);ff.extend(tuple(i+off for i in x) for x in f);off+=len(v)
 return BVHTree.FromPolygons(vv,ff)
def helpers(side):
 fore,hand,upper=[r.data.bones[f'B_{side}_{n}'] for n in ('Forearm','Hand','UpperArm')]
 axis=(fore.matrix_local.inverted()@hand.head_local).normalized();relative=(r.pose.bones[fore.name].matrix.inverted()@r.pose.bones[hand.name].matrix).to_quaternion();rr=(fore.matrix_local.inverted()@hand.matrix_local).to_quaternion()
 _,t=armik.split_swing_twist(relative@rr.inverted(),axis);r.pose.bones[f'B_{side}_ForearmTwist'].rotation_quaternion=Quaternion(axis,.5*t)
 axis=(upper.matrix_local.inverted()@fore.head_local).normalized();_,t=armik.split_swing_twist(r.pose.bones[upper.name].matrix_basis.to_quaternion(),axis);r.pose.bones[f'B_{side}_UpperArmTwist'].rotation_quaternion=Quaternion(axis,-.5*t)
 cl=r.data.bones[f'B_{side}_Clavicle'];pa=r.data.bones[f'B_{side}_Pauldron'];rest_cl=cl.matrix_local.to_3x3();rest_u=upper.matrix_local.to_3x3();d0=rest_cl.inverted()@rest_u.col[1];d1=r.pose.bones[cl.name].matrix.to_3x3().inverted()@r.pose.bones[upper.name].matrix.to_3x3().col[1];q=d0.rotation_difference(d1);q=Quaternion(q.axis,q.angle*.8) if q.angle>1e-6 else Quaternion();rb=rest_cl.inverted()@pa.matrix_local.to_3x3();r.pose.bones[pa.name].rotation_quaternion=(rb.inverted()@q.to_matrix()@rb).to_quaternion()
 bpy.context.view_layer.update()
report={}
for clip in clips:
 act=bpy.data.actions[clip];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 report[clip]={}
 for side in 'RL':
  moving=[o for o in bpy.data.objects if o.name.startswith('Arm_') and o.get('bone') in [f'B_{side}_{n}' for n in ('UpperArm','Forearm','Pauldron')]]
  obstacles=[o for o in bpy.data.objects if o.name.startswith('Arm_') and o not in moving]
  nms=[f'B_{side}_{n}' for n in ('UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist','Pauldron')]
  frames=[]
  for frame in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
   sc.frame_set(frame);original={n:r.pose.bones[n].matrix_basis.copy() for n in nms};h=armik.W(r,f'B_{side}_Hand').copy();u=armik.W(r,f'B_{side}_UpperArm').translation.copy();e=armik.W(r,f'B_{side}_Forearm').translation.copy();axis=(h.translation-u).normalized()
   platepoints={n:evaluated(bpy.data.objects[n])[0][gate['BASE_PLATE'][n]] for n in ('Arm_breast_'+side,'Arm_chest')};rows=[]
   for angle in range(-120,121,10):
    for n,m in original.items():r.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update();pole=u+Quaternion(axis,math.radians(angle))@(e-u);armik.solve(r,side,h.translation,pole,h.to_3x3().normalized());helpers(side)
    v,_=evaluated(body);bt=BVHTree.FromPolygons(v.tolist(),gate['BFK']);contacts=100*max(gate['inside_closed'](bt,pts,1.2,gate['HIDFK'])[0] for pts in platepoints.values());stretch=np.linalg.norm(v[edges[:,0]]-v[edges[:,1]],axis=1)/np.maximum(length,1e-6);p99=float(np.percentile(stretch[mask[side]],99));sw,tw=armik.wrist_cost(r,side,h.to_3x3())
    cost=contacts*100000+max(0,sw-59.5)*100000+max(0,p99-2.04)*1000000+.01*angle*angle
    rows.append(dict(angle=angle,cost=cost,contacts=contacts,wrist=sw,p99=p99,pose={n:r.pose.bones[n].matrix_basis.copy() for n in nms}))
   for n,m in original.items():r.pose.bones[n].matrix_basis=m
   frames.append(rows)
  angles=np.array([x['angle'] for x in frames[0]]);transition=5*(angles[:,None]-angles[None,:])**2;transition[np.abs(angles[:,None]-angles[None,:])>10]=1e12
  loop=clip in ('Carbine_Standing','Carbine_Walking','Lancer_Running','Carbine_Dead')
  best=None
  for start in range(len(angles)) if loop else [None]:
   cost=np.array([x['cost'] for x in frames[0]])
   if start is not None:cost[np.arange(len(angles))!=start]=1e12
   backs=[]
   for rows in frames[1:]:
    table=cost[:,None]+transition;back=table.argmin(0);cost=table[back,np.arange(len(rows))]+np.array([x['cost'] for x in rows]);backs.append(back)
   index=start if loop else int(np.where(angles==0)[0][0]) if clip=='Carbine_Death' else int(cost.argmin())
   if best is None or cost[index]<best[0]:best=(cost[index],index,backs)
  assert best[0]<1e11,('No continuous elbow path',clip,side)
  _,index,backs=best;path=[index]
  for back in reversed(backs):index=int(back[index]);path.append(index)
  path.reverse();previous={};chosen=[]
  for f,index in enumerate(path):
   row=frames[f][index];chosen.append({k:v for k,v in row.items() if k!='pose'})
   for n,m in row['pose'].items():
    b=r.pose.bones[n];q=m.to_quaternion()
    if n in previous and q.dot(previous[n])<0:q=-q
    previous[n]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
  report[clip][side]=chosen
  print('POLE_FIT',clip,side,'contacts',max(x['contacts'] for x in chosen),'wrist',max(x['wrist'] for x in chosen),'p99',max(x['p99'] for x in chosen),'angles',[x['angle'] for x in chosen],flush=True)
 r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(src));(P/'review/cuirass_elbow_fit.json').write_text(json.dumps(report,indent=2)+'\n')
for name,args in [('bake_new_twists.py',[src,src,*clips]),('helper_bones.py',[src,src]),('gates.py',[src,'review2',*clips]),('shell_stretch.py',[src,P/'scripts/armour_lancer.json','review2',*clips]),('shell_leak.py',[src,P/'scripts/armour_lancer.json','review2',*clips]),('armour_gate.py',[src,'review2',P/'scripts/armour_lancer.json',*clips]),('render_review.py',['lancer_review2.blend','Carbine_Standing','0','front'])]:
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
