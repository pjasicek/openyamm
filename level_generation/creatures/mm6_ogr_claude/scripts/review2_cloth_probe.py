from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v13.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];me=b.data;pv=[a.value for a in me.attributes['piece'].data];fs=[tuple(f.vertices) for f in me.polygons if all(pv[i]==0 for i in f.vertices)]
for name,f in [('Running',4),('Running',22),('Standing',57),('Death',16)]:
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(f);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,fs);rows=[]
 for face in [fa for fa in me.polygons if pv[fa.vertices[0]] in [14,19]]:
  for v,ids in [(co[i],[i]) for i in face.vertices]+[(sum((co[i] for i in face.vertices),Vector())/3,list(face.vertices))]:
   loc,n,fi,d=tree.find_nearest(v,.06)
   if loc is not None and (v-loc).dot(n)<-.707*d:
    rows.append((d,ids,fs[fi],tuple(v),tuple(loc),tuple(n),[tuple(me.vertices[i].co) for i in ids]))
 print(name,f,*sorted(rows,reverse=True)[:3],sep='\n')
