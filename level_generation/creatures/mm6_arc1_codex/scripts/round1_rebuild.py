import runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round1_motion.py'),run_name='__main__')
p=P/'scripts/round1_export_gates.py';exec(compile(p.read_text().split('# Final exported model views')[0],str(p),'exec'),{'__file__':str(p)})
runpy.run_path(str(P/'scripts/round1_check_and_export.py'),run_name='__main__')
