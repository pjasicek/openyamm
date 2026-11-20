import bpy,math,json,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('ROBE_INPUT','work/motion_skin.blend')))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update()
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices])
ids=np.where(np.isin(pv,[2,5,12,13,14,15,16]))[0];faces=[tuple(f.vertices) for f in me.polygons if all(pv[i]==2 for i in f.vertices)]
tree=BVHTree.FromPolygons(co.tolist(),faces);axis=Vector((0,-.02,0));zs=[1.13,.85,.57,.29,.025];chains=[]
for c in range(16):
 deg=-180+c*22.5;a=math.radians(deg);d=Vector((math.sin(a),math.cos(a),0));pts=[]
 for z in zs:
  start=Vector((axis.x,axis.y,z));hits=[];dist=0
  while dist<.6:
   loc,n,idx,dl=tree.ray_cast(start+d*(dist+1e-5),d,.6-dist)
   if loc is None:break
   hits.append(loc);dist+=dl+1e-5
  if hits:pt=hits[-1]
  else:
   aa=np.arctan2(co[ids,0]-axis.x,co[ids,1]-axis.y);da=np.abs((aa-a+math.pi)%(2*math.pi)-math.pi)
   candidates=ids[(da<.25)&(np.abs(co[ids,2]-z)<.07)]
   assert len(candidates), (deg,z)
   pt=Vector(co[candidates].mean(0));pt.z=z
  pts.append(list(pt))
 chains.append({'deg':deg,'pts':pts,'bones':[f'Robe_{c:02}_{k}' for k in range(4)]})
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 parent=rig.data.edit_bones['B_Pelvis']
 for k,n in enumerate(c['bones']):
  b=rig.data.edit_bones.get(n) or rig.data.edit_bones.new(n);b.head=c['pts'][k];b.tail=c['pts'][k+1];b.parent=parent;b.use_connect=k>0;parent=b
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
 for n in c['bones']:
  if n not in body.vertex_groups:body.vertex_groups.new(name=n)
groups={g.name:g for g in body.vertex_groups}
for i in ids:
 x,y,z=co[i];a=(math.degrees(math.atan2(x-axis.x,y-axis.y))+180)/22.5;lo=int(a)%16;hi=(lo+1)%16;t=a-math.floor(a);w={}
 for ci,mix in [(lo,1-t),(hi,t)]:
  # Linear blend of joint rotations centred on each bone. Adjacent sectors form a continuous closed robe.
  u=np.interp(z,list(reversed(zs[:-1])),list(reversed(range(4))))
  k=min(3,int(u));j=min(3,k+1);v=u-k
  for n,amt in [(chains[ci]['bones'][k],1-v),(chains[ci]['bones'][j],v)]:w[n]=w.get(n,0)+mix*amt
 waist=float(np.clip((z-1.055)/.075,0,1));w={n:v*(1-waist) for n,v in w.items()};w['B_Pelvis']=waist
 for g in body.vertex_groups:g.remove([int(i)])
 best=sorted(w.items(),key=lambda nv:-nv[1])[:4];total=sum(v for n,v in best)
 for n,v in best:
  if v>1e-6:groups[n].add([int(i)],v/total,'REPLACE')
scene['cloak_chains']=json.dumps(chains);assert len(rig.data.bones)<=128
print('ROBE chains',len(chains),'joints',len(rig.data.bones),'verts',len(ids))
bpy.ops.wm.save_as_mainfile(filepath=str(p/os.environ.get('ROBE_OUTPUT','work/robe_rig.blend')))
