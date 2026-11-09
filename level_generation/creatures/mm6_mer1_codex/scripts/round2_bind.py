"""Bind the regenerated surface to the retained source-frame rig; no previous body vertices/weights are used."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction_master.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
for o in list(bpy.data.objects):
 if o.name not in ('Rig','ClubMesh'):bpy.data.objects.remove(o,do_unlink=True)
with bpy.data.libraries.load(str(P/'work/round2/raw_body.blend'),link=False)as(src,dst):dst.objects=['Body']
body=dst.objects[0];bpy.context.collection.objects.link(body)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_round2_rig/result_rigged_character_glb_url.glb'))
new=set(bpy.data.objects)-before;ma=next(o for o in new if o.type=='ARMATURE');mm=max((o for o in new if o.type=='MESH'),key=lambda o:len(o.data.vertices))
co=np.array([tuple(v.co)for v in body.data.vertices]);mc=np.array([tuple(mm.matrix_world@v.co)for v in mm.data.vertices])
cen=lambda a:np.array([(a[:,0].min()+a[:,0].max())/2,(a[:,1].min()+a[:,1].max())/2,a[:,2].min()])
scale=np.ptp(co[:,2])/np.ptp(mc[:,2]);shift=cen(co)-cen(mc)*scale;mc=mc*scale+shift
mj={b.name:np.array(ma.matrix_world@b.head_local)*scale+shift for b in ma.data.bones}
mapping={'Hips':'B_Pelvis','Spine02':'B_Spine','Spine01':'B_Spine1','Spine':'B_Spine2','neck':'B_Neck','Head':'B_Head','head_end':'B_Head','headfront':'B_Head'}
for side,sd in [('Left','L'),('Right','R')]:
 for mn,bn in [('Shoulder','Clavicle'),('Arm','UpperArm'),('ForeArm','Forearm'),('Hand','Hand'),('UpLeg','Thigh'),('Leg','Calf'),('Foot','Foot'),('ToeBase','Toe0')]:mapping[side+mn]=f'B_{sd}_{bn}'
J={mapping[n]:v for n,v in mj.items()if n in mapping and n not in ('head_end','headfront')}
rawparts=np.array([v.value for v in body.data.attributes['piece'].data])
bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table()
for sd,pid in [('L',4),('R',5)]:
 vs={v.index for e in bm.edges if e.is_boundary for v in e.verts if rawparts[v.index]==pid}
 J[f'B_{sd}_Hand']=co[sorted(vs)].mean(0)
cuffids={v.index for e in bm.edges if e.is_boundary for v in e.verts if rawparts[v.index]==2 and abs(v.co.x)>.35 and v.co.z<1.1}
bm.free()
(P/'work/round2/meshy_joints.json').write_text(json.dumps({n:p.tolist()for n,p in J.items()},indent=2))
# Minimal segment swing from the fresh estimate to the existing rig's rest stance.
children={'B_Pelvis':'B_Spine','B_Spine':'B_Spine1','B_Spine1':'B_Spine2','B_Spine2':'B_Neck','B_Neck':'B_Head'}
for sd in 'LR':
 for a,b in [('Clavicle','UpperArm'),('UpperArm','Forearm'),('Forearm','Hand'),('Thigh','Calf'),('Calf','Foot'),('Foot','Toe0')]:children[f'B_{sd}_{a}']=f'B_{sd}_{b}'
target={n:np.array(rig.data.bones[n].head_local)for n in J};A={}
for n in J:
 if n in children:
  u=J[children[n]]-J[n];v=target[children[n]]-target[n];d=u/np.linalg.norm(u)
  q=Vector(u).rotation_difference(Vector(v));A[n]=np.array(q.to_matrix())@(np.eye(3)+(np.linalg.norm(v)/np.linalg.norm(u)-1)*np.outer(d,d))
 else:A[n]=A.get(n.replace('Hand','Forearm'),np.eye(3))
for sd in 'LR':A[f'B_{sd}_Hand']=A[f'B_{sd}_Forearm'].copy()
rawparts=np.array([v.value for v in body.data.attributes['piece'].data]);kd=KDTree(len(mc))
for i,c in enumerate(mc):kd.insert(c,i)
kd.balance();gn={g.index:g.name for g in mm.vertex_groups};W=[];errors=[]
for i,c in enumerate(co):
 _,j,dist=kd.find(c);errors.append(dist);w={}
 for g in mm.data.vertices[j].groups:
  n=mapping.get(gn[g.group])
  if n:w[n]=w.get(n,0)+g.weight
 part=int(rawparts[i]);sd='L'if c[0]>0 else'R'
 if part in [0,6,9,10,11,12,13]:w={'B_Head':1}
 elif part in [7,8,14,15,16,17,18,19]:w={'B_Pelvis':1}
 elif part in [4,5]:w={f'B_{sd}_Hand':1}
 elif part==2:
  w={n:x for n,x in w.items()if n in ['B_Pelvis','B_Spine','B_Spine1','B_Spine2'] or n in [f'B_{sd}_{z}'for z in ['Clavicle','UpperArm','Forearm','Hand']]}
  if not w:w={'B_Spine2':1}
  # No foreign arm influence on the belly; preserve a wide, smooth armpit transition.
  keep=float(max(np.clip((abs(c[0])-.24)/.10,0,1),np.clip((c[2]-1.12)/.18,0,1)*np.clip((abs(c[0])-.12)/.13,0,1)))
  if abs(c[0])<.34:
   for n in list(w):
    if 'Arm'in n or 'Clavicle'in n:
     x=w[n]*(1-keep);w[n]-=x;w['B_Spine2']=w.get('B_Spine2',0)+x
 elif part==1:
  w={n:x for n,x in w.items()if any(k in n for k in ['Pelvis','Thigh','Calf','Foot','Toe0'])}
  if not w:w={f'B_{sd}_Calf':1}
 if not w:w={'B_Pelvis':1}
 total=sum(w.values());W.append({n:x/total for n,x in w.items()})
# Diffuse only the continuous shirt field over its actual edges, before deformation.
names=list(J);mat=np.array([[w.get(n,0)for n in names]for w in W]);adj=[[]for _ in co]
for e in body.data.edges:
 a,b=e.vertices
 if rawparts[a]==rawparts[b]==2:adj[a].append(b);adj[b].append(a)
for _ in range(5):
 old=mat.copy()
 for i,nb in enumerate(adj):
  if nb and co[i,2]>1.1:mat[i]=old[i]*.55+old[nb].mean(0)*.45
W=[{n:float(x)for n,x in zip(names,row)if x>1e-7}for row in mat]
for i,c in enumerate(co):
 if rawparts[i]!=2:continue
 sd='L'if c[0]>0 else'R';wr=J[f'B_{sd}_Hand'];d=wr-J[f'B_{sd}_Forearm'];d/=np.linalg.norm(d);t=float(np.clip(((c-wr)@d+.045)/.04,0,1)) if abs(c[0])>.35 else 0.
 if i in cuffids:t=1.
 if t:W[i]={**{n:v*(1-t) for n,v in W[i].items() if n!=f'B_{sd}_Hand'},f'B_{sd}_Hand':W[i].get(f'B_{sd}_Hand',0)*(1-t)+t}
# Repose only upper limbs into the retained rest rig; preserve torso/head/legs and garment silhouette.
for i,v in enumerate(body.data.vertices):
 c=co[i];part=int(rawparts[i])
 if part in [2,4,5]:
  transformed=sum(((target[n]+A[n]@(c-J[n])) if any(k in n for k in ['Arm','Hand','Clavicle']) else c)*x for n,x in W[i].items())
  # Axial translations are small and applied to garment uniformly; no cutting or arm-root patch.
  v.co=transformed
body.vertex_groups.clear()
for b in rig.data.bones:body.vertex_groups.new(name=b.name)
def put(i,w):
 total=sum(w.values())
 if not total:raise RuntimeError(('No weights',i))
 for n,x in w.items():
  if x>1e-7:body.vertex_groups[n].add([i],float(x/total),'REPLACE')
# Cloth is authored directly over the fresh skirt, with smooth angular/vertical interpolation.
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
newco=np.array([tuple(v.co)for v in body.data.vertices])
for i,v in enumerate(body.data.vertices):
 part=int(rawparts[i]);x,y,z=v.co;sd='L'if x>0 else'R';w=W[i]
 if part==3:
  a=(math.atan2(x,y-.015)%(2*math.pi))/(2*math.pi)*16;j=int(a);f=a-j;anchor=smooth((z-.79)/.05);w={'B_Pelvis':anchor}
  t=float(np.clip((.84-z)/.5*4,0,3.999));k=int(t);r=t-k
  for chain,share in [(j,1-f),((j+1)%16,f)]:
   cw={k:1.}
   if r<.4 and k>0:cw={k-1:.5*(1-r/.4),k:.5+.5*r/.4}
   elif r>.6 and k<3:cw={k:1-.5*(r-.6)/.4,k+1:.5*(r-.6)/.4}
   for kk,g in cw.items():w[f'Cloak_{chain}_{kk}']=g*share*(1-anchor)
 elif part in [4,5]:w={f'B_{sd}_Hand':1}
 elif part==1:
  if z<.17:w={f'B_{sd}_Foot':1}
  elif z<.33:
   t=smooth((z-.17)/.16);w={f'B_{sd}_Foot':1-t,f'B_{sd}_Calf':t}
 elif part==2:
  a=rig.data.bones[f'B_{sd}_Forearm'].head_local;b=rig.data.bones[f'B_{sd}_Hand'].head_local;d=(b-a).normalized();handshare=max(w.get(f'B_{sd}_Hand',0),smooth(((v.co-b).dot(d)+.045)/.055) if abs(v.co.x)>.3 else 0.)
  w={n:g*(1-handshare)for n,g in w.items()};w[f'B_{sd}_Hand']=handshare
  for segment,child,helper in [('UpperArm','Forearm','UpperArmTwist'),('Forearm','Hand','ForearmTwist')]:
   n=f'B_{sd}_{segment}';a=rig.data.bones[n].head_local;b=rig.data.bones[f'B_{sd}_{child}'].head_local;d=b-a;t=(v.co-a).dot(d)/d.length_squared
   share=smooth((t-.12)/.72)*(.85 if segment=='Forearm'else .6)
   amount=w.get(n,0)*share;w[n]=w.get(n,0)-amount;w[f'B_{sd}_{helper}']=amount
 put(i,w)
# Semantic labels retain pipeline compatibility without separating the continuous garment.
semantic={0:0,2:1,3:2,4:3,5:4,6:11,7:10,8:12,9:14,10:15,11:0,12:0,13:0,14:17,15:13,16:13,17:13,18:13,19:16}
for i,a in enumerate(body.data.attributes['piece'].data):
 a.value=semantic.get(int(rawparts[i]),6 if newco[i,0]>0 else 7)
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
for o in new:bpy.data.objects.remove(o,do_unlink=True)
for a in list(bpy.data.actions):
 if a.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:bpy.data.actions.remove(a)
for f in body.data.polygons:f.use_smooth=True
# Neutral clay materials make arm structure visible before texture.
colors={0:(.64,.43,.3,1),1:(.07,.25,.10,1),2:(.07,.25,.10,1),3:(.64,.43,.3,1),4:(.64,.43,.3,1),6:(.19,.10,.04,1),7:(.19,.10,.04,1),10:(.44,.3,.13,1),11:(.045,.045,.045,1),12:(.055,.035,.025,1),13:(.12,.07,.03,1),14:(.55,.55,.4,1),15:(.55,.55,.4,1),16:(.2,.1,.05,1),17:(.35,.35,.32,1)}
body.data.materials.clear()
for j in range(18):
 m=bpy.data.materials.new(f'Round2_clay_{j}');m.diffuse_color=colors.get(j,(.2,.2,.2,1));body.data.materials.append(m)
pv=[a.value for a in body.data.attributes['piece'].data]
for f in body.data.polygons:f.material_index=pv[f.vertices[0]]
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/bound_body.blend'))
common.workbench_clay(bpy.context.scene)
for role,t in [('Standing',0),('Attack',.65),('Death',1.4),('Dead',0),('Running',.2)]:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];f=t*30;bpy.context.scene.frame_set(int(f),subframe=f%1)
 common.render_views(str(P/'review/round2'/('bound_'+role)),.85,2.2,views=('front','left','three_quarter'),resolution=(600,900))
(P/'review/round2/binding_method.json').write_text(json.dumps({'body_source':'meshy/body_round2_smart/model_urls_glb.glb','weights_source':'meshy/body_round2_rig/result_rigged_character_glb_url.glb','method':'Fresh Meshy weights mapped to retained source-frame rig; continuous-shirt graph smoothing, anatomical exclusions, local rest-stance fit, new cloth/twist fields. No previous body geometry or skin weights reused.','nearest_raw_vertex_max_mm':max(errors)*1000,'raw_to_rest_joint_estimates':{n:v.tolist()for n,v in J.items()}},indent=2))
