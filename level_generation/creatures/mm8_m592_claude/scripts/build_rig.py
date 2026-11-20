"""Fitted source-frame rig, measured three-claw hands, mirrored Meshy weights and isolated jaw."""
from pathlib import Path
import bpy,json,math,numpy as np,sys
from mathutils import Matrix,Vector,Quaternion
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
S=json.loads((P/'work/source_rest.json').read_text());jr=json.loads((P/'work/joints_final.json').read_text());J={k:Vector(v) for k,v in jr['joints'].items()};F=json.loads((P/'work/claws_fit.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));body=bpy.data.objects['Body'];co=np.array([tuple(v.co) for v in body.data.vertices]);pv=np.array([v.value for v in body.data.attributes['piece'].data])
mapping={'B_'+n:n for n in J};order=[]
def visit(n):
 if n not in mapping:return
 order.append(n)
 for c,v in S.items():
  if v['parent']==n:visit(c)
visit('B_Pelvis');assert len(order)==22
heads={n:J[mapping[n]] for n in order};rots={};swings={};parents={n:S[n]['parent'] if S[n]['parent'] in mapping else None for n in order}
def basis(forward,across):
 f=Vector(forward).normalized();t=Vector(across);t=(t-f*t.dot(f)).normalized();return Matrix((t,f,t.cross(f))).transposed()
for n in order:
 c=S[n]['child'];Rs=Matrix(S[n]['rot'])
 if c in heads:q=Vector(S[n]['seg']).rotation_difference(heads[c]-heads[n])
 else:q=swings.get(parents[n],Quaternion())
 if n in ('B_Pelvis','B_Head'):q=Quaternion()
 if n.endswith('_Hand'):
  side=n[2];kn=[Vector(x['base']) for x in F[side]];f=sum(kn,Vector())/3-heads[n];t=kn[0]-kn[2]
  fs=Vector(S[f'B_{side}_Finger2']['head'])-Vector(S[n]['head']);ts=Vector(S[f'B_{side}_Finger1']['head'])-Vector(S[f'B_{side}_Finger4']['head'])
  q=(basis(f,t)@basis(fs,ts).transposed()).to_quaternion()
 swings[n]=q;rots[n]=q.to_matrix()@Rs
for side in ('R','L'):
 across=Vector(F[side][0]['base'])-Vector(F[side][2]['base'])
 for f in F[side]:
  n=f['name'];order.append(n);heads[n]=Vector(f['base']);rots[n]=basis(f['direction'],across);parents[n]=f'B_{side}_Hand'
order.append('Jaw');heads['Jaw']=Vector((0,-.345,1.215));rots['Jaw']=Matrix.Identity(3);parents['Jaw']='B_Head'
ad=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',ad);bpy.context.scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n in order:
 b=ad.edit_bones.new(n);b.head=heads[n];c=S[n]['child'] if n in S else None;length=(heads[c]-heads[n]).length if c in heads else .08
 if 'Finger' in n:length=.16
 b.tail=b.head+rots[n].col[1]*max(length,.025);b.align_roll(rots[n].col[2])
for n in order:
 if parents[n]:ad.edit_bones[n].parent=ad.edit_bones[parents[n]]
bpy.ops.object.mode_set(mode='OBJECT')
err=max(min(q.angle,2*math.pi-q.angle) for q in [ad.bones[n].matrix_local.to_quaternion().rotation_difference(rots[n].to_quaternion()) for n in order]);assert err<.001
for pb in rig.pose.bones:pb.rotation_mode='QUATERNION'
def imported(path):
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(path));return set(bpy.data.objects)-before
temp=imported(P/'work/body_for_rig.glb');asym=max((o for o in temp if o.type=='MESH'),key=lambda x:len(x.data.vertices));ac=np.array([tuple(asym.matrix_world@v.co) for v in asym.data.vertices])
for o in temp:bpy.data.objects.remove(o,do_unlink=True)
temp=imported(P/'meshy/rig_v1/result_rigged_character_glb_url.glb');src=max((o for o in temp if o.type=='MESH'),key=lambda x:len(x.data.vertices));sc=np.array([tuple(src.matrix_world@v.co) for v in src.data.vertices])
centre=lambda c:np.array([(c[:,0].min()+c[:,0].max())/2,(c[:,1].min()+c[:,1].max())/2,c[:,2].min()])
scale=np.ptp(ac[:,2])/np.ptp(sc[:,2]);sc=sc*scale+centre(ac)-centre(sc)*scale
kd=KDTree(len(sc))
for i,c in enumerate(sc):kd.insert(c,i)
kd.balance();query=co.copy();query[:,0]=-abs(query[:,0])+jr['symmetry_plane_before_centre'];hits=[kd.find(c) for c in query];distance=np.array([h[2] for h in hits]);assert np.percentile(distance,99)<.015
mp={'Hips':'B_Pelvis','Spine02':'B_Spine','Spine01':'B_Spine1','Spine':'B_Spine2','neck':'B_Neck','Head':'B_Head','head_end':'B_Head','headfront':'B_Head'}
for label,side in [('Left','L'),('Right','R')]:
 for a,b in [('Shoulder','Clavicle'),('Arm','UpperArm'),('ForeArm','Forearm'),('Hand','Hand'),('UpLeg','Thigh'),('Leg','Calf'),('Foot','Foot'),('ToeBase','Foot')]:mp[label+a]='B_'+side+'_'+b
gn={g.index:mp.get(g.name) for g in src.vertex_groups};W=[]
for i,hit in enumerate(hits):
 w={}
 for ge in src.data.vertices[hit[1]].groups:
  n=gn[ge.group]
  if not n or ge.weight<1e-6:continue
  if co[i,0]>0:n=n.replace('B_R_','B_L_')
  else:n=n.replace('B_L_','B_R_')
  w[n]=w.get(n,0)+ge.weight
 W.append(w)
for o in temp:bpy.data.objects.remove(o,do_unlink=True)
def mix(i,target,t):
 t=float(np.clip(t,0,1));W[i]={n:w*(1-t) for n,w in W[i].items()};W[i][target]=W[i].get(target,0)+t
for i,c in enumerate(co):
 # Keep the central chest and the low forward head independent of raised shoulders.
 if abs(c[0])<.36:
  for n in list(W[i]):
   if any(s in n for s in ('UpperArm','Forearm','Hand','Clavicle')):
    t=float(np.clip((.36-abs(c[0]))/.12,0,1));v=W[i][n]*t;W[i][n]-=v;W[i]['B_Spine2']=W[i].get('B_Spine2',0)+v
 head=abs(c[0])<.22 and c[1]<-.29 and c[2]>1.055
 if head or pv[i]==2:W[i]={'B_Head':1.0}
 if c[2]<.135 and abs(c[0])<.50:W[i]={'B_L_Foot' if c[0]>0 else 'B_R_Foot':1.0}
 if head:
  jaw=(c[2]<1.155 and c[1]<-.36) or (abs(c[0])>.072 and c[1]<-.48 and c[2]<1.255)
  if jaw:W[i]={'Jaw':1.0}
for side,sgn in [('R',-1),('L',1)]:
 wr=np.array(J[side+'_Hand']);forward=np.mean([f['base'] for f in F[side]],axis=0)-wr;forward/=np.linalg.norm(forward)
 ids=np.flatnonzero((sgn*co[:,0]>.44)&(np.linalg.norm(co-wr,axis=1)<.65)&(co[:,2]<wr[2]+.08))
 for i in ids:mix(int(i),f'B_{side}_Hand',((co[i]-wr)@forward+.025)/.065)
 for f in F[side]:
  base=np.array(f['base']);owned=set(f['vertices']);near=set(owned)
  for _ in range(3):
   new=set()
   for e in body.data.edges:
    a,b=e.vertices
    for v,u in ((a,b),(b,a)):
     if v in near and u not in near and np.linalg.norm(co[u]-base)<.065:new.add(int(u))
   near.update(new)
  for i in near:
   t=float(np.clip((base[2]+.025-co[i,2])/.065,0,1))
   if i not in owned:t*=.35
   W[i]={f'B_{side}_Hand':1-t,f['name']:t}
# Smooth the mouth walls and cheeks between rigid upper teeth and the entire lower dental arch.
head_region=(abs(co[:,0])<.22)&(co[:,1]<-.285)&(co[:,2]>1.04)
jaw_fixed=head_region&(((co[:,2]<1.195)&(co[:,1]<-.445))|((co[:,2]<1.18)&(co[:,1]<-.42))|((abs(co[:,0])>.072)&(co[:,1]<-.48)&(co[:,2]<1.255)))
head_fixed=head_region&((co[:,2]>1.265)|((co[:,2]>1.205)&(abs(co[:,0])<.072)&(co[:,1]<-.475)))
cuts=json.loads((P/'work/dental_cuts.json').read_text());dental=next(c for c in cuts if c['x']==.14 and c['y']==-.43)
for component in dental['components']:
 ids=component['vertices'];upper=component['upper_roots']>0;lower=component['lower_roots']>0
 assert upper!=lower,('Ambiguous dental component',component['count'])
 jaw_fixed[ids]=lower;head_fixed[ids]=upper
jw=np.array([w.get('Jaw',0) for w in W]);jw[jaw_fixed]=1;jw[head_fixed]=0
adj=[[] for _ in co]
for e in body.data.edges:
 a,b=e.vertices;adj[a].append(b);adj[b].append(a)
free=np.flatnonzero(head_region&~jaw_fixed&~head_fixed)
for _ in range(40):
 nxt=jw.copy()
 for i in free:
  if adj[i]:nxt[i]=.45*jw[i]+.55*float(np.mean(jw[adj[i]]))
 jw=nxt
for i in np.flatnonzero(head_region):W[int(i)]={'B_Head':1-float(jw[i]),'Jaw':float(jw[i])}
body.vertex_groups.clear();groups={n:body.vertex_groups.new(name=n) for n in order}
for i,w in enumerate(W):
 w=sorted(((n,v) for n,v in w.items() if v>1e-6),key=lambda x:-x[1])[:4];total=sum(v for n,v in w);assert total>0
 for n,v in w:groups[n].add([i],v/total,'REPLACE')
body.parent=rig;mod=body.modifiers.new('Armature','ARMATURE');mod.object=rig
scene=bpy.context.scene;scene.render.fps=30;scene['rig_offsets']=json.dumps({n:{'q':list(swings[n]),'R_src':S[n]['rot']} for n in swings});scene['guardian_claws']=json.dumps(F)
scene['guardian_jaw']='Lower jaw/beard and outer lower tusks only; upper muzzle/upper fangs excluded; visual isolation gate follows.'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_v1.blend'))
report={'bones':len(order),'source_frame_error_degrees':math.degrees(err),'weights_transfer_p99_mm':float(np.percentile(distance,99)*1000),'weights_transfer_max_mm':float(distance.max()*1000),'claw_branches':{s:[len(f['vertices']) for f in F[s]] for s in F},'rigid_claw_edges_pending_probe':True,'jaw_pending_probe':True}
(P/'review/geometry/rig_build.json').write_text(json.dumps(report,indent=2)+'\n');print('RIG_BUILD',report,flush=True)
