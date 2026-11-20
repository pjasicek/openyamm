from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
run('close_head.py',[])
for l in ['UVMap','HeadUV']:run('uv_raster.py',[p/'work/ready.blend',l,'1024'])
run('bake_maps.py',[p/'work/ready.blend','1024'])
