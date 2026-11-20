"""48 Hz geometric palms, foot contact, and source-relative angular acceleration."""
import bpy,sys,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];ROOT=P.parents[2]
ROLES=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']
def activate(r,a):
 r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()
 r.animation_data.action=a
 if a.slots:r.animation_data.action_slot=a.slots[0]
def traces(r,a,names):
 activate(r,a);sc=bpy.context.scene;frames=np.linspace(a.frame_range[0],a.frame_range[1],math.ceil((a.frame_range[1]-a.frame_range[0])*48/sc.render.fps)+1);prev=None;vel=[];rows=[]
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));cur={n:(r.matrix_world@r.pose.bones[n].matrix).to_quaternion()for n in names}
  if prev is not None:
   vec=[]
   for n in names:
    q=prev[n].rotation_difference(cur[n])
    if q.w<0:q=-q
    axis,angle=q.to_axis_angle();vec.append(np.array(axis)*math.degrees(angle))
   vel.append(vec)
  prev=cur
 arr=np.array(vel);acc=np.diff(arr,axis=0)
 return {n:{'max_step_deg':float(np.linalg.norm(arr[:,i],axis=1).max()),'max_step_time_s':float(frames[1+np.argmax(np.linalg.norm(arr[:,i],axis=1))]/sc.render.fps),'max_accel_deg_per_sample2':float(np.linalg.norm(acc[:,i],axis=1).max())}for i,n in enumerate(names)}
bpy.ops.wm.open_mainfile(filepath=os.environ.get('MOTION_BLEND',str(P/'work/export_reimport_lod0.blend')));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;names=[f'B_{s}_{n}'for s in 'LR'for n in ['UpperArm','Forearm','Hand']]
rest={n:b.matrix_local.copy()for n,b in r.data.bones.items()};co=np.array([v.co[:]for v in body.data.vertices]);gn={g.index:g.name for g in body.vertex_groups};sole={};palm={}
for sd in 'LR':
 ids=[v.index for v in body.data.vertices if co[v.index,2]<.008 and sum(g.weight for g in v.groups if gn[g.group]in[f'B_{sd}_Foot',f'B_{sd}_Toe'])>.8];sole[sd]=ids
 W=r.data.bones[f'B_{sd}_Hand'].head_local;kn=[r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(1,5)];K=sum(kn,Vector())/4;axis=(kn[0]-kn[-1]).normalized();N=axis.cross((K-W).normalized()).normalized();tips=sum((r.data.bones[f'B_{sd}_Finger{i}2'].head_local for i in range(1,5)),Vector())/4
 if (tips-K).dot(N)<0:N=-N
 palm[sd]=(rest[f'B_{sd}_Hand'].inverted().to_3x3()@N,rest[f'B_{sd}_Hand'].inverted()@K)
out={'hands':{s:{'palm_axis':list(palm[s][0]),'elbow_hinge_axis':list((rest[f'B_{s}_UpperArm'].inverted().to_3x3()@(r.data.bones[f'B_{s}_Forearm'].head_local-r.data.bones[f'B_{s}_UpperArm'].head_local).cross(r.data.bones[f'B_{s}_Hand'].head_local-r.data.bones[f'B_{s}_Forearm'].head_local)).normalized())}for s in 'LR'},'hz':48,'clips':{},'stride_m':{'Walking':.9,'Running':1.395},'run_multiplier':1.55}
for name in ROLES:
 a=bpy.data.actions[name];trace=traces(r,a,names+[b.name for b in r.data.bones if 'Finger'in b.name or 'Twist'in b.name or b.name=='Knife']);activate(r,a);rows=[];nf=a.frame_range[1]
 for f in np.linspace(0,nf,math.ceil(nf*48/30)+1):
  sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pos=np.array([v.co[:]for v in me.vertices]);ev.to_mesh_clear();row={'time':float(f/30),'palms':{},'feet':{}}
  for sd in 'LR':
   hand=r.pose.bones[f'B_{sd}_Hand'].matrix;normal=(hand.to_3x3()@palm[sd][0]).normalized();kn=hand@palm[sd][1];thigh=r.pose.bones[f'B_{sd}_Thigh'].head;inward=Vector((thigh.x-kn.x,thigh.y-kn.y,0)).normalized();delta=r.pose.bones[f'B_{sd}_Foot'].matrix@rest[f'B_{sd}_Foot'].inverted();forward=delta.to_3x3()@Vector((0,-1,0));yaw=abs(math.degrees(math.atan2(forward.x,-forward.y)));entry={'normal':list(normal),'toward_thigh':float(normal.dot(inward))}
   if sd=='R'and name=='Attack':entry['toward_grip']=float(normal.dot((r.pose.bones['Knife'].head-kn).normalized()))
   row['palms'][sd]=entry;row['feet'][sd]={'sole_m':float(pos[sole[sd],2].min()),'yaw_deg':yaw}
  rows.append(row)
 grounded=[min(x['feet'][s]['sole_m']for s in 'LR')<=.01 for x in rows]
 out['clips'][name]={'trace':trace,'samples':rows,'ground_contact_fraction':float(np.mean(grounded)),'max_both_soles_above_m':float(max(min(x['feet'][s]['sole_m']for s in 'LR')for x in rows)),'foot_yaw_max_deg':max(x['feet'][s]['yaw_deg']for x in rows for s in 'LR'),'palm_inward_min':{s:min(x['palms'][s]['toward_thigh']for x in rows)for s in 'LR'}}
sources={'Walking':('humanoid_set/Relax.glb','RelaxWalkFemale3'),'Running':('humanoid_set/Relax.glb','RelaxRunForward'),'Attack':('humanoid_set/1Hand.glb','DaggerAttackR3'),'Hit':('humanoid_set/Unarmed.glb','UnarmedGetHitF1'),'Death':('mixamo/Falling Forward Death.fbx',None)}
for role,(path,clip)in sources.items():
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
 if path.endswith('.fbx'):bpy.ops.import_scene.fbx(filepath=str(ROOT/'anim_library'/path))
 else:bpy.ops.import_scene.gltf(filepath=str(ROOT/'anim_library'/path))
 arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');act=next(a for a in bpy.data.actions if clip is None or a.name.split('@')[-1].split('|')[-1]==clip)
 if clip is None:
  mapping={f'B_{s}_{part}':next(b.name for b in arm.data.bones if b.name.endswith(('Left'if s=='L'else'Right')+{'UpperArm':'Arm','Forearm':'ForeArm','Hand':'Hand'}[part]))for s in 'LR'for part in ['UpperArm','Forearm','Hand']}
 else:mapping={n:n for n in names}
 src=traces(arm,act,list(mapping.values()));src={k:src[v]for k,v in mapping.items()};out['clips'][role]['source_trace']=src
for name,entry in out['clips'].items():
 flags=[]
 for n,v in entry['trace'].items():
  group=[v for k,v in entry.get('source_trace',{}).items()if k.endswith('Hand')==any(t in n for t in ['Hand','Finger','Knife'])];src={key:max([v[key]for v in group]or[15])for key in ['max_step_deg','max_accel_deg_per_sample2']}
  if v['max_step_deg']>src['max_step_deg']+10 or v['max_accel_deg_per_sample2']>src['max_accel_deg_per_sample2']*1.5+15:flags.append(n)
 entry['smoothness_flags']=flags
(P/'review/motion_proof.json').write_text(json.dumps(out,indent=2))
print('MOTION_PROOF',json.dumps({n:{k:v for k,v in d.items()if k not in ['trace','source_trace','samples']}for n,d in out['clips'].items()}),flush=True)
