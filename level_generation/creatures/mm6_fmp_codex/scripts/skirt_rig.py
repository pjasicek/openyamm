"""Sixteen closed-ring cloth chains shared by the dress and its overlaid apron."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_corrected.blend'))
scene=bpy.context.scene;arm=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
arm.animation_data.action=None
for b in arm.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
piece=[v.value for v in me.attributes['piece'].data];co=[v.co.copy() for v in me.vertices]
faces=[tuple(f.vertices) for f in me.polygons if all(piece[v]==1 for v in f.vertices)]
tree=BVHTree.FromPolygons(co,faces);axis=Vector((-.004,-.025,0));chains=[]
for i in range(16):
 deg=i*22.5;a=math.radians(deg);d=Vector((math.sin(a),math.cos(a),0));pts=[]
 for z in (1.035,.81,.58,.35,.12):
  o=Vector((axis.x,axis.y,z));hit=tree.ray_cast(o,d,.8)[0]
  assert hit is not None,(deg,z)
  pts.append(list(hit))
 chains.append(dict(deg=deg,pts=pts,bones=[f'Skirt_{i:02d}_{k}' for k in range(4)]))
bpy.context.view_layer.objects.active=arm;arm.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 parent=arm.data.edit_bones['B_Pelvis']
 for k,n in enumerate(c['bones']):
  b=arm.data.edit_bones.new(n);b.head=c['pts'][k];b.tail=c['pts'][k+1];b.parent=parent;b.use_connect=k>0;parent=b
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
 for n in c['bones']:body.vertex_groups.new(name=n)
def smooth(x):
 t=max(0,min(1,x));return t*t*(3-2*t)
def cw(c,z):
 zs=[v[2] for v in c['pts']]
 k=next((k for k in range(4) if z>=zs[k+1]),3);t=(zs[k]-z)/(zs[k]-zs[k+1]);w={c['bones'][k]:1.0}
 if t<.3 and k>0:
  f=.5*(1-max(0,t)/.3);w={c['bones'][k-1]:f,c['bones'][k]:1-f}
 elif t>.7 and k<3:
  f=.5*(min(1,t)-.7)/.3;w={c['bones'][k+1]:f,c['bones'][k]:1-f}
 return w
for v in me.vertices:
 if piece[v.index] not in (1,7):continue
 a=math.atan2(v.co.x-axis.x,v.co.y-axis.y)%(2*math.pi);t=a/(2*math.pi)*16;i=int(t)%16;t-=int(t);w={}
 for c,f in ((chains[i],1-t),(chains[(i+1)%16],t)):
  for n,x in cw(c,v.co.z).items():w[n]=w.get(n,0)+f*x
 blend=smooth((v.co.z-.96)/.075);w={n:x*(1-blend) for n,x in w.items()};w['B_Pelvis']=blend
 for g in body.vertex_groups:g.remove([v.index])
 for n,x in w.items():
  if x>1e-6:body.vertex_groups[n].add([v.index],x,'REPLACE')
 assert abs(sum(w.values())-1)<1e-6
scene['skirt_chains']=json.dumps(chains)
assert len(arm.data.bones)<128
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/skirt_rig.blend'))
