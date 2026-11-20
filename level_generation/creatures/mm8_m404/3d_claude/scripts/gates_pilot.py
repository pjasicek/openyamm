import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
arguments=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
prefix=arguments[1] if len(arguments)>1 else "pilot"
runpy.run_path(str(p/'scripts/export_pilot.py'),run_name='__main__')
sys.argv=['run_gates.py','--',str(p/('export/'+prefix+'_body.glb')),'--config',str(p/(prefix+'.gates.json')),'--out',str(p/('review/'+prefix+'_gates'))]
runpy.run_path('level_generation/creatures/claude_shared/gates/run_gates.py',run_name='__main__')
