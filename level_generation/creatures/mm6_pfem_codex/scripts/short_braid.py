"""Fit the short tied braid to the nape while retaining the generated hair surface and UVs."""
import bpy,numpy as np,json,runpy
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene;m=o.data
pv=np.array([x.value for x in m.attributes['piece'].data]);ids=np.flatnonzero(pv==19)
R=np.array([tuple(m.vertices[i].co) for i in ids]);faces=[tuple(f.vertices) for f in m.polygons if all(pv[i]==1 for i in f.vertices)]
samples=[]
for name in ('Standing','Walking','Hit','Death','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in np.arange(0,a.frame_range[1]+.01,1.):
  sc.frame_set(int(f));ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh()
  tree=BVHTree.FromPolygons([v.co for v in mm.vertices],faces);ev.to_mesh_clear()
  M=r.pose.bones['B_Head'].matrix@r.data.bones['B_Head'].matrix_local.inverted()
  samples.append((name,float(f),tree,np.array(M)))
results=[]
for scale in (.65,.5,.4):
 for offset in (.01,.02,.03,.04):
  co=R.copy();co[:,2]=1.47+(co[:,2]-1.47)*scale;co[:,1]+=offset*np.clip((1.47-R[:,2])/.035,0,1)
  worst=(0.,None,None)
  for name,f,tree,M in samples:
   V=co@M[:3,:3].T+M[:3,3]
   for j,x in enumerate(V):
    if R[j,2]>1.445:continue
    loc,n,fi,d=tree.find_nearest(Vector(x));depth=-(Vector(x)-loc).dot(n)
    if depth>worst[0]:worst=(float(depth),name,f)
  results.append({'scale':scale,'offset':offset,'worst':worst})
  print('BRAID CANDIDATE',results[-1])
best=min(results,key=lambda x:(max(0,x['worst'][0]-.001),1-x['scale']+x['offset']*5))
print('SELECTED',best)
assert best['worst'][0]<.002,best
co=R.copy();co[:,2]=1.47+(co[:,2]-1.47)*best['scale'];co[:,1]+=best['offset']*np.clip((1.47-R[:,2])/.035,0,1)
for j,i in enumerate(ids):
 v=m.vertices[i];v.co=co[j]
 for g in list(v.groups):o.vertex_groups[g.group].remove([int(i)])
 o.vertex_groups['B_Head'].add([int(i)],1,'REPLACE')
(p/'work/braid_fit.json').write_text(json.dumps({'candidates':results,'selected':best},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
