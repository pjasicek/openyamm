"""Fit the retained two-hand clips around the complete pectoral shell."""
import os,runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';W=P/'work';sys.path.insert(0,str(S))
def step(name,*args):
 print('CUIRASS',name,flush=True);sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
source=W/'lancer_review2.blend'
clips=['Carbine_Standing','Carbine_Fidget','Carbine_Attack','Lancer_Running','Carbine_Walking','Carbine_Hit','Carbine_Death','Carbine_Dead']
step('armour_spec_lancer.py')
step('make_armour.py',source,S/'armour_lancer.json',source)
step('skin_shell.py',source,S/'armour_lancer.json',source)
os.environ.update(LEFT='1',PASSES='3',MARGIN='.008')
step('armour_clear.py',source,source,*clips)
step('bake_new_twists.py',source,source,*clips)
step('helper_bones.py',source,source)
step('gates.py',source,'review2',*clips)
step('shell_stretch.py',source,S/'armour_lancer.json','review2',*clips)
step('shell_leak.py',source,S/'armour_lancer.json','review2',*clips)
step('armour_gate.py',source,'review2',S/'armour_lancer.json',*clips)
step('render_review.py','lancer_review2.blend','Carbine_Standing','0','front')
