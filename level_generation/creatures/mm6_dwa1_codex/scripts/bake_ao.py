import bpy,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for layer,prefix in [('UVMap','dwa1'),('HeadUV','dwa1_head')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));me=bpy.data.objects['Body'].data;me.uv_layers.active=me.uv_layers[layer];me.uv_layers[layer].active_render=True
 bpy.context.scene.render.threads_mode='FIXED';bpy.context.scene.render.threads=4
 sys.argv=['bake_creature_ao.py','--','Body',str(P/f'textures/{prefix}_ao_1k.png'),'.035','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
