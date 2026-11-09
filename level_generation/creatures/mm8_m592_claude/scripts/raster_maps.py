from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for layer in ('UVMap','HeadUV'):
 s=P/'scripts/uv_raster.py';sys.argv=[str(s),'--',str(P/'work/rig_uv.blend'),layer,'1024'];runpy.run_path(str(s),run_name='__main__')
