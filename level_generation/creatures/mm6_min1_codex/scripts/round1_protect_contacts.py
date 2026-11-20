import bpy,json
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];ax=bpy.data.objects['AxeMesh'];faces=[tuple(f.vertices) for f in b.data.polygons];af=[tuple(f.vertices) for f in ax.data.polygons];sets=[set(f) for f in faces];marked=set();report={}
def points(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();p=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();return p
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];before=len(marked)
 for f in np.arange(0,a.frame_range[1]+.001,bpy.context.scene.render.fps/48):
  bpy.context.scene.frame_set(int(f),subframe=f%1);co=points(b);tree=BVHTree.FromPolygons(co,faces)
  for i,j in tree.overlap(tree):
   if i<j and not sets[i].intersection(sets[j]):marked.update(faces[i]);marked.update(faces[j])
  for i,j in BVHTree.FromPolygons(points(ax),af).overlap(tree):marked.update(faces[j])
 report[a.name]=len(marked)-before
adj={i:set() for i in range(len(b.data.vertices))}
for e in b.data.edges:
 i,j=e.vertices;adj[i].add(j);adj[j].add(i)
marked.update({j for i in list(marked) for j in adj[i]});attr=b.data.attributes.get('protect_contact') or b.data.attributes.new('protect_contact','INT','POINT');attr.data.foreach_set('value',[int(i in marked) for i in range(len(b.data.vertices))]);report['total']=len(marked);report['vertices']=len(b.data.vertices)
(P/'review/round1/reduction/contact_protection.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_high.blend'));print('CONTACT PROTECTION',report,flush=True)
