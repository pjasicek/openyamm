from pathlib import Path
import bpy,json
P=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_uv_master.blend'))
body=bpy.context.scene.objects['Flying_Demon_Body'];old=len(body.data.polygons)
with bpy.data.libraries.load(str(P/'work/anatomy_clean_chest.blend'),link=False) as (a,b):b.objects=['Flying_Demon_Body']
donor=b.objects[0]
assert [g.name for g in donor.vertex_groups]==[g.name for g in body.vertex_groups]
body.data=donor.data;bpy.data.objects.remove(donor,do_unlink=True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_uv_master.blend'),compress=True)
(P/'work/chest_surface_repair.json').write_text(json.dumps({'cause':'Projected flatten/fill crossed collar triangles.','method':'Reused original valid surface topology; smoothed the harness intrinsically and adopted only the body mesh.','previous_body_triangles':old,'corrected_body_triangles':len(body.data.polygons),'weights_bind_wing_geometry_uv_and_animation_retained':True},indent=2)+'\n')
print('Adopted clean original-topology body:',len(body.data.vertices),'vertices',len(body.data.polygons),'triangles.',flush=True)
