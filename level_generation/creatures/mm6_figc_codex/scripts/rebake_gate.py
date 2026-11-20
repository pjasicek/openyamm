import runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round3';os.environ.update(FIGC_EXPORT_DIR=str(R/'rebake/gate_input'),FIGC_VALIDATION_DIR=str(R/'rebake/validation'))
runpy.run_path(str(P/'scripts/gates_exported.py'),run_name='__main__')
