import sys,os,runpy,bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,args=[]):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('transfer_uv.py',['work/production_body.blend','meshy/retexture_v1','work/textured_master.blend']);run('uv_gate.py');run('uv_raster.py',['work/textured_master.blend','UVMap',1024])
sys.argv=['ao','--','Body',str(P/'textures/knight_ao_1k.png'),'.04','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
