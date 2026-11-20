import bpy,bmesh,json,math,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];me=o.data;old=[[list(me.uv_layers.active.data[i].uv) for i in f.loop_indices] for f in me.polygons]
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:
 if f.material_index==1:f.select_set(True)
bmesh.update_edit_mesh(me);bpy.ops.uv.smart_project(angle_limit=math.radians(45),island_margin=.02,area_weight=0.,scale_to_bounds=False);bpy.ops.uv.pack_islands(margin=.012,rotate=True,shape_method='CONCAVE');bpy.ops.object.mode_set(mode='OBJECT')
patches=[{'source':old[f.index],'target':[list(me.uv_layers.active.data[i].uv) for i in f.loop_indices]} for f in me.polygons if f.material_index==1]
(P/'work/head_uv_reprojection.json').write_text(json.dumps(patches));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
runpy.run_path(str(P/'scripts/uv_gate.py'),run_name='__main__');runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
