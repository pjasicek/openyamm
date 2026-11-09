"""Sweep of the fidget blade direction (FIDGET_BLADE) with the bounded wrist roll: peak swing and twist range per
candidate (author_fidget.py writes work/rig_fidget.blend each time; the last candidate's result stays)."""
import runpy, sys, os, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
for b in sys.argv[sys.argv.index('--') + 1:]:
    os.environ['FIDGET_BLADE'] = b; sys.argv = ['author_fidget.py']
    runpy.run_path(str(P / 'scripts/author_fidget.py'), run_name='__main__')
    d = json.loads((P / 'work/fidget_plan.json').read_text())
    print('SWEEP', b, 'swing max', max(d['swing_per_frame']), 'hold', d['swing_per_frame'][30], 'twist', min(d['twist_per_frame']), max(d['twist_per_frame']))
