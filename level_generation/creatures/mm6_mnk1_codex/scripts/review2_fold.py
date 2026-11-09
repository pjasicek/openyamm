"""Review 2: tapered cloth cuffs with rounded hems and metric UVs."""
import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
HAND_Y=0;HAND_Z=0;HAND_NORMAL=0
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'review_round1/before/work/animation_finish.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;B=r.data.bones
# The generated palms were oversized; fit mesh and finger joints together, retaining the anatomical wrists.
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for sd,pi in [('L',2),('R',3)]:
 wrist=r.data.edit_bones[f'B_{sd}_Hand'].head.copy()
 for eb in r.data.edit_bones:
  if eb.name.startswith(f'B_{sd}_Finger'):eb.head=wrist+(eb.head-wrist)*.80;eb.tail=wrist+(eb.tail-wrist)*.80
 for v in body.data.vertices:
  if body.data.attributes['piece'].data[v.index].value==pi:v.co=wrist+(v.co-wrist)*.80
bpy.ops.object.mode_set(mode='OBJECT')
names=[b.name for b in B]
def update():bpy.context.view_layer.update()
def setact(a):
 r.animation_data.action=a
 if a:r.animation_data.action_slot=a.slots[0]
def capture():return {n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in names}
def apply(pose):
 setact(None)
 for n,(q,l) in pose.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].location=l
 update()
def worldrot(n,q):
 pb=r.pose.bones[n];m=q.to_matrix().to_4x4();m.translation=pb.head;pb.matrix=m;update()
def aim(n,child,target):
 pb=r.pose.bones[n];rest=B[child].head_local-B[n].head_local
 carry=pb.parent.matrix.to_3x3()@B[n].parent.matrix_local.to_3x3().inverted() if pb.parent else Matrix.Identity(3)
 ref=carry@B[n].matrix_local.to_3x3()
 worldrot(n,(carry@rest).rotation_difference(Vector(target)-pb.head)@ref.to_quaternion())
def fold():
 shoulders={s:r.pose.bones[f'B_{s}_UpperArm'].head.copy() for s in ['L','R']};centre=(shoulders['L']+shoulders['R'])/2
 wrists={};elbows={}
 for s,sign in [('L',1),('R',-1)]:
  c,u,f,h=[f'B_{s}_{n}' for n in ['Clavicle','UpperArm','Forearm','Hand']]
  el=centre+Vector((sign*.195,-.23,-.185));elbows[s]=el
  L=(B[h].head_local-B[f].head_local).length;w=el-Vector((sign,0,0))*L;wrists[s]=w
  sh=r.pose.bones[c].head.copy();l1=(B[u].head_local-B[c].head_local).length;l2=(B[f].head_local-B[u].head_local).length
  delta=el-sh;d=delta.length;e=delta.normalized();a=(l1*l1-l2*l2+d*d)/(2*d);v=shoulders[s]-sh;v=(v-e*v.dot(e)).normalized();shoulder=sh+e*a+v*math.sqrt(max(0,l1*l1-a*a))
  aim(c,u,shoulder);aim(u,f,el);aim(f,h,w)
 for s,other in [('L','R'),('R','L')]:
  h=f'B_{s}_Hand';rf=(B[f'B_{s}_Finger2'].head_local-B[h].head_local).normalized();rn=rf.cross(B[f'B_{s}_Finger1'].head_local-B[f'B_{s}_Finger4'].head_local).normalized()
  if rn.y>0:rn=-rn
  rt=rn.cross(rf).normalized();rn=rf.cross(rt).normalized();sign=1 if s=='L' else -1;df=(elbows[other]-wrists[s]+Vector((0,sign*HAND_Y,-.04+sign*HAND_Z))).normalized();dn=Vector((0,0,-1));dt=dn.cross(df).normalized();dn=df.cross(dt).normalized()
  src=Matrix((rf,rt,rn)).transposed();dst=Matrix((df,dt,dn)).transposed();worldrot(h,(dst@src.transposed()).to_quaternion()@B[h].matrix_local.to_quaternion())
  for j in range(1,5):
   root=f'B_{s}_Finger{j}'
   for n,ch,angle in [(root,root+'1',50),(root+'1',root+'2',115)]:
    v=df*math.cos(math.radians(angle))+dn*math.sin(math.radians(angle));aim(n,ch,r.pose.bones[n].head+v)
   # The last phalanx follows its parent's bend, retaining the fitted terminal joint.
   n=root+'2';tip=Vector(json.loads((p/'work/finger_joints.json').read_text())[s][n+'_tip']);w=B[h].head_local;tip=w+(tip-w)*.80;restvec=tip-B[n].head_local;pb=r.pose.bones[n];carry=pb.parent.matrix.to_3x3()@B[n].parent.matrix_local.to_3x3().inverted();desired=df*math.cos(math.radians(170))+dn*math.sin(math.radians(170));worldrot(n,(carry@restvec).rotation_difference(desired)@(carry@B[n].matrix_local.to_3x3()).to_quaternion())
  for base in ['UpperArm','Forearm']:r.pose.bones[f'B_{s}_{base}Twist'].rotation_quaternion=Quaternion()
 update()
 return wrists,elbows
