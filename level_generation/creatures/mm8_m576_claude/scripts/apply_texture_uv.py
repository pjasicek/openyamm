import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parent;W=R/'work'
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/n),run_name='__main__')
run('transfer_uv.py',W/'full_equipped.blend',R/'meshy/body_retexture_v1',W/'body_uv.blend')
run('transfer_uv.py',W/'body_uv.blend',R/'meshy/head_retexture_v1',W/'master_textured_uv.blend','HeadUV')
run('uv_raster.py',W/'master_textured_uv.blend','UVMap',1024)
run('uv_raster.py',W/'master_textured_uv.blend','HeadUV',1024)
run('render_tex.py',W/'master_textured_uv.blend',R/'meshy/body_retexture_v1/texture_urls_0_base_color.png','texture_raw',R/'meshy/head_retexture_v1/texture_urls_0_base_color.png')
