import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.argv=['gate','--',str(P/'work/round1/combined_clay.glb')];runpy.run_path(str(P/'scripts/g6_sword_round1.py'),run_name='__main__')