setact(bpy.data.actions['Standing']);scene.frame_set(0);base=capture();apply(base)
# A woven cuff follows the forearm, not the wrist articulation inside it.
me=body.data;piece=np.array([v.value for v in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices]);gn=[g.name for g in body.vertex_groups]
for s,sign in [('L',1),('R',-1)]:
 a=np.array(B[f'B_{s}_Forearm'].head_local);w=np.array(B[f'B_{s}_Hand'].head_local);d=w-a;t=(co-a)@d/(d@d)
 for v in me.vertices:
  if piece[v.index]!=0 or sign*(v.co.x+.006)<.20:continue
  old={gn[g.group]:g.weight for g in v.groups};arm=[n for n in old if n.startswith(f'B_{s}_') and any(k in n for k in ['Forearm','Hand','Finger'])]
  amount=sum(old[n] for n in arm)
  for n in arm:body.vertex_groups[n].remove([v.index])
  if amount:body.vertex_groups[f'B_{s}_Forearm'].add([v.index],amount,'ADD')
  rigid=float(np.clip((t[v.index]-.05)/.30,0,1))
  if rigid:
   for g in list(v.groups):body.vertex_groups[g.group].add([v.index],g.weight*(1-rigid),'REPLACE')
   body.vertex_groups[f'B_{s}_Forearm'].add([v.index],rigid,'ADD')
  # Restore some of the original cuff fullness while keeping the generated folds and UVs.
  u=float(np.clip((t[v.index]+.05)/.45,0,1));axis=a+d*t[v.index];v.co=axis+(co[v.index]-axis)*(1+0*u)
for n in names:
 if 'Finger' in n:r.pose.bones[n].rotation_quaternion=Quaternion().slerp(base[n][0],.4)
