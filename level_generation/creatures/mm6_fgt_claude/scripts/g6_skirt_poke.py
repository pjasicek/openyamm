"""Closed tassets: test trousers crossing each strip's OUTWARD surface from behind it at rest.
The generic nearest-face gate treats the inside/back of a closed strip as its front, which flags the untouched
standing pose. Keep each sample's same rest-associated strip and require an actual outward crossing.
"""
import bpy,sys,os,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
rest=[v.co.copy() for v in me.vertices]
strips={16,17,18,19,20,21,22,23,24,25,28,30,31,33,34,36,38}
skin=[i for i,v in enumerate(me.vertices) if pv[i]==2 and .65<v.co.z<1.04]
faces={}
for part in strips:
 fs=[]
 for p in me.polygons:
  if pv[p.vertices[0]]!=part:continue
  radial=Vector((p.center.x,p.center.y,0))
  if radial.length and p.normal.dot(radial.normalized())>.2 and abs(p.normal.z)<.8:fs.append(tuple(p.vertices))
 assert fs, f'No outer surface for strip {part}'
 faces[part]=fs
from collections import Counter
boundaries={}
for part,fs in faces.items():
 counts=Counter(tuple(sorted((f[k],f[(k+1)%len(f)]))) for f in fs for k in range(len(f)))
 boundaries[part]=[[(f[k],f[(k+1)%len(f)]) for k in range(len(f)) if counts[tuple(sorted((f[k],f[(k+1)%len(f)])))]==1] for f in fs]
def boundary(part,fi,loc,co):
 for a,b in boundaries[part][fi]:
  edge=co[b]-co[a];t=max(0,min(1,(loc-co[a]).dot(edge)/max(edge.length_squared,1e-12)))
  if (loc-(co[a]+edge*t)).length<1e-5:return True
 return False
samples={}
for part,fs in faces.items():
 tree=BVHTree.FromPolygons(rest,fs)
 ids=[]
 for i in skin:
  loc,n,fi,d=tree.find_nearest(rest[i],.055)
  if loc is not None and not boundary(part,fi,loc,rest) and d>.001 and (rest[i]-loc).dot(n)<-.8*d:ids.append(i)
 samples[part]=ids
print('SKIRTGATE associated samples',sum(map(len,samples.values())))
assert sum(map(len,samples.values()))>20
for name in a[1:]:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
 worst=(0,None,None,None)
 for f in np.arange(act.frame_range[0],act.frame_range[1]+.001,.625):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1))
  ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear()
  for part,fs in faces.items():
   tree=BVHTree.FromPolygons(co,fs)
   for i in samples[part]:
    loc,n,fi,d=tree.find_nearest(co[i],.055)
    if loc is not None and not boundary(part,fi,loc,co) and d>worst[0] and (co[i]-loc).dot(n)>.8*d:worst=(d,float(f),part,i)
 print('SKIRTPOKE',name,'outward cm/frame/strip/vertex',round(worst[0]*100,2),*worst[1:])
