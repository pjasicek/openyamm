"""Fit finger curls using the shared evaluator's exact weighted hand samples across all LODs."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));C.activate('Attack',42/48);r=bpy.data.objects['Rig'];G=json.loads((P/'work/round3_left_before_multilod.json').read_text());q0={n:Quaternion(q)for n,q in G['finger_local'].items()};H=np.array(r.pose.bones['B_L_Hand'].matrix);invH=np.linalg.inv(H);rest={b.name:b.matrix_local.copy()for b in r.data.bones};parents={b.name:b.parent.name if b.parent else None for b in r.data.bones};basepose={b.name:b.matrix.copy()for b in r.pose.bones};axis=np.array(G['handle_axis_hand_local']);axis/=np.linalg.norm(axis);centre=np.array(G['handle_centre_hand_local']);palm=np.array(json.loads((P/'gates.json').read_text())['hands']['L']['palm_axis']);origin=(sum((np.array(r.pose.bones[f'B_L_Finger{i}'].head)for i in range(5)))/5+H[:3,3])/2;origin=(invH@np.r_[origin,1])[:3]
glb=S.Glb(P/'export/mm6_natm.glb');cfg=json.loads((P/'gates.json').read_text());pose=glb.rest.copy()
for n,m in basepose.items():
 if n in glb.names:pose[glb.names[n]]=np.array(m)
centre=(invH@np.array(r.pose.bones['Spear'].matrix)@np.array([0,0,-.16,1]))[:3];axis=(invH@np.array(r.pose.bones['Spear'].matrix))[:3,2];axis/=np.linalg.norm(axis);G['handle_axis_hand_local']=axis.tolist();prop=S.load_props(cfg,P,glb,S.Report(cfg))[0];to_prop=S.C@np.linalg.inv(pose[glb.names['Spear']])@H
centre_reference=centre.copy();centre=np.array(G['handle_centre_hand_local']);centre[1]-=.006;centre[2]-=.007
samples=[]
for mesh in S.load_meshes(glb):
 if 'shadow'in mesh.label:continue
 S.configure_mesh(mesh,cfg,S.Report(cfg));tri,bary,groups,digest=S.grip_points(mesh,'L',cfg);ids=np.unique(tri);mapping=np.full(len(mesh.vertices),-1);mapping[ids]=np.arange(len(ids));samples.append((mesh.vertices[ids],mesh.joints[ids],mesh.weights[ids],mesh.skin_nodes,mesh.bind,mapping[tri],bary,groups))
chains=[];axes=[];spread=[]
for f in [0,1,2,3,4]:
 ch=[f'B_L_Finger{f}',f'B_L_Finger{f}1',f'B_L_Finger{f}2']if f else['B_L_Finger0','B_L_Finger01','B_L_Finger02'];chains.append(ch);aa=[]
 for n in ch:
  b=basepose[parents[n]]@rest[parents[n]].inverted()@rest[n];aa.append((b.to_3x3().inverted()@Vector(H[:3,:3]@axis)).normalized())
 axes.append(aa);fd=(basepose[ch[1]].translation-basepose[ch[0]].translation).normalized();pn=Vector(H[:3,:3]@axis).cross(fd).normalized();b=basepose[parents[ch[0]]]@rest[parents[ch[0]]].inverted()@rest[ch[0]];spread.append((b.to_3x3().inverted()@pn).normalized())
u=palm-axis*np.dot(axis,palm);u/=np.linalg.norm(u);v=np.cross(axis,u);parameter=np.zeros(22)
def evaluate(x,report=False):
 qs={};world={};po=pose.copy()
 for f,ch in enumerate(chains):
  for j,n in enumerate(ch):qs[n]=Quaternion(axes[f][j],math.radians(x[f*4+j]))@q0[n]
  qs[ch[0]]=Quaternion(spread[f],math.radians(x[f*4+3]))@qs[ch[0]]
 for n in q0:
  parent=parents[n];world[n]=(world[parent]if parent in world else basepose[parent])@rest[parent].inverted()@rest[n]@qs[n].to_matrix().to_4x4();po[glb.names[n]]=np.array(world[n])
 cc=centre+x[20]*u+x[21]*v;rows=[];cost=0
 for level,(vertices,joints,weights,nodes,bind,tris,bary,groups)in enumerate(samples):
  mats=po[nodes]@bind;pts=np.zeros_like(vertices)
  for k in range(weights.shape[1]):
   m=mats[joints[:,k]];pts+=(np.einsum('nij,nj->ni',m[:,:3,:3],vertices)+m[:,:3,3])*weights[:,k,None]
  pts=S.transform(invH,pts);points=np.einsum('sk,tkj->tsj',bary,pts[tris]).reshape(-1,3);local=S.transform(to_prop,points-(cc-centre_reference));surface=prop['grip_surfaces']['L'][level];gaps=[surface.gap(local[group])for group in groups];signed,_=prop['solid_surfaces'][level].signed(local);depth=max(0.,-signed.min());rows.append({'gaps_mm':(np.array(gaps)*1000).tolist(),'depth_mm':depth*1000})
  if level==0:cost+=1e7*float(np.maximum(-signed-.0015,0)@np.maximum(-signed-.0015,0))+1e7*sum(max(0,gap-.0015)**2 for gap in gaps)
 angle=math.degrees(math.acos(np.clip(np.dot(palm,cc-origin)/np.linalg.norm(palm)/np.linalg.norm(cc-origin),-1,1)));cost+=max(0,angle-58)**2+1e-5*float(x[:20]@x[:20])+100*float(x[20:]@x[20:])
 return (cost,qs,cc,rows,angle)if report else cost
best=evaluate(parameter);print('EXACT_GRIP_START',evaluate(parameter,True)[3:],flush=True)
for step in [8,4,2,1,.3]:
 for sweep in range(10):
  changed=False
  for j in range(22):
   for sign in [-1,1]:
    y=parameter.copy();y[j]+=sign*(step if j<20 else step*.00025)
    if (j<20 and abs(y[j])>65)or(j>=20 and abs(y[j])>.009):continue
    val=evaluate(y)
    if val<best-1e-9:best=val;parameter=y;changed=True
  if not changed:break
 print('EXACT_GRIP_STEP',step,best,evaluate(parameter,True)[3:],flush=True)
cost,qs,cc,rows,angle=evaluate(parameter,True);G['finger_local']={n:list(q)for n,q in qs.items()};G['handle_centre_hand_local']=cc.tolist();(P/'work/round3_left_grip.json').write_text(json.dumps(G,indent=2));(P/'review/round3_near_grip_authoring.json').write_text(json.dumps({'cost':cost,'parameters':parameter.tolist(),'shared_contact_objective_by_lod':rows,'palm_axis_angle':angle,'centre':cc.tolist(),'method':__doc__},indent=2))