W=np.zeros((len(me.vertices),len(gn)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
adj=[[] for v in me.vertices]
for e in me.edges:
 a,z=e.vertices;adj[a].append(z);adj[z].append(a)
region=(piece==0)&(abs(co[:,0]+.006)>.075)&(abs(co[:,0]+.006)<.255)&(co[:,2]>1.14)&(co[:,2]<1.43)
for iteration in range(20):
 new=W.copy()
 for i in np.where(region)[0]:new[i]=.5*W[i]+.5*W[adj[i]].mean(0)
 W=new
for i in np.where(region)[0]:
 carry=float(np.clip((abs(co[i,0]+.006)-.10)/.05,0,1))*float(np.clip((co[i,2]-1.13)/.07,0,1))
 amount=W[i,gn.index('B_Spine')]*carry;W[i,gn.index('B_Spine')]-=amount;W[i,gn.index('B_Spine2')]+=amount
 keep=np.argsort(W[i])[-8:];weights=W[i,keep];weights/=weights.sum()
 for g in list(me.vertices[i].groups):body.vertex_groups[g.group].remove([int(i)])
 for gi,weight in zip(keep,weights):
  if weight>1e-6:body.vertex_groups[int(gi)].add([int(i)],float(weight),'REPLACE')
wrists,elbows=fold()
# Replace the generated sealed cuff ends with open, lined hems on the existing sleeve cut loops.
import bmesh
u0=1771/2048;u1=1835/2048;v0=1-636/2048;v1=1-572/2048
tile=lambda x:1-abs(x%2-1)
cloth_faces=[]
bm=bmesh.new();bm.from_mesh(me);pl=bm.verts.layers.int['piece'];uv=bm.loops.layers.uv['UVMap'];deform=bm.verts.layers.deform.verify();cuff_layer=bm.faces.layers.int.new('cuff');added=[]
for sd,sign in [('L',1),('R',-1)]:
 a=B[f'B_{sd}_Forearm'].head_local.copy();d=B[f'B_{sd}_Hand'].head_local-a;axis=d.normalized();cut=a+d*.10
 verts=[v for v in bm.verts if v[pl]==0];edges=[e for e in bm.edges if all(v[pl]==0 for v in e.verts)];faces=[f for f in bm.faces if all(v[pl]==0 for v in f.verts)]
 result=bmesh.ops.bisect_plane(bm,geom=verts+edges+faces,plane_co=cut,plane_no=axis,clear_outer=True,dist=.000001)
 edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and len(e.link_faces)==1]
 assert edges
 # One ordered cuff boundary; follow original winding and retain its original cut-loop coordinates.
 adj={}
 for e in edges:
  x,y=e.verts;adj.setdefault(x,[]).append(y);adj.setdefault(y,[]).append(x)
 assert all(len(v)==2 for v in adj.values())
 start=next(iter(adj));ring=[start];previous=None;current=start
 while True:
  nxt=next(v for v in adj[current] if v is not previous)
  if nxt==start:break
  ring.append(nxt);previous,current=current,nxt
 assert len(ring)==len(adj)
 rotation=r.pose.bones[f'B_{sd}_Forearm'].matrix.to_3x3()@B[f'B_{sd}_Forearm'].matrix_local.to_3x3().inverted();inverse=rotation.inverted();along=rotation@axis;depth=along.cross(Vector((0,0,1))).normalized()
 theta=[]
 for v in ring:
  radial=rotation@(v.co-cut);theta.append(math.atan2(radial.z,radial.dot(depth)))
 # Ensure the generated quads agree with the source surface at the shared cut edge.
 edge=next(e for e in edges if ring[0] in e.verts and ring[1] in e.verts);loop=next(l for l in edge.link_faces[0].loops if l.edge==edge)
 if loop.vert==ring[0]:ring.reverse();theta.reverse()
 N=len(ring);plane=np.array([[(rotation@(v.co-cut)).dot(depth),(rotation@(v.co-cut)).z] for v in ring]);mean=plane.mean(0);angle=math.atan2(plane[0,1]-mean[1],plane[0,0]-mean[0]);area=np.sum(plane[:,0]*np.roll(plane[:,1],-1)-np.roll(plane[:,0],-1)*plane[:,1]);theta=[angle+(1 if area>0 else -1)*math.tau*k/N for k in range(N)]
 # A clean proximal cut keeps the original elbow cloth connected to the tapered cuff.
 for v,angle in zip(ring,theta):
  radial=depth*(.064*math.cos(angle))+Vector((0,0,.085*math.sin(angle)-.016))
  v.co=a+d*.10+inverse@radial;v[deform].clear();v[deform][body.vertex_groups[f'B_{sd}_Forearm'].index]=1
 rings=[ring]
 profile=[(.18,.078,.087),(.28,.075,.086),
          (.38,.073,.084),(.47,.072,.086),(.60,.073,.088),(.71,.070,.086),
          (.84,.078,.091),(.97,.083,.097),(1.10,.089,.102),(1.17,.087,.101),
          (1.19,.084,.098),(1.17,.081,.095),(1.06,.077,.090),(.60,.066,.080),(.12,.035,.046)]
 for j,(t,ry,rz) in enumerate(profile,1):
  if sd=='L' and t>.80:ry+=.006;rz+=.006
  new=[]
  for angle in theta:
   # Shallow oblique gathers and a wavy sewn lip avoid a lathed, rigid pipe silhouette.
   wave=.0035*math.sin(3*angle+5*t)+.002*math.sin(7*angle-3*t)
   lip=.010*math.cos(angle+.4)*max(0,(t-.8)/.39)
   radial=depth*((ry+wave)*math.cos(angle))+Vector((0,0,(rz+wave)*math.sin(angle)-.016))
   radial+=Vector((0,(-.016 if sd=='L' else .012)*max(0,min(1,(t-.25)/.85)),0))
   v=bm.verts.new(a+d*(t+lip)+inverse@radial);v[pl]=0;v[deform][body.vertex_groups[f'B_{sd}_Forearm'].index]=1;new.append(v)
  old=rings[-1]
  for k in range(N):
   f=bm.faces.new((old[k],old[(k+1)%N],new[(k+1)%N],new[k]));f.smooth=True;f[cuff_layer]=1 if j<=10 else 2;cloth_faces.append(f)
   # Metric UVs are assigned after the final triangulation, using a woven atlas patch.
   for loop,(uu,vv) in zip(f.loops,[(tile(k/4),(j-1)%2),(tile((k+1)/4),(j-1)%2),(tile((k+1)/4),j%2),(tile(k/4),j%2)]):loop[uv].uv=(u0+(u1-u0)*uu,v0+(v1-v0)*vv)
  rings.append(new)
 added.append({'side':sd,'cut_ring_vertices':N,'new_quad_faces':N*len(profile)})
# Remove the redundant generated forearm stumps beneath the cuff; retain the wrist seam inside the cloth.
for sd,pi in [('L',2),('R',3)]:
 wrist=B[f'B_{sd}_Hand'].head_local;direction=(B[f'B_{sd}_Finger2'].head_local-wrist).normalized();verts=[v for v in bm.verts if v[pl]==pi];edges=[e for e in bm.edges if all(v[pl]==pi for v in e.verts)];faces=[f for f in bm.faces if all(v[pl]==pi for v in f.verts)]
 result=bmesh.ops.bisect_plane(bm,geom=verts+edges+faces,plane_co=wrist-direction*.006,plane_no=direction,clear_inner=True,dist=.000001)
 # A narrow cloth lining reaches the anatomical wrist inside the broad outer sleeve.
 cut_edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and len(e.link_faces)==1]
 adj={}
 for edge in cut_edges:
  a,z=edge.verts;adj.setdefault(a,[]).append(z);adj.setdefault(z,[]).append(a)
 assert adj and all(len(v)==2 for v in adj.values())
 start=next(iter(adj));skinring=[start];previous=None;current=start
 while True:
  nxt=next(v for v in adj[current] if v is not previous)
  if nxt==start:break
  skinring.append(nxt);previous,current=current,nxt
 assert len(skinring)==len(adj)
 center=sum((v.co for v in skinring),Vector())/len(skinring);elbow=B[f'B_{sd}_Forearm'].head_local;axis=(wrist-elbow).normalized();gi=body.vertex_groups[f'B_{sd}_Forearm'].index;lining=[];M=len(skinring)
 for t in [.10,.60,1.0]:
  ring=[]
  for old in skinring:
   radial=old.co-center
   if t==1:
    co=center+radial*1.12+direction*.009;weights=dict(old[deform])
   else:
    radial=radial-axis*radial.dot(axis);co=elbow+(wrist-elbow)*t+radial.normalized()*.040;weights={gi:1.0}
   v=bm.verts.new(co);v[pl]=0
   for group,weight in weights.items():v[deform][group]=weight
   ring.append(v)
  lining.append(ring)
 for j in range(2):
  for k in range(M):
   face=bm.faces.new((lining[j][k],lining[j][(k+1)%M],lining[j+1][(k+1)%M],lining[j+1][k]));face.smooth=True;face[cuff_layer]=2;cloth_faces.append(face)
   for loop,(u,v) in zip(face.loops,[(tile(k/4),j%2),(tile((k+1)/4),j%2),(tile((k+1)/4),(j+1)%2),(tile(k/4),(j+1)%2)]):loop[uv].uv=(u0+(u1-u0)*u,v0+(v1-v0)*v)

