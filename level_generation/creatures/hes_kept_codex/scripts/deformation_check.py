"""Half-frame posed-mesh contacts/soles and source-relative 48 fps rotation probes."""
import bpy,sys,os,json,math,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];kind=os.environ['KEPT_BODY'];src,tag=sys.argv[sys.argv.index('--')+1:]
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];co=np.array([v.co[:] for v in me.vertices]);pc=np.array([x.value for x in me.attributes['piece'].data]);faces=[tuple(p.vertices) for p in me.polygons]
weights=np.zeros((len(co),len(names)))
for v in me.vertices:
 for g in v.groups:weights[v.index,g.group]=g.weight
mask=lambda keys:weights[:,[i for i,n in enumerate(names) if any(k in n for k in keys)]].sum(1)>.5
feet=np.isin(pc,(5,6) if kind=='male' else (5,7));hands={sd:mask((f'B_{sd}_Hand',f'B_{sd}_Finger')) for sd in 'LR'}
arm_part={'L':4 if kind=='male' else 3,'R':3 if kind=='male' else 4}
forearms={sd:mask((f'B_{sd}_Forearm',))&(pc==arm_part[sd]) for sd in 'LR'}
skin_faces={x:[f for f in faces if all(pc[i]==x for i in f)] for x in (1,3,4)}
cloth_faces=[f for f in faces if pc[f[0]] not in (1,3,4)]
# The rolled sleeve deliberately overlaps its own proximal skin. Keep that contact separate from body collisions.
cuff_faces={}
for sd in 'LR':
 elbow=np.array(rig.data.bones[f'B_{sd}_Forearm'].head_local);wrist=np.array(rig.data.bones[f'B_{sd}_Hand'].head_local);axis=wrist-elbow;length=np.linalg.norm(axis);axis/=length
 centres=np.array([co[list(f)].mean(0)for f in cloth_faces]);t=(centres-elbow)@axis;rad=np.linalg.norm(centres-elbow-t[:,None]*axis,axis=1)
 cuff_faces[sd]={i for i,f in enumerate(cloth_faces)if pc[f[0]]==0 and .10*length<t[i]<.55*length and rad[i]<.09}
