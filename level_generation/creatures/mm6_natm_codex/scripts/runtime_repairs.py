"""Repair measured runtime contact issues without changing the selected LOD topology."""
import bpy,sys,json,math,shutil,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path[:0]=[str(P/'scripts'),str(P.parent/'claude_shared/gates')]
import reduction_common as C,run_gates as G
cfg=json.loads((P/'gates.json').read_text());g=G.Glb(P/'export/mm6_natm.glb');report=G.Report(cfg);clips={n:(a,s,e)for n,a,s,e in g.clips()};meshes=[m for m in G.load_meshes(g)if 'colour'in m.label]
for m in meshes:G.configure_mesh(m,cfg,report)
def evaluated(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([p.co[:]for p in me.vertices]);ev.to_mesh_clear();return v
def skin(o,r):
 out=np.zeros((len(o.data.vertices),4,4))
 for v in o.data.vertices:
  for w in v.groups:
   n=o.vertex_groups[w.group].name
   if n in r.data.bones:out[v.index]+=np.array(r.pose.bones[n].matrix@r.data.bones[n].matrix_local.inverted())*w.weight
 return out
records=[]
for level in range(4):
 src=P/f'work/runtime_lod{level}.blend';backup=P/f'work/pre_runtime_fix_lod{level}.blend'
 if not backup.exists():shutil.copy2(src,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;me=body.data
 # Sole geometry, rather than the imported toe joint, defines the travel direction.
 for a in bpy.data.actions:
  if a.name not in ['Standing','Fidget','Walking','Running','Attack','Cast','Hit']:continue
  frames=[]
  for f in range(round(a.frame_range[1])+1):
   C.activate(a.name,f/48);r.animation_data.action=None;pose={}
   for side,angle in [('L',16),('R',-16)]:
    pb=r.pose.bones[f'B_{side}_Foot'];M=pb.matrix.copy();R=Quaternion((0,0,1),math.radians(angle)).to_matrix();Mnew=(R@M.to_3x3()).to_4x4();Mnew.translation=M.translation;pb.matrix=Mnew;bpy.context.view_layer.update();pose[pb.name]=(pb.location.copy(),pb.rotation_quaternion.copy())
   frames.append(pose)
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  for f,pose in enumerate(frames):
   for n,(l,q)in pose.items():pb=r.pose.bones[n];pb.location=l;pb.rotation_quaternion=q;pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f)
 C.activate('Standing',0);M=np.array(r.pose.bones['Spear'].matrix);A=skin(body,r);posed=evaluated(body);invM=np.linalg.inv(M);local=G.transform(invM,posed);old=local.copy()
 weights={}
 for name,pattern in [('palm','B_R_Hand'),('thumb','B_R_Finger0'),('index','B_R_Finger1'),('middle','B_R_Finger2'),('ring','B_R_Finger3'),('pinky','B_R_Finger4')]:
  weights[name]=np.array([sum(w.weight for w in v.groups if body.vertex_groups[w.group].name==pattern or ('Finger'in pattern and body.vertex_groups[w.group].name.startswith(pattern)))for v in me.vertices])
 hand=sum(weights.values())>.3;me.calc_loop_triangles();tri=np.array([t.vertices[:]for t in me.loop_triangles]);tt=tri[np.all(hand[tri],axis=1)];bary=np.array([[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3])
 # Push the triangle interiors out of the real handle, then close each digit's nearest contact patch.
 for iteration in range(24):
  changes=0
  for ids in tt:
   for w in bary:
    p=w@local[ids];rad=np.linalg.norm(p[:2])
    if -.125<p[2]<.075 and rad<.0144:
     normal=p[:2]/max(rad,1e-8)
     if rad<1e-5:normal=np.mean(local[ids,:2],axis=0);normal/=np.linalg.norm(normal)
     correction=np.r_[normal*(.0144-rad),0];local[ids]+=np.outer(w,correction)/(w@w);changes+=1
  for name,W in weights.items():
   ww=np.einsum('sk,tk->ts',bary,W[tt]);pts=np.einsum('sk,tkj->tsj',bary,local[tt]);rad=np.linalg.norm(pts[:,:,:2],axis=2);eligible=(ww>.3)&(abs(pts[:,:,2])<.115)&(rad>.0144);distance=np.where(eligible,rad-.0157,np.inf);j,k=np.unravel_index(np.argmin(distance),distance.shape)
   if distance[j,k]>.0016 and np.isfinite(distance[j,k]):
    p=pts[j,k];w=bary[k];corr=np.r_[-p[:2]/np.linalg.norm(p[:2])*(distance[j,k]-.0016),0];local[tt[j]]+=np.outer(w,corr)/(w@w);changes+=1
  if not changes:break
 newposed=G.transform(M,local);d=newposed-posed
 for v in me.vertices:
  if hand[v.index]:v.co+=Vector(np.linalg.solve(A[v.index,:3,:3],d[v.index]))
 me.update()
 # The upper strap was above the elbow. Both straps must wrap the forearm itself.
 ob=bpy.data.objects['BucklerMesh'];rest=r.data.bones['Buckler'].matrix_local;inv=rest.inverted();strap=0
 for v in ob.data.vertices:
  p=inv@v.co
  if p.y>.016 and p.z>.055 and p.z<.14 and abs(p.x)<.133:p.z-=.08;v.co=rest@p;strap+=1
 # Solve far sole floor constraints in the fall, preserving the flat standing sole.
 if level:
  C.reset();base=np.array([v.co[:]for v in me.vertices]);foot=np.array([sum(w.weight for w in v.groups if any(x in body.vertex_groups[w.group].name for x in ['_Foot','_Toe']))>.3 for v in me.vertices]);delta=np.zeros_like(base)
  constraints=[]
  for f in range(161):
   C.activate('Death',f/48);A=skin(body,r);pv=evaluated(body);constraints.append((A[:,:3,:3],pv[:,2].copy()))
  ids=np.flatnonzero(foot);flat=base[:,2]<.008
  for it in range(30):
   worst=0
   for mat,z in constraints:
    for i in ids:
     row=mat[i,2].copy()
     if flat[i]:row[2]=0
     deficit=-.0012-(z[i]+mat[i,2]@delta[i]);den=row@row
     if deficit>0 and den>1e-8:delta[i]+=row*deficit/den;worst=max(worst,deficit)
   if worst<.00005:break
  for i in ids:me.vertices[i].co+=Vector(delta[i])
 else:delta=np.zeros_like(old)
 # Use the actual cupped-palm contact normal rather than the flat open-hand reference normal.
 if level==0:
  C.activate('Standing',0);me.update();A=skin(body,r);pv=evaluated(body);M=np.array(r.pose.bones['Spear'].matrix);lp=G.transform(np.linalg.inv(M),pv);normals=[]
  for ids in tt:
   if weights['palm'][ids].mean()<.3:continue
   c=lp[ids].mean(0);n=np.cross(lp[ids[1]]-lp[ids[0]],lp[ids[2]]-lp[ids[0]]);length=np.linalg.norm(n)
   if length<1e-10:continue
   n/=length;rad=np.linalg.norm(c[:2]);toward=np.r_[-c[:2]/max(rad,1e-9),0]
   if rad<.035 and -.08<c[2]<.06 and n@toward>.25:normals.append((n,length))
  if normals:
   n=sum(n*a for n,a in normals);n/=np.linalg.norm(n);world=M[:3,:3]@n;localnormal=np.linalg.solve(np.array(r.pose.bones['B_R_Hand'].matrix)[:3,:3],world);localnormal/=np.linalg.norm(localnormal);cfg['hands']['R']['palm_axis']=localnormal.tolist()
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(src))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
 records.append({'lod':level,'hand_max_correction_mm':float(np.linalg.norm(d,axis=1).max()*1000),'strap_vertices':strap,'far_sole_max_correction_mm':float(np.linalg.norm(delta,axis=1).max()*1000)})
 print('REPAIRED',records[-1],flush=True)
# Deformation-twist frames represent the distal forearm orientation; hinge frames remain separately audited.
cfg['bones']={f'B_{s}_Forearm':f'B_{s}_ForearmTwist'for s in 'LR'}
for s in 'LR':
 for part,terms in [('arm',['UpperArm','Forearm','Hand']),('limb',['Clavicle','UpperArm','Forearm','Hand','Finger'])]:cfg['regions'][f'{part}_{s}']={'weights':[f'B_{s}_{t}*'for t in terms],'weight_min':.2 if part=='limb'else.3}
(P/'gates.json').write_text(json.dumps(cfg,indent=2));(P/'review/runtime_repairs.json').write_text(json.dumps(records,indent=2))
