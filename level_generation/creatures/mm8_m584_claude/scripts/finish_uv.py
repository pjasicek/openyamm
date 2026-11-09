import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def step(name,*args):
 s=P/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
step('transfer_uv.py',P/'work/rig_uv_head.blend',P/'meshy/body_texture_v1',P/'work/rig_uv_body.blend')
step('transfer_uv.py',P/'work/rig_uv_body.blend',P/'meshy/head_texture_v2',P/'work/textured_uv.blend','HeadUV')
step('uv_raster.py',P/'work/textured_uv.blend','UVMap',1024)
step('uv_raster.py',P/'work/textured_uv.blend','HeadUV',1024)
step('bake_ao.py',P/'work/textured_uv.blend',1024)

step('raster_prop.py',P/'work/textured_uv.blend','PolearmUV',1024)
