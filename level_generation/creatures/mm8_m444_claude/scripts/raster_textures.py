from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for layer in ['UVMap','HeadUV']:
 sys.argv=[str(p/'scripts/uv_raster.py'),'--',str(p/'work/rig_v6.blend'),layer,'1024'];runpy.run_path(str(p/'scripts/uv_raster.py'),run_name='__main__')
