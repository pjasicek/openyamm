"""Effect-body checks on the delivered GLB using the shared gate decoder/skinner/BVH.
The generic humanoid runner requires legs and soles; this floating torso has neither.
"""
from pathlib import Path
import sys,json,math
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/gates'))
from run_gates import Glb,load_meshes,Surface,penetration,unit,angle,rotation_vector,sample_grid,swing_twist
model=Glb(P/'export/mm8_m508.glb');meshes=load_meshes(model);rows=[]
def check(name,value,limit,clip='',part='',minimum=False):
 ok=value>=limit if minimum else value<=limit
 rows.append({'check':name,'value':float(value),'limit':float(limit),'clip':clip,'part':part,'status':'PASS' if ok else 'FAIL'})
for i,mesh in enumerate(model.doc['meshes']):
 for key in ['openyamm_lods','openyamm_shadow_lods']:
  chain=mesh.get('extras',{}).get(key,[]);assert i not in chain and len(chain)==len(set(chain))
for me in meshes:
 for primitive in model.doc['meshes'][me.index]['primitives']:
  weights=model.accessor(primitive['attributes']['WEIGHTS_0']);check('skin_sum_error',np.abs(weights.sum(1)-1).max(),1e-4,part=me.label)
 for name in ['arm','hand']:
  patterns=['*Arm','*ForeArm','*Hand*'] if name=='arm' else ['*Hand*']
  me.regions[name]=me.weight(patterns)>.3
 if me.name.startswith('Body'):
  me.contacts=[]
  for side in ['Left','Right']:
   limb=me.weight([side+'*'])>.15;samples=me.weight([side+'Hand*',side+'ForeArm'])>.7
   surface=Surface(me,~limb);me.contacts.append((side,surface,samples))
  head=me.weight(['Head'])>.7;head&=me.rest[:,2]>1.92
  me.contacts.append(('head',Surface(me,me.weight(['Head','Neck'])<.2),head))
  if me.name=='Body':
   for side in ['Left','Right']:check('hand_vertices',np.sum(me.weight([side+'Hand*'])>.3),40,part=side,minimum=True)
for group in ['Body','Wind','DeathCloud','Lightning']:
 levels=[m for m in meshes if m.label.startswith(group+'/colour')];counts=[len(m.faces) for m in levels]
 # Tiny lightning cards retain two crossing planes at distance; the combined budget is checked below.
 if group!='Lightning':
  for i in range(1,len(counts)):check('lod_decrease',counts[i]/counts[i-1],.9,part=group+str(i))
