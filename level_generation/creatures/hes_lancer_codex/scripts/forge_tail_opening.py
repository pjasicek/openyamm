"""Open the rear lower hull plate around the preserved Kreegan tail."""
import bpy,bmesh,os,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_direction_fit.blend'))
o=bpy.data.objects['Apron_Back2'];bm=bmesh.new();bm.from_mesh(o.data);seen=set();remove=[]
for v in bm.verts:
 if v in seen:continue
 component={v};queue=[v];seen.add(v)
 while queue:
  w=queue.pop()
  for e in w.link_edges:
   q=e.other_vert(w)
   if q not in seen:seen.add(q);component.add(q);queue.append(q)
 if max(abs(q.co.x) for q in component)<.075 and max(q.co.z for q in component)<.72:remove.extend(component)
assert remove,'Expected two bridge components'
bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(o.data);bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_direction_fit.blend'));print('TAIL_CLEARANCE',len(remove),flush=True);os._exit(0)
