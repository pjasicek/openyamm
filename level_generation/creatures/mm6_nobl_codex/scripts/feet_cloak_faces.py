import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v10.blend'))
o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];sc=bpy.context.scene
pv=np.zeros(len(o.data.vertices),np.int32);o.data.attributes['piece'].data.foreach_get('value',pv)
r.animation_data.action=bpy.data.actions['Dead'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0)
ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
fs=[f for f in me.polygons if pv[f.vertices[0]]==0 and np.mean([o.data.vertices[i].co.z for i in f.vertices])>1.3]
tree=BVHTree.FromPolygons([v.co for v in me.vertices],[list(f.vertices) for f in fs])
visible=set()
for x in np.linspace(-.4,.4,65):
 for y in np.linspace(-1.15,-.4,65):
  pt,n,k,d=tree.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2)
  if k is not None:visible.add(fs[k].index)
img=bpy.data.images.load(str(p/'textures/nobl_basecolor_1k.png'));A=np.array(img.pixels[:]).reshape(img.size[1],img.size[0],4)
rows=[]
for j in visible:
 f=o.data.polygons[j];uv=np.mean([o.data.uv_layers['UVMap'].data[i].uv[:] for i in f.loop_indices],0);c=np.mean([o.data.vertices[i].co[:] for i in f.vertices],0);rgb=A[int(uv[1]*1023),int(uv[0]*1023),:3]
 rows.append({'face':j,'center':c.tolist(),'normal':list(f.normal),'rgb':rgb.tolist(),'verts':list(f.vertices)})
print('CAPE_VISIBLE',json.dumps(sorted(rows,key=lambda a:sum(a['rgb']))[:30]))
for s in 'LR':
 ids=[v.index for v in o.data.vertices if pv[v.index]==2 and v.co.z<.065 and v.co.x*(1 if s=='L' else -1)>0]
 print('SOLE_WEIGHTS',s,[{'co':list(o.data.vertices[i].co),'w':{o.vertex_groups[g.group].name:round(g.weight,3) for g in o.data.vertices[i].groups if g.weight>.01}} for i in ids[::8]])
ev.to_mesh_clear()
