from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('clean_texture_geometry.py')
run('transfer_uv.py',p/'work/rig_texture_clean.blend',p/'meshy/body_retexture_v1',p/'work/rig_textured_uv.blend')
run('transfer_uv.py',p/'work/rig_textured_uv.blend',p/'meshy/head_retexture_v1',p/'work/rig_textured_uv.blend','HeadUV')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',p/'work/rig_textured_uv.blend',layer,'1024')
