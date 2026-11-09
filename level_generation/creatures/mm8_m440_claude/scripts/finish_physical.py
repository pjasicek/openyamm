from pathlib import Path
import bpy,sys,math,numpy as np
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik,action_curves
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_repaired.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;me=body.data
co=np.array([tuple(v.co) for v in me.vertices]);parts=np.array([a.value for a in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(co),len(names)))
for v in me.vertices:
 for e in v.groups:W[v.index,e.group]=e.weight
skin=(parts==0)&(co[:,2]>.95);bad=[i for i,n in enumerate(names) if n=='B_Pelvis' or any(t in n for t in ('Thigh','Calf','Foot','Toe'))]
removed=W[np.ix_(np.flatnonzero(skin),bad)].sum(1);W[np.ix_(np.flatnonzero(skin),bad)]=0;W[np.flatnonzero(skin),names.index('B_Spine2')]+=removed
# Remove stray lower-body influence and smooth the axillary blend over the connected skin.
ids=np.flatnonzero(skin & (abs(co[:,0])>.20)&(abs(co[:,0])<.40)&(co[:,2]<1.34));neigh=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if parts[a]==0 and parts[b]==0:neigh[a].append(b);neigh[b].append(a)
for _ in range(8):
 old=W.copy()
 for i in ids:
  if neigh[i]:W[i]=old[i]*.5+old[neigh[i]].mean(0)*.5
for i in np.flatnonzero(skin):
 w=W[i];top=np.argsort(w)[-4:];top=top[w[top]>1e-6];assert len(top);total=w[top].sum()
 for e in list(me.vertices[int(i)].groups):body.vertex_groups[e.group].remove([int(i)])
 for j in top:body.vertex_groups[int(j)].add([int(i)],float(w[j]/total),'REPLACE')
feet={s:np.flatnonzero(parts==k) for s,k in [('L',4),('R',5)]};soles={s:ix[co[ix,2]<co[ix,2].min()+.005] for s,ix in feet.items()}
def act(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def points():
 bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();x=np.array([tuple(v.co) for v in m.vertices]);ev.to_mesh_clear();return x
for name in ('Running','Walking'):
 a=bpy.data.actions[name];N=int(a.frame_range[1]);frames=[]
 for i in range(N*2+1):
  f=i/2;act(a);sc.frame_set(int(f),subframe=f-int(f));snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};act(None)
  for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
  bpy.context.view_layer.update()
  if name=='Running':
   H=armik.W(rig,'B_L_Hand');target=H.translation+Vector((.012,-.008,0));armik.solve(rig,'L',target,hand_rot=H.to_3x3())
   x=points();low={s:float(x[ix,2].min()) for s,ix in feet.items()}
   for side in 'LR':
    # Bare-foot support: level only the planted foot; preserve the source heel kick in flight.
    g=max(0,min(1,(.06-low[side])/.05));ix=soles[side];normal=Vector(np.linalg.svd(x[ix]-x[ix].mean(0))[2][-1]);normal=normal if normal.z>0 else -normal
    q=normal.rotation_difference(Vector((0,0,1)));q=__import__('mathutils').Quaternion().slerp(q,g);F=armik.W(rig,f'B_{side}_Foot');armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,q.to_matrix()@F.to_3x3()))
    x=points();ys=co[ix,1];d=x[ix[ys<=np.quantile(ys,.3)]].mean(0)-x[ix[ys>=np.quantile(ys,.7)]].mean(0)
    if g>.95:
     yaw=math.atan2(d[0],-d[1]);want=math.radians(8 if side=='L' else -8);delta=(want-yaw+math.pi)%(2*math.pi)-math.pi;F=armik.W(rig,f'B_{side}_Foot');armik.set_world(rig,f'B_{side}_Foot',armik.rot_world(F,Matrix.Rotation(delta,3,'Z')@F.to_3x3()))
  x=points();low=min(x[ix,2].min() for ix in feet.values());M=armik.W(rig,'B_Pelvis');M.translation.z+=.004-float(low);armik.set_world(rig,'B_Pelvis',M);frames.append({b.name:b.matrix_basis.copy() for b in rig.pose.bones})
 frames[-1]=frames[0];act(a);prev={}
 for i,snap in enumerate(frames):
  for n,m in snap.items():
   b=rig.pose.bones[n];q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=i/2)
   if n=='B_Pelvis':b.location=m.translation;b.keyframe_insert('location',frame=i/2)
 action_curves.continuous(a)
act(None);bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_repaired.blend'));print('PHYSICAL skin weights and bare-foot support corrected')
