import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
for n in ['equip_bow.py','bow_uv.py','gate_equipment.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
