"""Delay individual finger closure until the shaft is inside the palm, using the shared surface evaluator."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
cfg=json.loads((P/'gates.json').read_text());g=S.Glb(P/'export/mm6_natm.glb');meshes=S.load_meshes(g)[:4];props=S.load_meshes(S.Glb(P/'export/mm6_natm_spear.glb'))[:4];surfaces=[]
for m in meshes:S.configure_mesh(m,cfg,S.Report(cfg));surfaces.append(S.Surface(m,m.solid&~m.regions['hand_R']))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];lg=json.loads((P/'work/round3_left_grip.json').read_text());D=json.loads((P/'work/round3_pose_reference.json').read_text());from mathutils import Matrix
start={n:Matrix(v).to_quaternion()for n,v in D['standing_basis'].items()};rows={}
for f in range(34,44):
 C.activate('Attack',f/48);rows[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones}
r.animation_data.action=None
# Retain the near-fitted knuckle frame; only the closure amount is edited.
def ramp(t):
 t=max(0,min(1,t));rr=1/3;return .5*t*t/(rr*(1-rr))if t<rr else 1-.5*(1-t)**2/(rr*(1-rr))if t>1-rr else(t-rr/2)/(1-rr)
def evaluate(params,save=False):
 cost=.1*float(params@params);result={};metrics=[];quats={}
 for f in range(34,44):
  for n,m in rows[f].items():r.pose.bones[n].matrix_basis=m
  if 34<f<42:
   bump=math.sin(math.pi*(f-34)/8)
   for n,q in lg['finger_local'].items():
    digit=int(n[len('B_L_Finger')]);close=max(0,min(1,ramp((f-27)/15)+params[digit]*bump));r.pose.bones[n].rotation_quaternion=start[n].slerp(Quaternion(q),close)
  bpy.context.view_layer.update();quats[f]={n:r.pose.bones[n].matrix.to_quaternion()for n in lg['finger_local']}
  if not 34<f<42:continue
  pose=g.rest.copy()
  for bone in r.pose.bones:
   if bone.name in g.names:pose[g.names[bone.name]]=np.array(bone.matrix)
  depths=[]
  for level,m in enumerate(meshes):
   points=m.posed(pose);prop=S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),props[level].rest);depths.append(S.penetration(surfaces[level].build(points),prop)[0])
  cost+=1000*sum(max(0,d-1.3)**2 for d in depths);metrics.append({'frame':f,'depth_mm':depths});result[f]={n:r.pose.bones[n].rotation_quaternion.copy()for n in lg['finger_local']}
 for n in lg['finger_local']:
  for f in range(34,43):
   angle=math.degrees(quats[f][n].rotation_difference(quats[f+1][n]).angle);angle=min(angle,360-angle);cost+=1000*max(0,angle-24)**2
 return(cost,result,metrics)if save else cost
best=np.zeros(5);score=evaluate(best)
for step in [.2,.1,.05,.02]:
 for sweep in range(3):
  changed=False
  for k in range(5):
   for sign in [-1,1]:
    q=best.copy();q[k]+=sign*step
    if abs(q[k])>.7:continue
    value=evaluate(q)
    if value<score:best,score=q,value;changed=True
  print('FINGER_ENTRY',step,sweep,score,best.tolist(),flush=True)
  if not changed:break
score,result,metrics=evaluate(best,True)
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f,row in result.items():
  for n,q in row.items():b=r.pose.bones[n];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_finger_entry.json').write_text(json.dumps({'amounts':best.tolist(),'objective':float(score),'frames':metrics},indent=2));print('FINGER_ENTRY_FINAL',metrics,flush=True)
