from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
for n,a in [('triangulate_upload.py',[p/'work/animated.blend',p/'work/triangulated.blend']),('transfer_uv.py',[p/'work/triangulated.blend',p/'meshy/body_retexture_v1',p/'work/textured_body.blend'])]:
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in a]];runpy.run_path(str(s),run_name='__main__')
