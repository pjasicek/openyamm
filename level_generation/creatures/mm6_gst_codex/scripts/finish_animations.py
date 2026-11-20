import runpy,sys
from pathlib import Path
p=Path(__file__).parent;sys.argv.append('--full')
runpy.run_path(str(p/'animate_ghost.py'),run_name='__main__')
runpy.run_path(str(p/'verify_animation.py'),run_name='__main__')
