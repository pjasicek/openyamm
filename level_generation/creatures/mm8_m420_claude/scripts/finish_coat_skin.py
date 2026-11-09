"""Reproduce the coat correction from the retained whole-body cast master."""
import runpy, sys
from pathlib import Path
P = Path(__file__).resolve().parent
runpy.run_path(str(P / 'coat_weights.py'), run_name='__main__')
sys.argv = ['probe_coat_skin.py', '--after']
runpy.run_path(str(P / 'probe_coat_skin.py'), run_name='__main__')
runpy.run_path(str(P / 'finish_cast_revision.py'), run_name='__main__')
