import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];w=p/'work'
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',w/'master_uv_upload.blend',p/'meshy/body_retexture_v1',w/'master_uv_body.blend')
run('transfer_uv.py',w/'master_uv_body.blend',p/'meshy/head_retexture_v1',w/'master_uv.blend','HeadUV')
run('uv_raster.py',w/'master_uv.blend','UVMap',1024)
run('uv_raster.py',w/'master_uv.blend','HeadUV',1024)
run('render_tex.py',w/'master_uv.blend',p/'meshy/body_retexture_v1/texture_urls_0_base_color.png','texture_raw',p/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
run('bake_ao.py',w/'master_uv.blend',1024)
