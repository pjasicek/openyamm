from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for layer,job,src,out in [('UVMap','body_retexture_v1','rig_uv_ready.blend','rig_body_uv.blend'),('HeadUV','head_retexture_v1','rig_body_uv.blend','rig_textured_uv.blend')]:
    sys.argv=['transfer','--',str(p/'work'/src),str(p/'meshy'/job),str(p/'work'/out),layer]
    runpy.run_path(str(p/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ('UVMap','HeadUV'):
    sys.argv=['raster','--',str(p/'work/rig_textured_uv.blend'),layer,'1024']
    runpy.run_path(str(p/'scripts/uv_raster.py'),run_name='__main__')
sys.argv=['ao','--',str(p/'work/rig_textured_uv.blend'),'1024']
runpy.run_path(str(p/'scripts/bake_ao_natm.py'),run_name='__main__')
