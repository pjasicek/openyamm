import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',[P/'work/uv_master.blend',P/'meshy/body_retexture_v2',P/'work/rig_body_uv.blend'])
run('transfer_uv.py',[P/'work/rig_body_uv.blend',P/'meshy/head_retexture_v1',P/'work/rig_textured_uv.blend','HeadUV'])

import shutil
shutil.copyfile(P/'work/rig_textured_uv.blend',P/'work/rig_textured_uv_original.blend')
runpy.run_path(str(P/'scripts/finish_uv.py'),run_name='__main__')
