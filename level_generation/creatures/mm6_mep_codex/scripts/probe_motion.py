import runpy,sys,os
from pathlib import Path
p=Path(__file__).resolve().parents[1];runpy.run_path(str(p/'scripts/dense_gates.py'),run_name='__main__');runpy.run_path(str(p/'scripts/cloth_topology.py'),run_name='__main__')
sys.argv=['g6','--',str(p/'work/geometry_final.blend'),'Attack'];runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
