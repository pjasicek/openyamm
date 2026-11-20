from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
for script,args in [('restore_forge_stroke.py',[]),('finish_shell.py',['--full'])]:
 sys.argv=[script,'--',*args];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
