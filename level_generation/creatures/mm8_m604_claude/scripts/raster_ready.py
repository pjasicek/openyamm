from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for layer in ['UVMap','HeadUV']:
 s=p/'scripts/uv_raster.py';sys.argv=[str(s),'--',str(p/'work/ready.blend'),layer,'1024'];runpy.run_path(str(s),run_name='__main__')
