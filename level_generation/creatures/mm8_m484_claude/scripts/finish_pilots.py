import os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for f in ['fit_pilots.py','reduce_body.py','setup_cloth.py','solve_cloth.py']:runpy.run_path(str(P/'scripts'/f),run_name='__main__')
os.environ['CHECK_BLEND']='work/pilots_cloth.blend';os.environ['CHECK_PREFIX']='cloth'
for f in ['check_pilots.py','check_contacts.py']:runpy.run_path(str(P/'scripts'/f),run_name='__main__')


runpy.run_path(str(P/'scripts/full_gate_run.py'),run_name='__main__')

