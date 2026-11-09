import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from collections import Counter
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_feet.blend'));C.activate('Standing',0);o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();mm.calc_loop_triangles();pos=[v.co.copy()for v in mm.vertices];tt=[t.vertices[:]for t in mm.loop_triangles];tree=BVHTree.FromPolygons(pos,tt,all_triangles=True);pv=np.array([x.value for x in o.data.attributes['piece'].data]);rows=json.loads((P/'work/extra_pixels.json').read_text());counts=Counter();reports=[]
for view,pixels in rows.items():
 a=int(view)*math.pi/4;h=Vector((math.cos(a),math.sin(a),0));d=Vector((math.sin(a),-math.cos(a),0));ppm=88/1.7129090557573363
 for iy,ix in pixels:
  origin=h*((ix+.5-410)/ppm)+Vector((0,0,.85-(iy+.5-410)/ppm))+d*5;hit,n,idx,dist=tree.ray_cast(origin,-d,10)
  if hit is not None:
   counts[idx]+=1;reports.append({'view':int(view),'pixel':[iy,ix],'triangle':idx,'part':pv[list(tt[idx])].tolist(),'hit':hit[:]})
report={'most_common':[(i,n,list(tt[i]),pv[list(tt[i])].tolist(),[list(pos[j])for j in tt[i]])for i,n in counts.most_common(30)],'hits':reports};(P/'review/far_extra_faces.json').write_text(json.dumps(report,indent=2));print('EXTRA FACES',report['most_common'][:15],flush=True)
