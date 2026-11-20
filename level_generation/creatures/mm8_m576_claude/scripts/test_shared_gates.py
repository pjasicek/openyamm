import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['test_gates.py','--','--out',str(P/'review/gate_tool_tests')]
runpy.run_path(str(P.parent/'claude_shared/gates/test_gates.py'),run_name='__main__')
