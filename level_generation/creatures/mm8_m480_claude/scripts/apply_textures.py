from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')

run('transfer_uv.py',[p/'work/texture_master.blend',p/'meshy/body_retexture_v1',p/'work/textured_body.blend'])
run('transfer_uv.py',[p/'work/textured_body.blend',p/'meshy/head_retexture_v1',p/'work/textured.blend','HeadUV'])
for layer in ['UVMap','HeadUV']:run('uv_raster.py',[p/'work/textured.blend',layer,'1024'])
run('render_tex.py',[p/'work/textured.blend',p/'meshy/body_retexture_v1/texture_urls_0_base_color.png','raw_texture',p/'meshy/head_retexture_v1/texture_urls_0_base_color.png'])
