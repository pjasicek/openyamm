"""Smooth continuous skin fields and deterministic, leg-driven garment envelopes."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/master.blend'));body=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];s=bpy.context.scene;pv=np.array([v.value for v in body.data.attributes['piece'].data]);co=np.array([v.co[:]for v in body.data.vertices]);gn=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(gn)))
for v in body.data.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
adj=[[]for _ in co]
for e in body.data.edges:
 a,b=e.vertices
 if pv[a]==pv[b]==1:adj[a].append(b);adj[b].append(a)
for _ in range(24):
 old=W.copy()
 for i,nb in enumerate(adj):
  if nb and abs(co[i,0])>.16 and co[i,2]>.97:W[i]=.65*old[i]+.35*old[nb].mean(0)
for v in body.data.vertices:
 if pv[v.index]!=1:continue
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 ids=np.argsort(W[v.index])[-4:];total=W[v.index,ids].sum()
 for gi in ids:
  if W[v.index,gi]>1e-7:body.vertex_groups[int(gi)].add([v.index],float(W[v.index,gi]/total),'REPLACE')
def activate(a):r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
def frame(f):s.frame_set(int(f),subframe=f%1)
# Loose relaxed fingers keep the jogging hand away from the cuff.
a=bpy.data.actions['Running'];activate(a)
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 frame(f)
 for sd in 'LR':
  for b in r.pose.bones:
   if b.name.startswith(f'B_{sd}_Finger'):b.rotation_quaternion=Quaternion();b.keyframe_insert('rotation_quaternion',frame=float(f))
 b=r.pose.bones['B_L_UpperArm'];M=b.matrix.copy();Q=Quaternion((0,-1,0),math.radians(5));h=M.translation.copy();M=Q.to_matrix().to_4x4()@M;M.translation=h;b.matrix=M;b.keyframe_insert('rotation_quaternion',frame=float(f))
# Fidget remains the selected examine clip, with a quieter free arm around the relaxed native pose.
activate(bpy.data.actions['Standing']);frame(0);idle={b.name:b.rotation_quaternion.copy()for b in r.pose.bones};a=bpy.data.actions['Fidget'];activate(a)
for f in np.arange(0,float(a.frame_range[1])+.001,.25):
 frame(f)
 for n in ['B_L_UpperArm','B_L_Forearm','B_L_Hand']:
  b=r.pose.bones[n];b.rotation_quaternion=idle[n].slerp(b.rotation_quaternion,.4);b.keyframe_insert('rotation_quaternion',frame=float(f))
# Build leg envelope parameters in the pelvis-rest frame, retaining full hidden leg geometry.
pr=r.data.bones['B_Pelvis'].matrix_local.copy();levels=[.84,.715,.59,.465,.34];restpts=np.array([json.loads(s['merchant_skirt'])[i]['pts']for i in range(16)]);legids=np.where(np.isin(pv,[6,7]))[0];records={}
for role in ['Standing','Walking','Running','Fidget','Hit','Attack','Death']:
 a=bpy.data.actions[role];activate(a);end=float(a.frame_range[1]);fs=np.arange(0,end+.001,.25);data=[];pels=[]
 for f in fs:
  frame(f);pel=r.pose.bones['B_Pelvis'].matrix.copy();pels.append(pel);M=pr@pel.inverted();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();legs=np.array([M@me.vertices[int(i)].co for i in legids]);ev.to_mesh_clear();row=[]
  for k,z in enumerate(levels):
   near=legs[abs(legs[:,2]-z)<.1];cx,cy=0.,.015;rx=max(abs(restpts[:,k,0]))+.025;ry=max(abs(restpts[:,k,1]-.015))+.025
   if len(near) and k:
    center=(near[:,:2].min(0)+near[:,:2].max(0))/2;cx,cy=center
    need=np.sqrt(((near[:,0]-cx)/rx)**2+((near[:,1]-cy)/ry)**2).max();rx*=max(1.,need+.05);ry*=max(1.,need+.05)
   row.append([cx,cy,rx,ry])
  data.append(row)
 data=np.array(data);params=[]
 for i,f in enumerate(fs):
  dt=fs-f
  if role in ['Standing','Walking','Running','Fidget']:dt=(dt+end/2)%end-end/2
  w=np.exp(-.5*(dt/3.)**2);w[abs(dt)>9]=0;v=np.einsum('f,fkj->kj',w,data)/w.sum();v[:,2:]=np.maximum(v[:,2:],data[i,:,2:]);params.append(v)
 # Remove every old cloth channel before writing the new smooth chain poses.
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in list(cb.fcurves):
     if 'Cloak_'in fc.data_path:cb.fcurves.remove(fc)
 prev={}
 for f,pel,par in zip(fs,pels,params):
  frame(f);M=pel@pr.inverted()
  for i in range(16):
   ang=i*2*math.pi/16;pts=[M@Vector((v[0]+math.sin(ang)*v[2],v[1]+math.cos(ang)*v[3],z))for v,z in zip(par,levels)]
   for k in range(4):
    n=f'Cloak_{i}_{k}';b=r.pose.bones[n];rest=r.data.bones[n];d=pts[k+1]-pts[k];q=(rest.tail_local-rest.head_local).rotation_difference(d);T=q.to_matrix().to_4x4()@rest.matrix_local;T.translation=pts[k];b.matrix=T;bpy.context.view_layer.update();q=b.rotation_quaternion.copy()
    if n in prev and q.dot(prev[n])<0:q=-q
    prev[n]=q;b.rotation_quaternion=q
    for field in ['rotation_quaternion','location']:b.keyframe_insert(field,frame=float(f))
 records[role]={'frames':len(fs),'radius_max_m':float(np.max(np.array(params)[:,:,2:])),'sigma_s':.1}
 print('ENVELOPE',role,records[role],flush=True)
activate(bpy.data.actions['Death']);frame(float(r.animation_data.action.frame_range[1]));terminal={b.name:b.matrix_basis.copy()for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in [0,30]:
 for b in r.pose.bones:
  b.matrix_basis=terminal[b.name]
  for field in ['location','rotation_quaternion','scale']:b.keyframe_insert(field,frame=f)
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2/master.blend'));(P/'review/round2/cloth_envelope.json').write_text(json.dumps(records,indent=2))
