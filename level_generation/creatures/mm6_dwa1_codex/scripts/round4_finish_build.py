import runpy,sys,subprocess
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round4_cloth_receipt.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round4_export.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round4_prepare_checks.py')],check=True)
for name in ['round4_gates.py','round4_lower_gates.py','round4_final_visual.py']:
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
