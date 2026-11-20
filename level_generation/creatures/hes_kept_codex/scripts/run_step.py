"""Run an owned asset step; exit immediately even when argument validation fails."""
import os,sys,runpy,traceback
sys.dont_write_bytecode=True
from pathlib import Path
try:
    args=sys.argv[sys.argv.index('--')+1:]
    script=Path(args[0]).resolve()
    assert script.parent==Path(__file__).resolve().parent and script.name!='run_step.py'
    sys.argv=[str(script),'--',*args[1:]]
    runpy.run_path(str(script),run_name='__main__')
except BaseException:
    traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
