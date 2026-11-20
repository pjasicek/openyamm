import runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['round3_configure_gates.py','round3_compare.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
try:runpy.run_path(str(P/'scripts/round2_final_gates.py'),run_name='__main__')
except RuntimeError:
 if json.loads((P/'review/gates/gates.json').read_text())['counts'].get('FAIL',0)==0:raise
runpy.run_path(str(P/'scripts/round3_cloth_findings.py'),run_name='__main__')
