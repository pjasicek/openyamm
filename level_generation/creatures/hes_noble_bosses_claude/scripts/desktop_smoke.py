#!/usr/bin/env python3
"""Minimised desktop smoke runs of every staged map that places the given monster ids: each map loads in the real
game (models load only there; headless scenarios load none) and its game.log must not contain
"Actor model load failed" or "decoration models failed to load" (the Hierarch's throne in D12). Takes the engine/stage locks per run. Usage (repository root):
    desktop_smoke.py <tag> <id> [<id> ...]   -> review/desktop_smoke_<tag>.json"""
import json, re, subprocess, sys
from collections import Counter
from pathlib import Path
import yaml

ROOT = Path.cwd(); P = ROOT / 'level_generation/creatures/hes_noble_bosses_claude'
tag, ids = sys.argv[1], {int(x) for x in sys.argv[2:]}
results = []
for f in sorted((ROOT / 'level_generation/projects').glob('hesper_*/runtime/worlds/hesper/maps/*.scene.yml')):
    scene = yaml.safe_load(f.read_text()); actors = scene.get('initial_state', {}).get('actors', [])
    placed = Counter(a['monster_id'] for a in actors if a.get('monster_id') in ids)
    if not placed:
        continue
    stem = f.name.split('.')[0]; mapfile = stem + ('.odm' if '_out' in stem else '.blv')
    cmd = ['flock', '-s', 'output/hesper_stage/locks/engine_build.lock', 'flock', '-s',
           'output/hesper_stage/locks/stage.lock', './tools/run_game.sh', '--isolated', f'nobles_{tag}_{stem}',
           '--world', 'hesper', '--map', mapfile, '--assets', str(ROOT / 'output/hesper_stage/assets_editor_dev'),
           '--warmup', '2', '--seconds', '5']
    try:
        r = subprocess.run(cmd, text=True, capture_output=True, timeout=180); out = r.stdout + r.stderr; code = r.returncode
    except subprocess.TimeoutExpired as e:
        out = str(e); code = 124
    m = re.search(r'Isolated run: (.+)', out); run = Path(m.group(1).strip()) if m else None
    game = (run / 'game.log').read_text(errors='replace') if run and (run / 'game.log').exists() else ''
    meta = json.loads((run / 'run.json').read_text()) if run and (run / 'run.json').exists() else {}
    fails = [l for l in game.splitlines() if 'Actor model load failed' in l or 'decoration models failed' in l]
    row = {'map': mapfile, 'placed': {str(k): v for k, v in placed.items()}, 'exit_code': code, 'run': str(run),
           'status': meta.get('status'), 'error': meta.get('error'), 'model_load_failures': fails,
           'passed': code == 0 and meta.get('status') == 'completed' and not fails}
    results.append(row); print(json.dumps(row), flush=True)
(P / 'review' / f'desktop_smoke_{tag}.json').write_text(json.dumps(results, indent=2) + '\n')
