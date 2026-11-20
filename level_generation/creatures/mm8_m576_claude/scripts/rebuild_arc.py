import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['author_attack.py','--',str(P/'work/gate_repair_carry_v3.blend'),str(P/'work/gate_repair_attack.blend')];runpy.run_path(str(P/'scripts/author_attack.py'),run_name='__main__')
sys.argv=['finish_gate_repair.py'];runpy.run_path(str(P/'scripts/finish_gate_repair.py'),run_name='__main__')
sys.argv=['export_gate_repair.py'];runpy.run_path(str(P/'scripts/export_gate_repair.py'),run_name='__main__')
