import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parent;W=P.parent/'work'
def run(n,*args):
    sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/n),run_name='__main__')
run('g4_weights.py',W/'pilot_grounded.blend','pilot','Standing:0','Walking:8','Attack:11','Attack:21','Attack:26','Attack:30')
run('make_trident.py')
run('equip_pilot.py')
