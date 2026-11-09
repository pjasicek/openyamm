import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v1_parts.blend'))
report=[]
for ob in list(bpy.data.objects):
 if ob.type!='MESH':continue
 if ob.name in ('P17','P19','P33','P34','P35'):
  report.append({'part':ob.name,'removed':'floating fragment'});bpy.data.objects.remove(ob,do_unlink=True);continue
 bm=bmesh.new();bm.from_mesh(ob.data);bm.verts.ensure_lookup_table()
 bad=[]
 for face in bm.faces:
  longest=max(e.calc_length() for e in face.edges);area=face.calc_area()
  if longest>0.14 and longest*longest/max(2*area,1e-12)>12:bad.append(face)
 report.append({'part':ob.name,'needle_faces_removed':len(bad),'original_faces':len(bm.faces)})
 bmesh.ops.delete(bm,geom=bad,context='FACES')
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
 bm.to_mesh(ob.data);bm.free()
 assert len(ob.data.polygons)>0,ob.name
 ob.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[int(ob.name[1:])]*len(ob.data.vertices))
for ob in bpy.data.objects:ob.select_set(ob.type=='MESH')
bpy.context.view_layer.objects.active=bpy.data.objects['P00'];bpy.ops.object.join();body=bpy.context.object;body.name=body.data.name='Body'
co=np.array([v.co[:] for v in body.data.vertices]);body.data.attributes.new('orig_co','FLOAT_VECTOR','POINT').data.foreach_set('vector',co.ravel())
(p/'work/geometry_cleanup.json').write_text(json.dumps(report,indent=2))
print('CLEAN',report,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/step1.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/clean_v1'),.85,1.9,views=('front','left','back','three_quarter'),resolution=(600,900))
