"""Keep the split neck seam closed and stone shoulder plates on the shoulder."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_uv.blend'))
rig=bpy.data.objects['JuggernautRig'];body=bpy.data.objects['Body'];head=bpy.data.objects['Head']
def assign(o,v,w):
 for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
 for name,weight in w.items():
  if weight<1e-7:continue
  group=o.vertex_groups.get(name) or o.vertex_groups.new(name=name);group.add([v.index],weight,'REPLACE')
def shoulder(p):
 side='L' if p[0]>0 else 'R';w=float(np.clip((abs(p[0])-.14)/.075,0,1));w=w*w*(3-2*w)
 return {'Chest':1-w,f'UpperArm_{side}':w}
for o in [body,head]:
 for v in o.data.vertices:
  x,y,z=v.co
  if z>.78:
   assign(o,v,{'Head':1} if abs(x+.012)<.115 else shoulder(v.co))
  elif .57<z<.78 and abs(x)<.145:
   assign(o,v,{'Chest':1})
tree=KDTree(len(body.data.vertices))
for v in body.data.vertices:tree.insert(v.co,v.index)
tree.balance();matched=0
for v in head.data.vertices:
 _,i,d=tree.find(v.co)
 if d<1e-6:
  source=body.data.vertices[i];w={body.vertex_groups[g.group].name:g.weight for g in source.groups};assign(head,v,w);matched+=1
assert matched>10,matched
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_uv.blend'))
(P/'work/seam_weights.json').write_text(json.dumps({'matched_neck_boundary_vertices':matched,'body_head_uvs_unchanged':True},indent=2))
print('SEAM_WEIGHTS',matched,flush=True)
