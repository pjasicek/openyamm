import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for n in ['round2_contact_gates.py','round1_gates.py','gate_equipment.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
