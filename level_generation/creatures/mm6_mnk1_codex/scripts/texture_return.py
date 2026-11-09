import bpy,runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('transfer_uv.py',p/'work/texture_master.blend',p/'meshy/retexture_v1',p/'work/textured_uv.blend')
run('uv_raster.py',p/'work/textured_uv.blend','UVMap',2048)
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'))
sys.argv=['bake_creature_ao.py','--','Body',str(p/'work/ao_body.png'),'.03','1024']
runpy.run_path(str(p.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
