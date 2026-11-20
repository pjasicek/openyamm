"""Space the two lance grips for the long weapon and clear free fingers during the fall."""
import os
from pathlib import Path
import runpy
import sys
P = Path(__file__).resolve().parents[1]
S, W = P/'scripts', P/'work'
sys.path.insert(0,str(S))
living = ['Carbine_Standing','Carbine_Walking','Lancer_Running','Carbine_Attack','Carbine_Hit','Carbine_Fidget']
def step(name, *args):
    print('POLISH', name, flush=True)
    sys.argv = [name, '--', *map(str,args)]
    runpy.run_path(str(S/name),run_name='__main__')
source = W/'lancer_polished.blend'
step('armour_spec_lancer.py')
step('helper_bones.py', W/'final_lancer.blend', source)
step('make_armour.py', source, S/'armour_lancer.json', source)
step('make_lance.py', source, source)
step('skin_shell.py', source, S/'armour_lancer.json', source)
os.environ.update(Y_LO='.24',Y_HI='.36',HG_X='-.12',NEAR='999',FAR='1000',ROLL_RANGE='0',ELBOW_RANGE='0',POLE_DOWN='1')
step('support_hand.py', source, source, *living)
step('clear_free_hands.py', source, source, 'Carbine_Death')
step('bake_new_twists.py', source, source, *living, 'Carbine_Death')
step('helper_bones.py', source, source)
step('gates.py', source, 'lancer_polished', *living, 'Carbine_Death','Carbine_Dead')
step('armour_gate.py', source, 'lancer_polished', S/'armour_lancer.json', *living, 'Carbine_Death','Carbine_Dead')
