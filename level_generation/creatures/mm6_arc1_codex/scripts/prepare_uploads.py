import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
for n in ['reduce_body.py','export_uploads.py']:runpy.run_path(str(P/'scripts'/n),run_name='__main__')
