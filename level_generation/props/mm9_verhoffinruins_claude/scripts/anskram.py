"""Loads an Anskram Keep props script (../mm9_anskramkeep_claude/scripts/<name>.py) as a module running on this
project's table: this project's props_table is put in sys.modules['props_table'] first, so the script's HERE, MODELS,
source(), placements() ... are the Verhoffin Ruins's."""
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import props_table  # noqa: E402

sys.modules['props_table'] = props_table


def load(name):
    path = props_table.ANSKRAM / 'scripts' / f'{name}.py'
    spec = importlib.util.spec_from_file_location(f'anskram_{name}', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
