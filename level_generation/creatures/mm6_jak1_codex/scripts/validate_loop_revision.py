import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/final_gates.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/rebuild_final_package.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/loop_audit.py')],check=True)
