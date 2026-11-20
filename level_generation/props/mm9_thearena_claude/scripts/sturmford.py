"""Loads a Sturmford City props script (../mm9_sturmfordcity_claude/scripts/<name>.py) as a module running on this
project's spectator table (spectators.py, in the Sturmford table's shape): while the script is loaded,
sys.modules['props_table'] is the spectator table, so its HERE, MODELS, POSES, source(), built_props() ... are the
Arena spectators'. The Arena's own props_table is put back afterwards (anskram.py's loader, for the posed peasants).
Usage: module = sturmford.load('convert_all')"""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import props_table  # noqa: E402,F401  (the Arena's table first: spectators.py reads it)
import spectators  # noqa: E402


def load(name):
    path = spectators.STURMFORD / 'scripts' / f'{name}.py'
    saved = sys.modules.get('props_table')
    sys.modules['props_table'] = spectators
    try:
        spec = importlib.util.spec_from_file_location(f'sturmford_{name}', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.modules['props_table'] = saved
    return module
