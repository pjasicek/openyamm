"""Fit the dedicated hollow-nose/teeth head; the body's sealed nose and empty mouth lack that topology."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pilot.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
# Keep the neck under the mantle; the new neck overlaps this hidden transition.
bm=bmesh.new();bm.from_mesh(body.data);pl=bm.verts.layers.int['piece']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[pl] in (10,11) or (v[pl]==0 and (v.co.z>1.60 or (v.co.z>1.56 and abs(v.co.x)<0.115)))],context='VERTS')
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary and all(v.co.z<1.4 for v in e.verts)],sides=8)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(body.data);bm.free()
with bpy.data.libraries.load(str(p/'work/head_raw.blend'),link=False) as (a,b):b.objects=['Body']
head=b.objects[0];bpy.context.scene.collection.objects.link(head);head.name='DetailedHead'
# glTF splits shared surface vertices at seams; weld them before reduction so each side cannot drift apart.
bm=bmesh.new();bm.from_mesh(head.data)
before=len(bm.verts);boundary=sum(e.is_boundary for e in bm.edges)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.00001)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=0.000001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=16)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
print('HEAD v2 weld',before,'->',len(bm.verts),'boundary',boundary,'->',sum(e.is_boundary for e in bm.edges))
bm.to_mesh(head.data);bm.free();head.data.validate();head.data.update()
for v in head.data.vertices:v.co.z+=1.49
# Transfer the visible neck's bend while keeping the skull rigid.
for n in ('B_Head','B_Neck'):head.vertex_groups.new(name=n)
for v in head.data.vertices:
 w=float(np.clip((v.co.z-1.50)/0.09,0,1))
 head.vertex_groups['B_Head'].add([v.index],w,'REPLACE');head.vertex_groups['B_Neck'].add([v.index],1-w,'REPLACE')
for name,val in [('piece',60),('garment',9),('finger',0)]:
 a=head.data.attributes.get(name) or head.data.attributes.new(name,'INT','POINT');a.data.foreach_set('value',[val]*len(head.data.vertices))
a=head.data.attributes.get('orig_co') or head.data.attributes.new('orig_co','FLOAT_VECTOR','POINT');a.data.foreach_set('vector',[x for v in head.data.vertices for x in v.co])
for f in head.data.polygons:f.use_smooth=True
for o in bpy.data.objects:o.select_set(o in (head,body))
bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_fitted.blend'))
sys.path.insert(0,str(p/'scripts'));import common
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/head_fitted'),1.0,2.05,views=('front','left','back'),resolution=(420,620))
common.render_views(str(p/'review/head_fitted_detail'),1.68,0.43,views=('front','left','back'),resolution=(500,500))
