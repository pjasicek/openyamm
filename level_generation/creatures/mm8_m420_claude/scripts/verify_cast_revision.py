from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parent
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(P/name),run_name='__main__')
run('export_parity.py')
run('export_physics.py')
run('export_physics.py','--cast-only')
run('g5_hand_stretch.py',P.parent/'work/master_settled.blend','Attack','Cast')

run('cast_endpoints.py')
run('verify_dual_support.py')

run('verify_cast_windup.py')
