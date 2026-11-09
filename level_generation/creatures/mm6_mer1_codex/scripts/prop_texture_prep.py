import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
for n in ['build_club.py','export_uploads.py']:
 sys.argv=[n];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
