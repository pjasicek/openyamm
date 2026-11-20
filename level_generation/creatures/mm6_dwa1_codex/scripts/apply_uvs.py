import bpy,runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args):sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',['work/texture_master.blend','meshy/body_retexture_v1','work/textured_master.blend'])
run('transfer_uv.py',['work/textured_master.blend','meshy/head_retexture_v1','work/textured_master.blend','HeadUV'])
run('uv_raster.py',['work/textured_master.blend','UVMap',1024]);run('uv_raster.py',['work/textured_master.blend','HeadUV',1024])
