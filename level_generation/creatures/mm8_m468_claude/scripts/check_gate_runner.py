from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];sys.argv=['test_gates.py','--','--out',str(p/'review/gate_runner_tests')];runpy.run_path(str(p.parent/'claude_shared/gates/test_gates.py'),run_name='__main__')
