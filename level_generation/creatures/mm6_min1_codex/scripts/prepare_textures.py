import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n,args in [('transfer_uv.py',[str(P/'work/uv_master.blend'),str(P/'meshy/retexture_v2'),str(P/'work/textured_uv.blend')]),('transfer_uv.py',[str(P/'work/textured_uv.blend'),str(P/'meshy/head_retexture_v1'),str(P/'work/textured_uv.blend'),'HeadUV']),('uv_raster.py',[str(P/'work/textured_uv.blend'),'UVMap','1024']),('uv_raster.py',[str(P/'work/textured_uv.blend'),'HeadUV','1024']),('bake_ao.py',[])]:
 sys.argv=[n,'--',*args] if args else [n];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
