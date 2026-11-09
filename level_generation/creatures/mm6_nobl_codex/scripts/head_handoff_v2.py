import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,args):
 sys.argv=[n,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',[p/'work/rig_v9h2.blend',p/'meshy/head_retexture_v2',p/'work/rig_v9.blend','HeadUV'])
run('uv_raster.py',[p/'work/rig_v9.blend','HeadUV',1024])
