import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/before_feedback_v1/textured_uv.blend'))
ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];me=ob.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([v.co[:] for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data]);report={}
for part in [0,1,2,4,5]:
 fs=[f for f in me.polygons if piece[f.vertices[0]]==part];counts={}
 for f in fs:
  for e in f.edge_keys:counts[e]=counts.get(e,0)+1
 boundary=[e for e,n in counts.items() if n==1];adj={}
 for a,b in boundary:adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
 loops=[];todo=set(adj)
 while todo:
  seen=set();stack=[next(iter(todo))]
  while stack:
   i=stack.pop()
   if i in seen:continue
   seen.add(i);stack.extend(adj[i]-seen)
  todo-=seen;ids=sorted(seen);pts=co[ids];loops.append({'vertices':ids,'count':len(ids),'min':pts.min(0).tolist(),'max':pts.max(0).tolist(),'center':pts.mean(0).tolist(),'coords':pts.tolist()})
 report[str(part)]={'faces':len(fs),'boundaries':loops}
print('BOUNDARIES',json.dumps({k:[{n:v for n,v in l.items() if n not in ['coords','vertices']} for l in x['boundaries']] for k,x in report.items()}),flush=True)
(P/'work/feedback_boundaries.json').write_text(json.dumps(report,indent=2))
# Distinct diagnostic colours reveal cloth and exposed-skin overlap independently of the texture.
me.materials.clear()
for name,color in [('cloth',(.12,.32,.16,1)),('skin',(.75,.48,.32,1)),('hair',(.25,.1,.03,1)),('other',(.45,.45,.5,1))]:
 m=bpy.data.materials.new(name);m.diffuse_color=color;me.materials.append(m)
for f in me.polygons:
 p=piece[f.vertices[0]];f.material_index=0 if p==0 else 1 if p in [1,4,5] else 2 if p==2 else 3
common.setup_render();common.workbench_clay(bpy.context.scene)
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
common.render_views(str(P/'review/feedback_v1/clay_sleeve_L'),1.18,.40,views=('front','left','three_quarter'),target=(.23,0),resolution=(700,700))
common.render_views(str(P/'review/feedback_v1/clay_hairline'),1.62,.26,views=('front','three_quarter'),resolution=(700,700))
