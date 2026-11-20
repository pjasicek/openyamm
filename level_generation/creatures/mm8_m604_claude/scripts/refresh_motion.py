from pathlib import Path
import sys,runpy,bpy
p=Path(__file__).resolve().parents[1]
def run(n,args):
 s=p/'scripts'/n;sys.argv=[str(s),'--',*[str(x) for x in args]];runpy.run_path(str(s),run_name='__main__')
run('polish_motion.py',[])
run('foot_level.py',[p/'work/polished.blend',p/'work/levelled.blend','Standing','Walking:const','Attack','Hit','Fidget','Death:until=8','Running:const'])
run('floor_motion.py',[])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/ready_lined.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
with bpy.data.libraries.load(str(p/'work/animated.blend'),link=False) as (src,dst):dst.actions=list(src.actions)
for a in dst.actions:a.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/ready_motion.blend'))
run('ground_final.py',[])
run('export_runtime.py',[])
