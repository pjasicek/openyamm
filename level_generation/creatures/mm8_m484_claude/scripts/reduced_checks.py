import runpy,os,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/reduce_body.py'),run_name='__main__')
os.environ['CHECK_BLEND']='work/pilots_reduced.blend';os.environ['CHECK_PREFIX']='reduced'
for f in ['check_pilots.py','check_contacts.py']:runpy.run_path(str(P/'scripts'/f),run_name='__main__')
