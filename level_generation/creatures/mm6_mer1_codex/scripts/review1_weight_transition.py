import bpy,json
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];sel=json.loads((P/'review/reduction/selection.json').read_text())
for e in [{'blend':'work/reduction_master.blend'}]+sel['body']:
 path=P/e['blend'];bpy.ops.wm.open_mainfile(filepath=str(path));o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];parts=[a.value for a in o.data.attributes['piece'].data]
 with bpy.data.libraries.load(str(P/'work/review1'/(path.stem+'_before.blend')),link=False)as(src,dst):dst.objects=['Body']
 old=dst.objects[0];oldparts=[a.value for a in old.data.attributes['piece'].data];trees={}
 for pid in [8,9]:
  vs=[v for v in old.data.vertices if oldparts[v.index]==pid];tree=KDTree(len(vs))
  for v in vs:tree.insert(v.co,v.index)
  tree.balance();trees[pid]=tree
 for v in o.data.vertices:
  pid=parts[v.index]
  if pid not in [8,9]:continue
  sd='R'if pid==8 else'L';head=r.data.bones[f'B_{sd}_UpperArm'].head_local;axis=(r.data.bones[f'B_{sd}_Forearm'].head_local-head).normalized();distance=(v.co-head).dot(axis);t=max(0,min(1,(distance+.04)/.36))
  source=old.data.vertices[trees[pid].find(v.co)[1]];weights={old.vertex_groups[g.group].name:g.weight*t for g in source.groups if old.vertex_groups[g.group].name in r.data.bones};anchor=f'B_{sd}_Clavicle';weights[anchor]=weights.get(anchor,0)+1-t
  for g in list(v.groups):o.vertex_groups[g.group].remove([v.index])
  for n,w in weights.items():
   if w>1e-7:o.vertex_groups[n].add([v.index],w,'REPLACE')
 bpy.data.objects.remove(old,do_unlink=True);bpy.ops.wm.save_as_mainfile(filepath=str(path))
