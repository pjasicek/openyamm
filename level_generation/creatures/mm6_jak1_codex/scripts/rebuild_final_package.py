import runpy,subprocess,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/export_fitted_lods.py'),run_name='__main__')
for script in ['package.py','write_shared_config.py','verify_exports.py']:subprocess.run(['/usr/bin/python3','-B',str(P/'scripts'/script)],check=True)
result=subprocess.run(['/usr/bin/python3','-B',str(P.parents[2]/'output/codex_batch/check_bindings.py'),str(P/'integration/actors.yml')],capture_output=True,text=True,check=True);assert 'BAD'not in result.stdout;(P/'review/bindings_check.txt').write_text(result.stdout)
runpy.run_path(str(P/'scripts/final_panel_gate.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/shared_runtime_gates.py'),run_name='__main__')
