from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('transfer_uv.py',[p/'work/rig_v5h.blend',p/'meshy/retexture_v1',p/'work/rig_v6.blend'])
run('transfer_uv.py',[p/'work/rig_v6.blend',p/'meshy/head_retexture_v1',p/'work/rig_v6.blend','HeadUV'])
run('uv_gate.py',[])
for layer in ('UVMap','HeadUV'):run('uv_raster.py',[p/'work/rig_v6.blend',layer,1024])
