import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s=P/'scripts/export_glb.py'
sys.argv=[str(s),'--',str(P/'work/rig_final.blend'),str(P/'review/viewer/gog_clay.glb')]
runpy.run_path(str(s),run_name='__main__')
runpy.run_path(str(P/'scripts/export_parity.py'),run_name='__main__')
