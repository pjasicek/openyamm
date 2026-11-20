from pathlib import Path
import bpy,sys,runpy
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));W=P/'work'
sys.argv=['reduce_rigged.py','--',str(W/'grounded.blend'),str(W/'master_rig.blend')];runpy.run_path(str(P/'scripts/reduce_rigged.py'),run_name='__main__')
body=bpy.data.objects['Body'];bpy.context.view_layer.objects.active=body
for o in bpy.data.objects:o.select_set(o==body)
mod=body.modifiers.new('FrozenTriangles','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
assert all(len(f.vertices)==3 for f in body.data.polygons)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'master_rig.blend'))
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')