BONES=['B_Head' ,'B_Neck','B_Spine2']+[f'B_{sd}_{b}' for sd in 'LR' for b in ('UpperArm','Forearm','Hand','Foot')]
props={}
if kind=='male':
 G=json.loads((P/'work/male/handle_R.json').read_text());C=Vector(G['handle_centre_hand_local']);A=Vector(G['handle_axis_hand_local'])
 # Same square source grip as the G1 prop review; X is the broad pick-head direction.
 source=json.loads((P/'work/male/source_rest.json').read_text());fdir=Vector(source['B_R_Finger2']['head'])-Vector(source['B_R_Hand']['head'])
 Rs=Matrix(source['B_R_Hand']['rot']);X=Rs.inverted()@fdir;X=(X-A*X.dot(A)).normalized();Y=A.cross(X)
 R=Matrix((X,Y,A)).transposed().to_4x4();R.translation=C
 with bpy.data.libraries.load(str(P/'work/props/props.blend'),link=False) as (data,to):to.objects=[n for n in data.objects if n in ('hes_kept_pick','hes_kept_club')]
 for o in to.objects:
  points=[v.co.copy() for v in o.data.vertices]
  points += [sum((o.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices) for f in o.data.polygons]
  points += [(o.data.vertices[e.vertices[0]].co+o.data.vertices[e.vertices[1]].co)*.5 for e in o.data.edges]
  props[o.name.removeprefix('hes_kept_')]=[R@v for v in points]
 assert set(props)=={'pick','club'},list(props)
def act(a):
 rig.animation_data_create();rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def posed():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();out=[body.matrix_world@v.co for v in m.vertices];ev.to_mesh_clear();return out
def inside(tree,p):
 direction=Vector((.719,.371,.588)).normalized();origin=p.copy();hits=0
 for _ in range(64):
  hit,n,ix,d=tree.ray_cast(origin,direction,10.)
  if hit is None:return hits%2==1
  hits+=1;origin=hit+direction*1e-5
 raise AssertionError('Ray did not leave closed skin')
report={'source':str(Path(src).relative_to(P) if Path(src).is_absolute() else Path(src)),'source_sha256':hashlib.sha256(Path(src).read_bytes()).hexdigest(),'half_frame_step':.5,'jerk_sample_hz':48,'clips':{}}
for name in sorted(a.name for a in bpy.data.actions if a.name.startswith('Kept_')):
 a=bpy.data.actions[name];act(a);f0,f1=a.frame_range;row={'skin_penetration_m':{},'cloth_proximity_vertices':{},'expected_cuff_proximity_vertices':{},'wrist_swing_deg':{},'wrist_twist_deg':{},'rotation_steps':{}}
 low=[];swing={sd:[] for sd in 'LR'};twist={sd:[] for sd in 'LR'}
 for f in np.arange(f0,f1+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));points=posed();arr=np.array(points);assert np.isfinite(arr).all();low.append([float(f),float(arr[feet,2].min()),float(arr[:,2].min())])
  skin={k:BVHTree.FromPolygons(points,fl) for k,fl in skin_faces.items()};cloth=BVHTree.FromPolygons(points,cloth_faces)
  for sd in 'LR':
   sw,tw=armik.wrist_cost(rig,sd,armik.W(rig,f'B_{sd}_Hand').to_3x3().normalized());swing[sd].append(sw);twist[sd].append(tw)
   samples={f'{sd}_hand':[points[i] for i in np.where(hands[sd])[0]],f'{sd}_forearm':[points[i] for i in np.where(forearms[sd])[0]]}
   if sd=='R' and (name.startswith('Kept_Armed') or name=='Kept_MaceAttack'):
    H=armik.W(rig,'B_R_Hand');samples.update({pn:[H@v for v in vs] for pn,vs in props.items()})
   for key,pts in samples.items():
    depth=0.;close=0;covered=0
    for pt in pts:
     for part,tree in skin.items():
      if part==arm_part[sd] and key.startswith(sd+'_'):continue
      loc,normal,idx,dist=tree.find_nearest(pt,.15)
      if loc is not None and (pt-loc).dot(normal)<-.7*dist and inside(tree,pt):depth=max(depth,dist)
     loc,n,idx,dist=cloth.find_nearest(pt,.003)
     if loc is not None:
      if key.endswith('_forearm') and idx in cuff_faces[sd]:covered+=1
      else:close+=1
    if depth>row['skin_penetration_m'].get(key,{}).get('depth',0):row['skin_penetration_m'][key]={'depth':depth,'frame':float(f)}
    if covered>row['expected_cuff_proximity_vertices'].get(key,{}).get('count',0):row['expected_cuff_proximity_vertices'][key]={'count':covered,'frame':float(f)}
    if close>row['cloth_proximity_vertices'].get(key,{}).get('count',0):row['cloth_proximity_vertices'][key]={'count':close,'frame':float(f)}
 for sd in 'LR':
  row['wrist_swing_deg'][sd]=max(swing[sd]);row['wrist_twist_deg'][sd]=[min(twist[sd]),max(twist[sd])]
 low=np.array(low);row['sole_range_m']=[float(low[:,1].min()),float(low[:,1].max())];row['whole_body_floor_m']=[float(low[:,2].min()),float(low[:,2].max())]
 row['samples']=len(low);row['floor_pass']=row['whole_body_floor_m'][0]>=-.02 and (('Running' in name) or ('Death' in name) or ('Dead' in name) or row['sole_range_m'][1]<=.02)
 Q={b:[] for b in BONES}
 for f in np.arange(f0,f1+.001,30/48):
  sc.frame_set(int(f),subframe=float(f%1))
  for b in BONES:Q[b].append(armik.W(rig,b).to_quaternion())
 for b,qs in Q.items():
  steps=np.array([math.degrees(q0.rotation_difference(q1).angle) for q0,q1 in zip(qs[:-1],qs[1:])]);steps=np.minimum(steps,360-steps)
  row['rotation_steps'][b]={'max_step_deg':float(steps.max(initial=0)),'max_second_difference_deg':float(abs(np.diff(steps)).max(initial=0))}
 report['clips'][name]=row
 print('CONTACT',kind,name,'floor',row['floor_pass'],row['sole_range_m'],'skin',row['skin_penetration_m'],'cloth',row['cloth_proximity_vertices'],'wrist',row['wrist_swing_deg'],flush=True)
report['cuff_contact_policy']='Only forearm versus its own rolled sleeve: shirt faces 10-55% down the rest elbow-wrist axis and radial distance <9cm; skin and other clothing remain checked.'
report['sampled_vertices']={sd:{'hand':int(hands[sd].sum()),'forearm':int(forearms[sd].sum())}for sd in 'LR'}
report['pass']=all(r['floor_pass'] and not r['skin_penetration_m'] and not r['cloth_proximity_vertices'] and max(r['wrist_swing_deg'].values())<=60 and all(max(map(abs,v))<=90 for v in r['wrist_twist_deg'].values()) for r in report['clips'].values())
(P/'review'/kind/f'{tag}_deformation.json').write_text(json.dumps(report,indent=2)+'\n')

assert report['pass'],'Deformation gate failed; see report'

sys.stdout.flush();sys.stderr.flush();os._exit(0)