# Seed valid UVs; review2_uv.py supplies the final continuous cloth mapping.
# The atlas is densely packed; reuse this measured cloth patch rather than resample the whole body atlas.
for fi,face in enumerate(cloth_faces):
 origin=face.verts[0].co;ex=(face.verts[1].co-origin).normalized()
 normal=(face.verts[1].co-origin).cross(face.verts[-1].co-origin).normalized();ey=normal.cross(ex).normalized()
 coords=np.array([[(v.co-origin).dot(ex),(v.co-origin).dot(ey)] for v in face.verts])*617
 span=np.ptp(coords,axis=0)
 if max(span)>60:
  # Hidden lining spans longer than the reusable atlas island; retain density along the exposed exterior.
  coords*=60/max(span)
 coords-=coords.mean(0);offset=np.array([1804,1302])
 for loop,co2 in zip(face.loops,coords):loop[uv].uv=((offset[0]+co2[0])/2048,1-(offset[1]+co2[1])/2048)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
(p/'work/review2_cuffs.json').write_text(json.dumps({'open_cuffs':added,'cloth_patch_uv':[u0,v0,u1,v1],'hand_scale':.80},indent=2))
# Keep the covered pose as one coherent arm configuration carried by the chest.
folded=capture();fold_c=(wrists['L']+wrists['R'])/2;fold_spine=r.pose.bones['B_Spine2'].matrix.to_quaternion().copy();fold_forearms={sd:r.pose.bones[f'B_{sd}_Forearm'].matrix.to_quaternion().copy() for sd in ['L','R']}
def death_fold(frame):
 # Let the folded forearms support the fallen body; retain source boot contacts with fixed-length leg IK.
 ankles={sd:r.pose.bones[f'B_{sd}_Foot'].head.copy() for sd in ['L','R']};footq={sd:r.pose.bones[f'B_{sd}_Foot'].matrix.to_quaternion().copy() for sd in ['L','R']}
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();pv=[v.value for v in me.attributes['piece'].data];low=min(v.co.z for v in mesh.vertices if pv[v.index]!=1);ev.to_mesh_clear()
 lift=max(0,.001-low)
 if not lift:return
 root=r.pose.bones['B_Pelvis'];m=root.matrix.copy();m.translation.z+=lift;root.matrix=m;update()
 for sd in ['L','R']:
  un,fn,hn=[f'B_{sd}_{k}' for k in ['Thigh','Calf','Foot']];sh=r.pose.bones[un].head.copy();target=ankles[sd];pole=r.pose.bones[fn].head.copy();l1=(B[fn].head_local-B[un].head_local).length;l2=(B[hn].head_local-B[fn].head_local).length
  delta=target-sh;d=min(delta.length,l1+l2-.001);direction=delta.normalized();target=sh+direction*d;a=(l1*l1-l2*l2+d*d)/(2*d);v=pole-sh;v=(v-direction*v.dot(direction)).normalized();el=sh+direction*a+v*math.sqrt(max(0,l1*l1-a*a))
  aim(un,fn,el);aim(fn,hn,target);worldrot(hn,footq[sd])
 update()
