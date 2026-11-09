"""Verify both paint returns, retain the rig, then bake UV-space region and occlusion maps."""
from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(name,args=()):
    s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('transfer_uv.py',[p/'work/rig_uvprep.blend',p/'meshy/body_retexture_v1',p/'work/rig_body_uv.blend'])
run('transfer_uv.py',[p/'work/rig_body_uv.blend',p/'meshy/head_retexture_v1',p/'work/rig_uv.blend','HeadUV'])
run('raster_texture_regions.py')
run('bake_ao.py')
