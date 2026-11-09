import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['g4_weights.py','--',str(P/'work/export_reimport_lod0.blend'),'export','Standing:0','Walking:10','Running:8','Attack:12.5','Attack:30','Hit:5','Death:30','Death:60','Dead:0','Fidget:30'];runpy.run_path(str(P/'scripts/g4_weights.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_sheets.py'),run_name='__main__')
