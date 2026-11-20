import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/adopt_textured_topology.py'),run_name='__main__')
for uv in ['UVMap','HeadUV']:
 sys.argv=['raster','--','work/textured_uv.blend',uv,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));bpy.data.objects['Body'].data.uv_layers.active=bpy.data.objects['Body'].data.uv_layers['UVMap'];sys.argv=['ao','--','Body',str(P/'work/ao_body.png'),'.03','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
