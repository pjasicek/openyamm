"""Verify Meshy face/corner correspondence and carry only UVs back onto the animated master."""
import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',P/'work/master_uv.blend',P/'meshy/body_texture_v1',P/'work/body_uv.blend')
run('transfer_uv.py',P/'work/body_uv.blend',P/'meshy/head_texture_v1',P/'work/head_uv.blend','HeadUV')
os.environ['UV_OBJECT']='Crossbow'
run('transfer_uv.py',P/'work/head_uv.blend',P/'meshy/crossbow_texture_v1',P/'work/textured_uv.blend')
run('uv_raster.py',P/'work/textured_uv.blend','UVMap',512)
os.environ['UV_OBJECT']='Body'
for layer in ('UVMap','HeadUV'):run('uv_raster.py',P/'work/textured_uv.blend',layer,1024)
