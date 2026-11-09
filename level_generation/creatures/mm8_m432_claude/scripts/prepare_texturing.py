import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['reduce_rigged.py','--',str(P/os.environ.get('REDUCE_INPUT','work/rig_assembled.blend')),str(P/'work/rig_reduced.blend')]
runpy.run_path(str(P/'scripts/reduce_rigged.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_uploads.py'),run_name='__main__')

import os
os.environ['GATE_INPUT']='work/rig_reduced.blend';os.environ['GATE_LABEL']='reduced'
runpy.run_path(str(P/'scripts/gates.py'),run_name='__main__')
