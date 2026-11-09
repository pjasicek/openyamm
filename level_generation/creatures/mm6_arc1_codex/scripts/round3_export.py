import os,sys,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
for level in range(4):
 os.environ['ARC1_EXPORT_SOURCE']=str(P/f'work/round2/lod{level}.blend');os.environ['ARC1_EXPORT_LEVEL']=str(level);runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
os.environ.pop('ARC1_EXPORT_SOURCE');os.environ.pop('ARC1_EXPORT_LEVEL')
for name in ['round2_pack_lods.py','pack_runtime.py']:subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
