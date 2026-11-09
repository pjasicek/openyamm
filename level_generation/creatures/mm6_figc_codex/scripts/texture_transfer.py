import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',P/'work/equipped.blend',P/'meshy/retexture_v1',P/'work/textured_uv.blend')
run('transfer_uv.py',P/'work/textured_uv.blend',P/'meshy/head_retexture_v1',P/'work/textured_uv.blend','HeadUV')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',P/'work/textured_uv.blend',layer,1024)
run('full_gates.py',P/'work/textured_uv.blend')
