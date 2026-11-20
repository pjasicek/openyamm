import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.argv=['probe','--','work/production_body.blend','Running','Attack','Death'];runpy.run_path(str(P/'scripts/skirt_probe_details.py'),run_name='__main__')