arm_names=[n for n in names if n.startswith(('B_L_','B_R_')) and any(k in n for k in ['Clavicle','UpperArm','Forearm','Hand','Finger'])]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
for act in list(bpy.data.actions):
 if act.name not in ['Standing','Walking','Running','Fidget','Hit','Attack','Cast','Death','Dead']:continue
 affected=arm_names+(['B_Pelvis','B_L_Thigh','B_L_Calf','B_L_Foot','B_R_Thigh','B_R_Calf','B_R_Foot'] if act.name in ['Death','Dead'] else [])
 setact(act);end=float(act.frame_range[1]);cached=[]
 for frame in np.arange(0,end+.01,.5):
  scene.frame_set(int(frame),subframe=float(frame%1));cached.append((float(frame),capture()))
 anchors=dict(cached)
 rows=[]
 for frame,old in cached:
  u=0
  if act.name=='Attack':u=smooth((frame-8)/8)*smooth((end-frame)/10)
  elif act.name=='Cast':u=smooth(frame/8)*smooth((end-frame)/9)
  target={n:(folded[n][0].slerp(old[n][0],u*u if any(k in n for k in ['Hand','Finger']) else u),old[n][1]) for n in arm_names}
  # Fixed boundary quaternions avoid switching shortest arcs as a moving source wrist passes 180 degrees.
  if act.name in ['Attack','Cast']:
   start,ready,back=(8,16,end-10) if act.name=='Attack' else (0,8,end-9)
   for n in arm_names:
    if not any(k in n for k in ['Hand','Finger']):continue
    q=old[n][0]
    if frame<ready:q=folded[n][0].slerp(anchors[ready][n][0],smooth((frame-start)/(ready-start))**(1 if act.name=='Attack' and 'Finger' in n else 2))
    elif frame>back:q=folded[n][0].slerp(anchors[back][n][0],smooth((end-frame)/(end-back))**(1 if act.name=='Attack' and 'Finger' in n else 2))
    target[n]=(q,old[n][1])
  if (act.name in ['Attack','Cast'] and frame>end-10) or (act.name=='Attack' and 8<frame<16) or (act.name=='Cast' and 0<frame<8):
   apply({**old,**target});un,fn,hn=['B_L_'+k for k in ['UpperArm','Forearm','Hand']];sh=r.pose.bones[un].head.copy();wrist=r.pose.bones[hn].head.copy();palm=r.pose.bones[hn].matrix.to_quaternion().copy();pole=r.pose.bones[fn].head.copy();wrist.z+=.18*math.sin(math.pi*((frame-8)/8 if act.name=='Attack' and frame<16 else frame/8 if act.name=='Cast' and frame<8 else (end-frame)/10))
   l1=(B[fn].head_local-B[un].head_local).length;l2=(B[hn].head_local-B[fn].head_local).length;delta=wrist-sh;distance=min(delta.length,l1+l2-.001);direction=delta.normalized();wrist=sh+direction*distance;a=(l1*l1-l2*l2+distance*distance)/(2*distance);v=pole-sh;v=(v-direction*v.dot(direction)).normalized();el=sh+direction*a+v*math.sqrt(max(0,l1*l1-a*a))
   aim(un,fn,el);aim(fn,hn,wrist);worldrot(hn,palm);pose=capture();target={n:pose[n] for n in affected}
  if act.name in ['Death','Dead']:
   apply(old);apply({**old,**target});death_fold(frame if act.name=='Death' else 60);pose=capture();target={n:pose[n] for n in affected}
  rows.append((frame,target))
 # Clear old arm curves, leaving the validated torso, feet and robe bake unchanged.
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in list(cb.fcurves):
     if any('"'+n+'"' in fc.data_path for n in affected):cb.fcurves.remove(fc)
 setact(act);previous={}
 for frame,pose in rows:
  for n,(q,l) in pose.items():
   if n in previous and q.dot(previous[n])<0:q.negate()
   previous[n]=q.copy();pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=frame)
   if n=='B_Pelvis':pb.location=l;pb.keyframe_insert('location',frame=frame)
 for layer in act.layers:
  for st in layer.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 print('CORRECTED',act.name,len(rows))
setact(bpy.data.actions['Standing']);scene.frame_set(0)
# Preview the actual UV layout used by the exporter.
me.uv_layers.active=me.uv_layers['UVMap']
common.workbench_clay(scene);common.render_views(str(p/'review/round2/fold_probe'),1.2,1.05,views=('front','left','three_quarter','back'),resolution=(700,700))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
(p/'work/review2_fold.json').write_text(json.dumps({'affected_bones':arm_names,'wrist_targets':{s:list(w) for s,w in wrists.items()},'elbow_targets':{s:list(e) for s,e in elbows.items()},'rest_actions':['Standing','Walking','Running','Fidget','Hit','Death','Dead'],'attack_unchanged_frames':[16,28],'cast_unchanged_frames':[8,float(bpy.data.actions['Cast'].frame_range[1])-9],'geometry':'Open lined cuffs connected to original cut loops. Hands and finger joints permanently fitted to 80 percent; no animated visibility or scale tricks.'},indent=2))
