import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
mesh=bpy.data.objects['Body']
for layer,name in [('UVMap','body'),('HeadUV','head')]:
 mesh.data.uv_layers.active=mesh.data.uv_layers[layer];mesh.data.uv_layers[layer].active_render=True
 sys.argv=['bake_ao','--','Body',str(P/'work'/f'ao_{name}.png'),'.06','1024']
 runpy.run_path('level_generation/creatures/claude_shared/bake_creature_ao.py',run_name='__main__')
