"""Smooth sleeve weights over physical distances; bound influence count for the runtime."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:];kind=os.environ['KEPT_BODY']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pc=np.array([a.value for a in me.attributes['piece'].data]);w=np.zeros((len(co),len(body.vertex_groups)))
for v in me.vertices:
 for g in v.groups:w[v.index,g.group]=g.weight
if kind=='male':
 ids=np.where(pc==0)[0];tree=KDTree(len(ids))
 for i in ids:tree.insert(co[i],int(i))
 tree.balance();old=w.copy()
 # Meshy's uneven triangles need a metric neighbourhood; equal-edge averaging left short-edge jumps.
 for i in ids:
  if co[i,2]<1.10:continue
  near=tree.find_range(co[i],.07);j=np.array([x[1] for x in near]);d=np.array([x[2] for x in near]);a=np.exp(-.5*(d/.03)**2)
  w[i]=np.average(old[j],weights=a,axis=0)
# Keep eight runtime influences; the protected hands normally use four or fewer.
order=np.argsort(w,axis=1);w[np.arange(len(w))[:,None],order[:,:-8]]=0;w/=w.sum(1)[:,None]
for g in body.vertex_groups:g.remove(list(range(len(co))))
for i,row in enumerate(w):
 for gi in np.where(row>1e-5)[0]:body.vertex_groups[int(gi)].add([i],float(row[gi]),'REPLACE')
assert (w>1e-5).sum(1).max()<=8
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
