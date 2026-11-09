import bpy,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_rig.blend'));body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=body
mod=body.modifiers.new('FrozenTriangles','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
assert all(len(f.vertices)==3 for f in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master_rig.blend'))
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')
