import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['g6_contacts.py','--',str(P/'work/rig_assembled.blend'),'Attack','Death']
runpy.run_path(str(P/'scripts/g6_contacts.py'),run_name='__main__')
