import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['retarget','--',str(P/'work/round4/sources_death.blend'),str(P/'work/round4/sources_complete.blend'),str(P.parents[2]/'anim_library/humanoid_set/Unarmed.glb')+':UnarmedRunForward:SourceRun']
runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
exec((P/'scripts/round4_textures.py').read_text().split("bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/repaired.blend'))")[0])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round4/near_unbaked.blend'));body=bpy.data.objects['Body']
for i in sorted({f.material_index for f in body.data.polygons}):
 ob=material_part(body,i,'UVProbe');bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
 print('BEFORE',i,ob.data.materials[0].name,[(min(u.uv[k]for u in ob.data.uv_layers.active.data),max(u.uv[k]for u in ob.data.uv_layers.active.data))for k in range(2)],flush=True)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.pack_islands(udim_source='ACTIVE_UDIM',rotate=False,scale=True,margin_method='FRACTION',margin=.016);bpy.ops.object.mode_set(mode='OBJECT')
 print('AFTER',i,[(min(u.uv[k]for u in ob.data.uv_layers.active.data),max(u.uv[k]for u in ob.data.uv_layers.active.data))for k in range(2)],flush=True)
 bpy.data.objects.remove(ob,do_unlink=True)
