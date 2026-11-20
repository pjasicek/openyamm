from pathlib import Path
import sys,runpy,os
p=Path(__file__).resolve().parents[1]
def run(name,args):
 s=p/'scripts'/name;sys.argv=[str(s),'--']+[str(x) for x in args];runpy.run_path(str(s),run_name='__main__')
run('retarget.py',[p/'work/rig_body.blend',p/'work/grip_probe.blend',str(p.parents[2]/'anim_library/humanoid_set/Relax.glb')+':RelaxIdle:GripProbe'])
os.environ['R_HANDLE']='0.016'
os.environ['GRIP_RENDER']=str(p/'review/grip')
os.environ['GRIP_SCALE']='0.30'
run('grip_solve.py',[p/'work/grip_probe.blend','GripProbe',0])
