from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
def run(name,*args):
 s=p/'scripts'/name;sys.argv=[str(s),'--',*map(str,args)];runpy.run_path(str(s),run_name='__main__')
run('transfer_uv.py',p/'work/rig_v5h.blend',p/'meshy/body_retexture_v1',p/'work/rig_v6.blend')
run('transfer_uv.py',p/'work/rig_v6.blend',p/'meshy/head_retexture_v1',p/'work/rig_v6.blend','HeadUV')
run('sync_actions.py',p/'work/rig_v5.blend',p/'work/rig_v6.blend')
for layer in ['UVMap','HeadUV']:run('uv_raster.py',p/'work/rig_v6.blend',layer,'1024')
