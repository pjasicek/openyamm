import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.dont_write_bytecode=True
for n in ['finish_motion.py','assemble.py']:
 print('RUN',n,flush=True)
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
