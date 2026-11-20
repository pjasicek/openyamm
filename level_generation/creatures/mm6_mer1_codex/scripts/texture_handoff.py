import bpy,sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
def run(n,args=()):sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('fix_club.py');run('prop_gate.py',['work/prop_fixed.blend'])
run('transfer_uv.py',['work/texture_weighted.blend','meshy/body_retexture_v1','work/textured_uv.blend'])
run('transfer_uv.py',['work/textured_uv.blend','meshy/head_retexture_v1','work/textured_uv.blend','HeadUV'])
for uv in ['UVMap','HeadUV']:run('uv_raster.py',['work/textured_uv.blend',uv,1024])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'));bpy.data.objects['Body'].data.uv_layers.active=bpy.data.objects['Body'].data.uv_layers['UVMap']
sys.argv=['ao','--','Body',str(P/'work/ao_body.png'),'.03','1024'];runpy.run_path(str(P.parent/'claude_shared/bake_creature_ao.py'),run_name='__main__')
