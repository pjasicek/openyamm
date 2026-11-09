import sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(Path('level_generation/creatures/claude_shared/gates').resolve()));import run_gates as g
config=json.load(open(p/'pilot.gates.json'));body=g.Glb(p/'export/pilot_body.glb');mesh=g.load_meshes(body)[0];report=g.Report(config);g.configure_mesh(mesh,config,report);props=g.load_props(config,p,body,report);prop=props[0]
for clip,t,side in [('Walking',.7291666666666666,'R'),('Standing',2.,'L')]:
 anim=next(a for n,a,_,_ in body.clips() if n==clip);pose=body.pose(anim,np.array([t]))[0];points=mesh.posed(pose);tris,bary,groups,_=g.grip_points(mesh,side,config)
 world=np.einsum('sk,tkj->tsj',bary,points[tris]).reshape(-1,3);M=pose[body.names['Socket_Sword']];local=g.transform(g.C@np.linalg.inv(M),world);surface=prop['solid_surfaces'][0];dist,face=surface.signed(local);i=int(np.argmin(dist));v=local[i]
 print('BAD_GRIP',clip,side,'closed',surface.closed,'point',v.tolist(),'depth_mm',-dist[i]*1000,'bounds',surface.lo,surface.hi,'face',face[i],flush=True)
 hit=surface.tree.find_nearest(Vector(v));print('NEAREST',list(hit[0]),list(hit[1]),hit[3],flush=True)
 for d in [(1,0,0),(0,1,0),(0,0,1),(.811107,.357913,.463187),(-.811107,-.357913,-.463187)]:
  print('EXACT_INSIDE',d,surface.exact_inside(v,np.array(d)),flush=True)
source=g.Glb(Path('anim_library/humanoid_set/2Hand Sword.glb'));selected=json.load(open(p/'creature_3d_progress.json'))['motion_study']['clips'];out={}
for role,clip in selected.items():
 name,anim,start,end=next(row for row in source.clips() if row[0].endswith(clip));times=g.sample_grid(start,end,48);pose=source.pose(anim,times);data={}
 for label,terms in [('arms',('UpperArm','Forearm','Clavicle')),('hands',('Hand','Finger')),('head',('Head','Neck')),('feet',('Foot','Toe'))]:
  nodes=[i for n,i in source.names.items() if n.startswith('B_') and any(term in n for term in terms)];R=pose[:,nodes,:3,:3];R/=np.linalg.norm(R,axis=-2,keepdims=True)
  dt=np.diff(times);v=g.rotation_vector(R[1:]@R[:-1].swapaxes(-1,-2))/dt[:,None,None]
  step=np.linalg.norm(v,axis=-1)*dt[:,None]*180/np.pi;acc=np.linalg.norm(np.diff(v,axis=0),axis=-1)/((dt[1:]+dt[:-1])/2)[:,None]*180/np.pi
  data[label]=float(step.max());data[label+'_acceleration']=float(acc.max())
 out[role]=data;print('SOURCE_MOTION',role,data,flush=True)
json.dump(out,open(p/'work/source_motion_limits.json','w'),indent=2)
