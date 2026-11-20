import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];w=p/'work'
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',w/'master_uv_upload.blend',p/'meshy/body_retexture_v1',w/'master_uv_body.blend')
run('transfer_uv.py',w/'master_uv_body.blend',p/'meshy/head_retexture_v1',w/'master_uv.blend','HeadUV')
run('attach_cutlass.py',w/'master_uv.blend',w/'master_equipped.blend')
