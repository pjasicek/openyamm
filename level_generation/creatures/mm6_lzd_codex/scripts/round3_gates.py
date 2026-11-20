"""48 Hz checks of anatomical elbows, actual sole direction, carry, palms and wrap contact."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from volume_contact import volumes,deepest
P=Path(__file__).resolve().parents[1]
source=Path(sys.argv[sys.argv.index('--')+1]) if '--'in sys.argv else P/'work/master_round3_motion.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
intent=json.loads((P/'work/round3_motion.json').read_text());normal=Vector(json.loads((P/'work/cast_intent.json').read_text())['palm_normal_hand_local'])
me=body.data;names=[g.name for g in body.vertex_groups];co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
sole={s:np.where((co[:,2]<.13)&(W[:,[i for i,n in enumerate(names)if n in [f'B_{s}_Foot',f'B_{s}_Toe0']]].sum(1)>.55))[0]for s in 'LR'}
heeltoe={side:{end:ids[co[ids,1] <= np.percentile(co[ids,1],30)] if end=='toe' else ids[co[ids,1]>=np.percentile(co[ids,1],70)] for end in ['toe','heel']} for side,ids in sole.items()}
flapfaces=[list(f.vertices)for f in me.polygons if all(pv[i]==15 for i in f.vertices)]
legids=np.where((pv==1)&(W[:,[i for i,n in enumerate(names)if any(x in n for x in ['Thigh','Calf','Foot','Toe'])]].sum(1)>.5))[0]
inv=rig.data.bones['Bow'].matrix_local.inverted();local=np.array([tuple(inv@Vector(v))for v in co]);wrapfaces=[list(f.vertices)for f in me.polygons if all(pv[i]==201 and abs(local[i,2])<.100 for i in f.vertices)]
assert wrapfaces
bowtree=BVHTree.FromPolygons(local.tolist(),wrapfaces)
me.calc_loop_triangles();digitfaces={}
for digit in [0,1,2,4]:
 mask=W[:,[i for i,n in enumerate(names)if n.startswith(f'B_L_Finger{digit}')]].sum(1)>.4
 digitfaces[str(digit)]=np.array([tuple(f.vertices)for f in me.loop_triangles if any(mask[i]for i in f.vertices) and all(pv[i]==3 for i in f.vertices)],dtype=int).reshape(-1,3)
bary=np.array([[i,j,4-i-j]for i in range(5)for j in range(5-i)])/4
source_limits=json.loads((P/'work/source_motion_limits.json').read_text())['clips']
groups={'arms':[f'B_{sd}_{n}'for sd in 'LR'for n in ['UpperArm','Forearm']],'hands':[f'B_{sd}_Hand'for sd in 'LR'],'twist':[f'B_{sd}_{n}'for sd in 'LR'for n in ['UpperArmTwist','ForearmTwist']],'fingers':[n for n in names if 'Finger'in n],'bow':['Bow']}
rows={};issues=[];adjacency={}
for side in 'LR':
 hand=W[:,names.index(f'B_{side}_Hand')]>.5;distal=[i for i,n in enumerate(names)if n.startswith(f'B_{side}_Finger')and n.endswith('2')and len(n.rsplit('Finger',1)[1])==2];tip=W[:,distal].sum(1)>.5
 adjacency[side]=sum(bool((hand[e.vertices[0]]and tip[e.vertices[1]])or(hand[e.vertices[1]]and tip[e.vertices[0]]))for e in me.edges)
 if adjacency[side]:issues.append([side,'G5_adjacency'])

for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];duration=float(a.frame_range[1]/30);out=[];previous=None;trace={g:0 for g in groups}
 for t in np.r_[np.arange(0,duration,1/48),duration]:
  f=t*30;sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=np.array([tuple(x.co)for x in m.vertices]);ev.to_mesh_clear()
  current={n:rig.pose.bones[n].matrix.to_quaternion()for ns in groups.values()for n in ns}
  if previous is not None:
   for group,ns in groups.items():
    for n in ns:
     angle=math.degrees(previous[n].rotation_difference(current[n]).angle);trace[group]=max(trace[group],min(angle,360-angle))
  previous=current
  r={'body_floor':float(v[pv!=202,2].min()),'time':float(t),'feet':{},'arms':{},'grip':{}}
  for s in 'LR':
   foot=rig.pose.bones[f'B_{s}_Foot'];d=foot.matrix.to_3x3()@Vector(intent['feet'][s]['forward_foot_local']);yaw=math.degrees(math.atan2(d.x,-d.y));u,fa,h=[rig.pose.bones[f'B_{s}_{n}']for n in ['UpperArm','Forearm','Hand']]
   x=(fa.head-u.head).normalized();y=(h.head-fa.head).normalized();axis=-u.matrix.to_3x3().col[2].normalized()
   r['arms'][s]={'flex':math.degrees(math.atan2(axis.dot(x.cross(y)),x.dot(y))),'plane':abs(math.degrees(math.asin(np.clip(axis.dot(y),-1,1)))),'twist':min(math.degrees(rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion.angle),360-math.degrees(rig.pose.bones[f'B_{s}_ForearmTwist'].rotation_quaternion.angle)),'upper_twist':math.degrees(rig.pose.bones[f'B_{s}_UpperArmTwist'].rotation_quaternion.angle)}
   th,ca,fo=[rig.pose.bones[f'B_{s}_{n}'].head for n in ['Thigh','Calf','Foot']];knee=math.degrees((ca-th).angle(fo-ca));hpts=v[sole[s]];r['feet'][s]={'yaw':yaw,'sole_min':float(hpts[:,2].min()),'sole_max':float(hpts[:,2].max()),'knee':knee,'heel':float(v[heeltoe[s]['heel'],2].min()),'toe':float(v[heeltoe[s]['toe'],2].min())}
  rh=rig.pose.bones['B_R_Hand'];palm=(rh.matrix.to_3x3()@normal).normalized();r['palm_in']=float(palm.dot(Vector((1,0,0))));r['right_wrist']=list(rh.head)
  bm=rig.pose.bones['Bow'].matrix;r['bow_up']=float(bm.to_3x3().col[2].normalized().z);r['string_body']=float(bm.to_3x3().col[1].normalized().y)
  # The minimum surface distance of each curled digit to the actual textured grip wrap.
  inverse=bm.inverted();xyz=(np.array(inverse)@np.c_[v,np.ones(len(v))].T).T[:,:3]
  for digit,tris in digitfaces.items():
   points=np.einsum('jk,nkl->njl',bary,xyz[tris]).reshape(-1,3);points=points[abs(points[:,2])<.110]
   distances=[bowtree.find_nearest(Vector(p))[3]for p in points];r['grip'][digit]=min(distances)if distances else float('inf')
  r['cloth_depth_m']=0
  if flapfaces:
   hem=min(v[i,2]for face in flapfaces for i in face);ids=[i for i in legids if v[i,2]>=hem+.005]
   r['cloth_depth_m']=deepest(volumes(v,flapfaces,pv),v[ids])[0]if ids else 0
  out.append(r)
 result={'samples':len(out),'elbows':{s:{'flex_min':min(r['arms'][s]['flex']for r in out),'plane_max':max(r['arms'][s]['plane']for r in out),'forearm_twist_max':max(r['arms'][s]['twist']for r in out),'upper_twist_max':max(r['arms'][s]['upper_twist']for r in out)}for s in 'LR'},'feet':{s:{'yaw_min_deg':min(r['feet'][s]['yaw']for r in out),'yaw_max_deg':max(r['feet'][s]['yaw']for r in out),'lowest_sole_m':min(r['feet'][s]['sole_min']for r in out),'swing_peak_m':max(r['feet'][s]['sole_min']for r in out),'knee_at_peak_deg':max(out,key=lambda r:r['feet'][s]['sole_min'])['feet'][s]['knee'],'heel_height_max_m':max(r['feet'][s]['heel']for r in out),'toe_height_max_m':max(r['feet'][s]['toe']for r in out)}for s in 'LR'},'free_palm_toward_thigh_min_dot':min(r['palm_in']for r in out),'bow_vertical_min_dot':min(r['bow_up']for r in out),'string_toward_body_min_dot':min(r['string_body']for r in out),'grip_distance_max_m':{d:max(r['grip'][d]for r in out)for d in digitfaces},'contact_fraction':sum(min(r['feet'][s]['sole_min']for s in 'LR')<=.01 for r in out)/len(out)}
 limits={g:source_limits[a.name]['arms' if g in ['arms','twist'] else 'hands']+10 for g in groups}
 result['source_motion_trace_degrees_per48hz']=trace;result['source_motion_limits_degrees_per48hz']=limits
 for g in trace:
  if trace[g]>limits[g]:issues.append([a.name,'motion_trace',g])
 result['body_floor_min_m']=min(r['body_floor']for r in out);result['body_floor_max_m']=max(r['body_floor']for r in out)
 if a.name=='Dead' and not(-.002<=result['body_floor_min_m']<=result['body_floor_max_m']<=.01):issues.append([a.name,'corpse_floor'])
 result['cloth_leg_flap_penetration_m']=max(r['cloth_depth_m']for r in out)
 if result['cloth_leg_flap_penetration_m']>.002:issues.append([a.name,'cloth'])
 if a.name in ['Standing','Fidget'] and max(max(x['heel_height_max_m'],x['toe_height_max_m'])for x in result['feet'].values())>.01:issues.append([a.name,'rest_sole'])
 if a.name in ['Walking','Running']:
  if result['contact_fraction']<.8 or min(x['lowest_sole_m']for x in result['feet'].values())<-.002:issues.append([a.name,'floor'])
  if a.name=='Walking' and any(not(.08<=x['swing_peak_m']<=.12)for x in result['feet'].values()):issues.append([a.name,'swing'])
 rows[a.name]=result
 print('ROUND3_GATE',a.name,result,flush=True)
 for s,x in result['elbows'].items():
  if x['flex_min']<-5 or x['plane_max']>1 or x['forearm_twist_max']>90.1:issues.append([a.name,s,'elbow'])
 if a.name in ['Standing','Fidget','Walking','Running']:
  if result['free_palm_toward_thigh_min_dot']<.85:issues.append([a.name,'palm'])
  for s,x in result['feet'].items():
   if max(abs(x['yaw_min_deg']),abs(x['yaw_max_deg']))>10:issues.append([a.name,s,'foot_yaw'])
 if a.name in ['Standing','Fidget','Walking','Running','Hit'] and(result['bow_vertical_min_dot']<.80 or result['string_toward_body_min_dot']<.80):issues.append([a.name,'bow_carry'])
 if max(result['grip_distance_max_m'].values())>.003:issues.append([a.name,'grip'])
report={'source':str(source),'G5_direct_hand_to_distal_edges':adjacency,'clips':rows,'issues':issues,'passed':not issues}
(P/'review/round3_motion_gate.json').write_text(json.dumps(report,indent=2));print('ISSUES',issues)
