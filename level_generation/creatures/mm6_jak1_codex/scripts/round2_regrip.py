import bpy,sys,runpy,os,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_grip_input.blend'))
from thumb_cmc import repair_thumbs
repair_thumbs(bpy.data.objects['Body'],bpy.data.objects['Rig'])
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_grip_anatomy.blend'))
for sd,suffix,clip in [('R','','GripRef'),('L','_left','Staff2')]:
 os.environ['GRIP_SIDE']=sd;os.environ['GRIP_SOURCE']=f'grip_source{suffix}.json';os.environ['GRIP_OUTPUT']=f'grip_pose{suffix}.json';os.environ['R_HANDLE']='.013';os.environ['GRIP_RENDER']=str(P/f'review/round2/grip_{sd}')
 run('grip_solve.py',['work/round2_grip_anatomy.blend',clip,0])
