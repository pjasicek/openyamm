import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
    sys.argv=[n,'--',*[str(x) for x in a]]
    runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',P/'work/rig_uv_master.blend',P/'meshy/body_retexture_v1',P/'work/rig_body_uv.blend')
run('transfer_uv.py',P/'work/rig_body_uv.blend',P/'meshy/head_retexture_v1',P/'work/rig_textured_uv.blend','HeadUV')
for uv in ['UVMap','HeadUV']:run('uv_raster.py',P/'work/rig_textured_uv.blend',uv,1024)
run('bake_ao.py',P/'work/rig_textured_uv.blend',1024)
