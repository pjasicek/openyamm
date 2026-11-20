import bpy,sys,json,bmesh
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
rep=[]
for level in range(4):
 path=P/f'work/round2/body_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));C.reset();o=bpy.data.objects['Body'];before=o.data.has_custom_normals
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 if before:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=True
 o.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(path));rep.append({'level':level,'custom_normals_before':before,'custom_normals_after':o.data.has_custom_normals})
 if level==0:
  common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='SINGLE';bpy.context.scene.display.shading.single_color=(.3,.5,.3)
  common.render_views(str(P/'review/round2/normal_fixed_rest'),1.2,1.4,views=('front','left'),resolution=(650,800))
  C.activate('Attack',.4);common.render_views(str(P/'review/round2/normal_fixed_attack'),1.2,1.4,views=('front','left'),resolution=(650,800))
(P/'review/round2/normals_correction.json').write_text(json.dumps(rep,indent=2))
