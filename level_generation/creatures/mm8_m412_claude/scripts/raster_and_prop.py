import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('uv_raster.py',p/'work/master_uv.blend','UVMap','1024')
run('uv_raster.py',p/'work/master_uv.blend','HeadUV','1024')
run('render_tex.py',p/'work/master_uv.blend',p/'meshy/body_retexture_v1/texture_urls_0_base_color.png','texture_raw',p/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
run('make_cutlass.py')
run('attach_cutlass.py',p/'work/master_uv.blend',p/'work/master_equipped.blend')