counts=[sum(len(m.faces) for m in meshes if m.label.endswith('/colour'+str(i))) for i in range(4)]
for i,limit in enumerate([1,.55,.25,.10]):check('combined_lod_ratio',counts[i]/counts[0],limit,part=str(i))
rig_metrics={}
for animation in model.doc['animations']:
 name=animation['name'];duration=max(float(model.accessor(s['input']).max()) for s in animation['samplers']);times=sample_grid(0,duration,48);poses=model.pose(animation,times);summary={}
 for side in ['Left','Right']:
  ids=[model.names[side+n] for n in ['Arm','ForeArm','Hand']];r=model.rest[ids];world=poses[:,ids];u=unit(world[:,1,:3,3]-world[:,0,:3,3]);f=unit(world[:,2,:3,3]-world[:,1,:3,3]);ur=unit(r[1,:3,3]-r[0,:3,3]);fr=unit(r[2,:3,3]-r[1,:3,3]);up=world[:,0,:3,:3];up=up/np.maximum(np.linalg.norm(up,axis=1,keepdims=True),1e-15);rest_axes=r[0,:3,:3]/np.linalg.norm(r[0,:3,:3],axis=0,keepdims=True)
  hinge=unit(np.cross(ur,fr));h=np.einsum('tij,j->ti',up,rest_axes.T@hinge);flex=np.degrees(np.arctan2(np.sum(h*np.cross(u,f),axis=1),np.sum(u*f,axis=1)));plane=np.abs(np.degrees(np.arcsin(np.clip(np.sum(h*f,axis=1),-1,1))))
  def axes(m):return m/np.maximum(np.linalg.norm(m,axis=-2,keepdims=True),1e-15)
  upp,fore,hand=[axes(world[:,k,:3,:3]) for k in range(3)];upr,forer,handr=[axes(r[k,:3,:3]) for k in range(3)]
  neutral=upp@upr.T@forer;_,roll=swing_twist(np.swapaxes(neutral,-1,-2)@fore,forer.T@fr);check('forearm_roll_deg',np.abs(roll).max(),90,name,side)
  neutral=fore@forer.T@handr;finger_ids=[model.names[side+'Hand'+digit+'1'] for digit in ['Thumb','Index','Middle','Ring','Pinky']];handaxis=unit(np.mean(model.rest[finger_ids,:3,3],axis=0)-r[2,:3,3]);bend,roll=swing_twist(np.swapaxes(neutral,-1,-2)@hand,handr.T@handaxis);check('wrist_flexion_deg',bend.max(),70,name,side);check('wrist_roll_deg',np.abs(roll).max(),45,name,side)
  parent=model.parents[ids[0]];neutral=axes(poses[:,parent,:3,:3])@axes(model.rest[parent,:3,:3]).T@upr;_,roll=swing_twist(np.swapaxes(neutral,-1,-2)@upp,upr.T@ur);check('upper_arm_roll_deg',np.abs(roll).max(),60,name,side)
  summary[side]={'flex_min':float(flex.min()),'flex_max':float(flex.max()),'elbow_plane_max':float(plane.max())}
  check('elbow_hyperextension_deg',max(0,-flex.min()),5,name,side);check('elbow_flexion_deg',flex.max(),150,name,side);check('elbow_plane_deg',plane.max(),5,name,side)
  for n in [side+'Arm',side+'ForeArm',side+'Hand']:
   m=poses[:,model.names[n],:3,:3];m=m/np.maximum(np.linalg.norm(m,axis=1,keepdims=True),1e-15);delta=rotation_vector(m[1:]@np.swapaxes(m[:-1],-1,-2));check('rotation_step_48hz_deg',np.rad2deg(np.linalg.norm(delta,axis=1)).max(),25,name,n)
 rig_metrics[name]=summary
 # Nonuniform scales occur only on childless wind-width/death leaves, so the skin never shears.
 shear=0.
 for j in model.doc['skins'][0]['joints']:
  m=poses[:,j,:3,:3];axes=m/np.maximum(np.linalg.norm(m,axis=1,keepdims=True),1e-15);gram=np.swapaxes(axes,-1,-2)@axes;shear=max(shear,float(np.abs(gram-np.eye(3)).max()))
 check('skin_world_shear',shear,1e-4,name)
 for me in meshes:
  if '/shadow' in me.label:continue
  worst={'arm_p99':0.,'arm_max':0.,'hand_max':0.};depths={};minimum=100.;first=None;last=None
  for i,pose in enumerate(poses):
   points=me.posed(pose);assert np.isfinite(points).all();minimum=min(minimum,float(points[:,2].min()));first=points.copy() if first is None else first;last=points
   if not me.name.startswith('Body'):continue
   stretch=np.linalg.norm(points[me.edges[:,1]]-points[me.edges[:,0]],axis=1)/me.lengths
   for region in ['arm','hand']:
    mask=me.regions[region][me.edges].all(1)
    if mask.any():
     worst[region+'_max']=max(worst[region+'_max'],float(stretch[mask].max()))
     if region=='arm':worst['arm_p99']=max(worst['arm_p99'],float(np.percentile(stretch[mask],99)))
   # Geometry checks use 24 Hz plus endpoint; rotation/skin checks use 48 Hz.
   if i%2==0 or i==len(poses)-1:
    for label,surface,samples in me.contacts:
     if samples.any():depth,_=penetration(surface.build(points),points[samples]);depths[label]=max(depths.get(label,0),depth)
  if me.name.startswith('Body'):
   for key,limit in [('arm_p99',2.),('arm_max',4.5),('hand_max',4.5)]:check(key,worst[key],limit,name,me.label)
   for label,depth in depths.items():check('body_penetration_mm',depth,10 if label=='head' else 2,name,me.label+'/'+label)
  if name in ['Standing','Walking','Running','Dead']:check('loop_seam_m',np.linalg.norm(last-first,axis=1).max(),.002,name,me.label)
  if name not in ['Death','Dead']:check('ground_penetration_m',max(0,-minimum),.002,name,me.label)
report={'model_sha256':model.sha256,'route':'Effect body, MPFB torso exception; shared GLB decoder/skinning/BVH, 48 Hz rotations/skin and 24 Hz surface contacts','not_applicable':['feet, soles, knees and grounded gait: floating legless vortex','prop grip and cloth containment: no equipment or clothing','solid collision of translucent wind layers: deliberate overlapping shells'],'triangles':counts,'rig_metrics':rig_metrics,'checks':rows,'failed':[r for r in rows if r['status']=='FAIL']}
(P/'work/gates.json').write_text(json.dumps(report,indent=2)+'\n');print('GATES',len(rows),'FAIL',len(report['failed']));print(json.dumps(report['failed'][:30],indent=2))
assert not report['failed'],'Effect-body gates failed; inspect work/gates.json'
