"""Rebuild the reviewed Lancer shell and weapon while retaining the approved source body and other clips."""
import runpy,sys,os
os.environ['FSTEP']='1'
full='--shell-only' not in sys.argv
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';W=P/'work';sys.path.insert(0,str(S))
def step(name,*args):
    print('REVIEW',name,flush=True);sys.argv=[name,'--',*map(str,args)]
    runpy.run_path(str(S/name),run_name='__main__')
step('armour_spec_lancer.py')
if full:step('fit_ready.py')
if full:step('review_death.py')
# Resume the already fitted ready clips.
source=W/'lancer_review2.blend'
if full:step('bake_new_twists.py',source,source,'Carbine_Standing','Carbine_Fidget','Carbine_Death')
if full:step('helper_bones.py',source,source)

step('make_armour.py',source,S/'armour_lancer.json',source)
step('make_lance.py',source,source)
step('skin_shell.py',source,S/'armour_lancer.json',source)


clips=['Carbine_Standing','Carbine_Fidget','Carbine_Attack','Lancer_Running','Carbine_Walking','Carbine_Hit','Carbine_Death','Carbine_Dead']
step('refresh_hull_uv.py',source,source)
if full:step('gates.py',source,'review2',*clips)
if full:step('sole_probe.py',source,*clips)
if full:step('jerk_probe.py',source,*clips)
if full:step('stride.py',source,'Carbine_Walking','Lancer_Running')
step('shell_stretch.py',source,S/'armour_lancer.json','review2',*clips)
step('shell_leak.py',source,S/'armour_lancer.json','review2',*clips)
if full:step('equipment_gate.py',source,'lancer',*clips)
step('armour_gate.py',source,'review2',S/'armour_lancer.json',*clips)

step('render_review.py','lancer_review2.blend','Carbine_Standing','0','front')
