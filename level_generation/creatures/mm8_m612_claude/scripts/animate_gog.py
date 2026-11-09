from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
def step(name,*args):
 script=P/'scripts'/name;sys.argv=[str(script),'--',*map(str,args)];runpy.run_path(str(script),run_name='__main__')
step('author_gog.py')
step('run_fit.py',P/'work/animated_authored.blend',P/'work/animated_running.blend')
step('foot_level.py',P/'work/animated_running.blend',P/'work/animated_feet.blend','Standing','Fidget','Attack','Cast','Hit','Walking:const','Death:until=6')
step('ground_tail.py')
step('twist_bones.py',P/'work/animated_grounded.blend',P/'work/animated_v1.blend')
