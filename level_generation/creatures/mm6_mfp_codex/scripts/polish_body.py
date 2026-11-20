import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix,kdtree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
co=np.array([v.co[:]for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);gn={g.index:g.name for g in b.vertex_groups};W=np.zeros((len(co),len(gn)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
# Spatial smoothing across short shoulder edges removes discontinuous automatic skin weights.
ids=np.flatnonzero((pv==0)&(co[:,2]>1.14)&(co[:,2]<1.4));tree=kdtree.KDTree(len(ids))
for i in ids:tree.insert(Vector(co[i]),int(i))
tree.balance();old=W.copy()
for i in ids:
 near=tree.find_range(Vector(co[i]),.035);ix=np.array([q[1]for q in near]);ds=np.array([q[2]for q in near]);ww=np.exp(-(ds/.020)**2);W[i]=(old[ix]*ww[:,None]).sum(0)/ww.sum()
# The palm webs are continuous skin, so proximal weights need a broad geodesic transition.
nb=[[]for _ in co]
for e in me.edges:
 a,z=e.vertices;nb[a].append(z);nb[z].append(a)
for sd,part in [('L',4),('R',5)]:
 channels=[g for g,n in gn.items()if n.startswith(f'B_{sd}_')and ('Hand'in n or 'Finger'in n)]
 hand=b.vertex_groups[f'B_{sd}_Hand'].index;deep=[g for g,n in gn.items()if n.startswith(f'B_{sd}_Finger')and n not in [f'B_{sd}_Finger{i}'for i in range(5)]]
 band=(pv==part)&(W[:,channels].sum(1)>.9)&(W[:,deep].sum(1)<.1)
 for _ in range(6):
  old=W.copy()
  for i in np.flatnonzero(band):
   ns=[j for j in nb[i]if pv[j]==part]
   if ns:W[i]=.35*old[i]+.65*old[ns].mean(0)
for i in np.flatnonzero((pv==0)&(co[:,2]>1.14)&(co[:,2]<1.4)|np.isin(pv,[4,5])):
 ww=W[i];ww[ww<1e-5]=0;ww/=ww.sum()
 for g in b.vertex_groups:g.remove([int(i)])
 for gi in np.flatnonzero(ww>0):b.vertex_groups[int(gi)].add([int(i)],float(ww[gi]),'REPLACE')
# Preserve source arm motion while reducing the low combat stance and clearing the skirt at rest.
rest={n:(Quaternion(v[0]),Vector(v[1]),Vector(v[2]))for n,v in json.loads((P/'work/native_rest.json').read_text()).items()}
def rotation(n,R):
 m=R.to_4x4();m.translation=r.pose.bones[n].head;r.pose.bones[n].matrix=m;bpy.context.view_layer.update()
poses={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];frames=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);frames.append({n:(pb.rotation_quaternion.copy(),pb.location.copy(),pb.scale.copy())for n,pb in r.pose.bones.items()})
 poses[a.name]=frames
for a in bpy.data.actions:
 r.animation_data.action=None
 for f,pose in enumerate(poses[a.name]):
  for n,(q,l,s)in pose.items():pb=r.pose.bones[n];pb.rotation_quaternion=q;pb.location=l;pb.scale=s
  bpy.context.view_layer.update()
  if a.name in ['Attack','Hit']:
   for n in ['B_Spine','B_Spine1','B_Spine2']:r.pose.bones[n].rotation_quaternion=rest[n][0].slerp(pose[n][0],.4)
   bpy.context.view_layer.update()
  for sd in 'LR':
   if sd=='L'or a.name!='Attack':
    for pb in r.pose.bones:
     if pb.name.startswith(f'B_{sd}_Finger'):pb.rotation_quaternion=Quaternion()
   if a.name not in ['Death','Dead']:
    n=f'B_{sd}_UpperArm';sign=-1 if sd=='L'else 1
    rotation(n,Quaternion(Vector((0,1,0)),math.radians(8)*sign).to_matrix()@r.pose.bones[n].matrix.to_3x3())
  r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
  for pb in r.pose.bones:
   if not pb.name.startswith(('Skirt_','Braid_')):pb.keyframe_insert('rotation_quaternion',frame=f)
  r.animation_data.action=None
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
