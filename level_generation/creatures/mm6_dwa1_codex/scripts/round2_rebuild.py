import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round2_package.py')],check=True)
runpy.run_path(str(P/'scripts/round2_gates.py'),run_name='__main__')
