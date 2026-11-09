import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('dedup_patch.py')
run('transfer_uv.py',p/'work/uv_ready.blend',p/'meshy/retexture_v1',p/'work/body_uv.blend')
run('transfer_uv.py',p/'work/body_uv.blend',p/'meshy/head_retexture_v1',p/'work/textured_uv.blend','HeadUV')
run('uv_raster.py',p/'work/textured_uv.blend','UVMap',1024)
run('uv_raster.py',p/'work/textured_uv.blend','HeadUV',1024)
run('face_nearest.py')
