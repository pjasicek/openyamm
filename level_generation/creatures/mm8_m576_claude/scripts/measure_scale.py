import bpy,json,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_textured_uv.blend'));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=[(ob.matrix_world@v.co).z for v in me.vertices];ev.to_mesh_clear();height=max(z)-min(z)
result={'standing_body_height_m':height,'native_body_height_px':189,'native_sprite_scale':1.1999969482421875,'native_body_measurement':'m576Sa0: crest at y=67, soles y=255 inclusive; raised shaft butt excluded','scale':189*1.1999969482421875/height}
(P/'work/scale.json').write_text(json.dumps(result,indent=2));print('SCALE',result,flush=True)
sys.argv=['stride.py','--',str(P/'work/master_textured_uv.blend'),'Walking','Running'];runpy.run_path(str(P/'scripts/stride.py'),run_name='__main__')
