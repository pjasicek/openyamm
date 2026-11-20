"""Fit the actual club around the body by small, smoothed wrist rotations; preserve the source blow."""
import bpy,sys,math,json,importlib.util,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1];root=p.parents[2];sys.path.insert(0,str(p/'scripts'));import armik
spec=importlib.util.spec_from_file_location('gates',root/'level_generation/creatures/claude_shared/gates/run_gates.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
cfg=json.loads((p/'full.gates.json').read_text());gl=g.Glb(p/'export/m440_full_body.glb');mesh=g.load_meshes(gl)[0];report=g.Report(cfg);g.configure_mesh(mesh,cfg,report)
pg=g.Glb(p/'export/m440_full_club.glb');pm=g.load_meshes(pg)[0]
prop_surface=g.Surface(mesh,~mesh.regions['hand_R']);hand_surface=g.Surface(mesh,~mesh.regions['limb_R'])
hand_ids=np.flatnonzero(mesh.regions['hand_R'])[::3]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
def action(a):
 rig.animation_data.action=a
 if a is not None:rig.animation_data.action_slot=a.slots[0]
ledger={}
for name in ('Running',):
 animation=next(a for a in gl.doc['animations'] if a['name']==name);act=bpy.data.actions[name];N=int(act.frame_range[1]);times=np.arange(N+1)/30;poses=gl.pose(animation,times);vectors=[];rows=[];previous=np.zeros(3)
 for f,pose in enumerate(poses):
  body=mesh.posed(pose);prop=g.transform(pose[gl.names['Club']]@np.linalg.inv(g.C),pm.rest);wrist=pose[gl.names['B_R_Hand'],:3,3]
  prop_surface.build(body);hand_surface.build(body);hand=body[hand_ids]
  def measure(q):
   R=np.array(q.to_matrix());pp=(prop-wrist)@R.T+wrist;hh=(hand-wrist)@R.T+wrist
   ds,_=prop_surface.signed(pp);dh,_=hand_surface.signed(hh)
   return min(float(ds.min()),float(dh.min()))
  before=measure(Quaternion());best=np.zeros(3);after=before
  if before<.004:
   direction=Vector(prop[np.argmax(np.linalg.norm(prop-wrist,axis=1))]-wrist).normalized();u=direction.orthogonal().normalized();v=direction.cross(u);candidates=[]
   for angle in range(3,37,3):
    for k in range(12):
     axis=u*math.cos(k*math.pi/6)+v*math.sin(k*math.pi/6);q=Quaternion(axis,math.radians(angle));clear=measure(q)
     if clear>=.006:
      vec=np.array(axis)*math.radians(angle);cost=angle+.4*np.linalg.norm(vec-previous)*180/math.pi;candidates.append((cost,vec,clear))
    if candidates:break
   if candidates:_,best,after=min(candidates,key=lambda x:x[0])
  vectors.append(best);previous=best;rows.append({'frame':f,'before_mm':before*1000,'after_raw_mm':after*1000,'turn_deg':float(np.linalg.norm(best)*180/math.pi)})
 vec=np.array(vectors);mag=np.linalg.norm(vec,axis=1);dilated=vec.copy()
 for i in range(len(vec)):
  j=max(range(max(0,i-2),min(len(vec),i+3)),key=lambda k:mag[k]);dilated[i]=vec[j]
 kernel=np.exp(-.5*(np.arange(-3,4)/1.25)**2);kernel/=kernel.sum();pad=np.pad(dilated,((3,3),(0,0)),mode='edge');smooth=np.array([np.sum(pad[i:i+7]*kernel[:,None],axis=0) for i in range(len(vec))])
 snaps=[]
 for f,vector in enumerate(smooth):
  action(act);sc.frame_set(f);snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};action(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update();angle=np.linalg.norm(vector)
  if angle>1e-8:
   H=armik.W(rig,'B_R_Hand');q=Quaternion(Vector(vector/angle),angle);armik.set_world(rig,'B_R_Hand',armik.rot_world(H,q.to_matrix()@H.to_3x3()))
  snaps.append(rig.pose.bones['B_R_Hand'].rotation_quaternion.copy())
 import action_curves
 action_curves.remove_rotations(act,['B_R_Hand','B_R_ForearmTwist'])
 action(act)
 for f,q in enumerate(snaps):
  if f and q.dot(snaps[f-1])<0:q=-q
  rig.pose.bones['B_R_Hand'].rotation_quaternion=q;rig.pose.bones['B_R_Hand'].keyframe_insert('rotation_quaternion',frame=f)
 # Re-bake the existing twist helper without redistributing its already fitted weights.
 previous=None
 for f in range(N+1):
  sc.frame_set(f);fb=rig.data.bones['B_R_Forearm'];hb=rig.data.bones['B_R_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones['B_R_Forearm'].matrix.inverted()@rig.pose.bones['B_R_Hand'].matrix).to_quaternion();rest=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();dq=rel@rest.inverted();angle=2*math.atan2(Vector((dq.x,dq.y,dq.z)).dot(axis),dq.w);angle=(angle+math.pi)%(2*math.pi)-math.pi
  if previous is not None:angle+=2*math.pi*round((previous-angle)/(2*math.pi))
  previous=angle;pb=rig.pose.bones['B_R_ForearmTwist'];pb.rotation_quaternion=Quaternion(axis,angle*.6);pb.keyframe_insert('rotation_quaternion',frame=f)
 action(None);ledger[name]=rows;print('CLUB_CLEAR',name,'raw max turn',max(r['turn_deg'] for r in rows),'contact frames',sum(r['before_mm']<0 for r in rows),flush=True)
(p/'work/club_clearance_full.json').write_text(json.dumps(ledger,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'))
