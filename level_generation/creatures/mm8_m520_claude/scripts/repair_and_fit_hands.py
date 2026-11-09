from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parent
for name in ['remove_extra_fingers','build_rig','fit_hands']:
 s=p/f'{name}.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
