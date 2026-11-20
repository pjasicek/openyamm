import bpy,bmesh,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];me=o.data
for ob in bpy.context.scene.objects:ob.select_set(ob==o)
bpy.context.view_layer.objects.active=o;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_mode(type='FACE');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(me)
for f in bm.faces:f.select_set(f.material_index==1)
bmesh.update_edit_mesh(me);bpy.ops.uv.pack_islands(margin=.003,margin_method='FRACTION',rotate=True,shape_method='CONVEX');bpy.ops.object.mode_set(mode='OBJECT');bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'))
for script in ['uv_gate.py','uv_raster.py','export_head_v2.py']:runpy.run_path(str(P/'scripts'/script),run_name='__main__')
