from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def run(name,args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('transfer_uv.py',[P/'work/rig_uv_ready.blend',P/'meshy/body_retexture_v1',P/'work/rig_body_uv.blend'])
run('transfer_uv.py',[P/'work/rig_body_uv.blend',P/'meshy/head_retexture_v1',P/'work/rig_textured_uv.blend','HeadUV'])
import shutil
shutil.copy(P/'work/rig_textured_uv.blend',P/'work/rig_textured_uv_original.blend')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',[P/'work/rig_textured_uv.blend',layer,1024])
