#!/usr/bin/env python3
"""Harrower-local copy of lod_repair_claude/repair.py's ratio ladder, baking and image gates.
Separate prepare/finish phases let the approved Blender wrapper render between project locks.
Usage: prepare_repair.py prepare|finish <stem> r25_12|r30_16|r35_20|r40_25
"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
HERE = PROJECT.with_name('lod_repair_claude') / 'scripts'
ROOT = PROJECT.parents[2]
PYTHON = os.environ.get('LOD_REPAIR_PYTHON', '/tmp/lancer_lod_venv/bin/python')  # needs pymeshlab, numpy, scipy (README)
LADDER = [(0.25, 0.125), (0.3, 0.16), (0.35, 0.2), (0.4, 0.25)]
SIZES = {1: 1024, 2: 512, 3: 256}
GATE = {2: (6.0, 16.0), 3: (13.0, 19.5)}


def lod_node(path):
    """The body: of the skinned nodes with LODs, the one with the most LOD0 triangles. Separate effect meshes (flames,
    sparks, clouds) and death rubble keep their own LODs (retopology playbook, MM8 batch lessons)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_actor_lods import read_glb
    doc, _ = read_glb(path)
    nodes = [n for n in doc['nodes'] if 'mesh' in n
             and (doc['meshes'][n['mesh']].get('extras') or {}).get('openyamm_lods')]
    if not nodes:
        raise ValueError(f'{path.name}: no skinned node with LODs')
    triangles = lambda n: sum(doc['accessors'][p['indices']]['count'] for p in doc['meshes'][n['mesh']]['primitives'])
    return max(nodes, key=triangles)['name']


def lod_count(path, node_name):
    from build_actor_lods import read_glb
    doc, _ = read_glb(path)
    node = next(n for n in doc['nodes'] if n.get('name') == node_name and 'mesh' in n)
    return len(doc['meshes'][node['mesh']]['extras']['openyamm_lods'])


def run(command, log, environment=None):
    with open(log, 'a') as out:
        out.write('$ ' + ' '.join(map(str, command)) + '\n')
        out.flush()
        subprocess.run([str(c) for c in command], check=True, stdout=out, stderr=subprocess.STDOUT,
                       env={**os.environ, **(environment or {})})


def scores(audit_dir):
    with open(audit_dir / 'scores.tsv') as table:
        return {(r['model'], int(r['lod'])): (float(r['outline_pct']), float(r['colour_diff']))
                for r in csv.DictReader(table, delimiter='\t')}


def passes(score, level, lod1):
    outline, colour = score
    limit_outline, limit_colour = GATE[level]
    if level == 2:
        limit_colour = max(limit_colour, lod1[1] + 3)
    return outline <= limit_outline and colour <= limit_colour


def repair(phase, stem, step):
    original = PROJECT / 'work/lod_originals' / f'{stem}.glb'
    if not original.exists():
        original.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(PROJECT / 'export' / f'{stem}.glb', original)
    work = PROJECT / 'work/lod_repair' / stem
    work.mkdir(parents=True, exist_ok=True)
    log = work / 'repair.log'
    node = lod_node(original)
    ratios = next({2: a, 3: b} for a, b in LADDER if step == f'r{round(a*100)}_{round(b*100)}')
    # The body needs the same reducer at LOD1 to avoid its measured 6.2% transition pop.
    levels = [1, 2, 3] if stem == 'hes_harrower' else [2, 3]
    if 1 in levels:
        ratios[1] = 0.5
    assert lod_count(original, node) == 3
    baked = work / f'{step}.glb'
    audit = work / 'audit'
    result_path = work / 'result.json'
    result = json.loads(result_path.read_text()) if result_path.exists() else {
        'source': str(original.relative_to(ROOT)), 'world': 'hesper', 'node': node, 'steps': []}
    if phase == 'prepare':
        shutil.copy(original, work / 'installed.glb')
        built = work / f'{step}.built.glb'
        bake_dir = work / f'bake_{step}'
        command = [PYTHON, HERE / 'build_lods.py', original, node, built,
                   ','.join(f'{k}:{ratios[k]}' for k in levels)]
        try:
            run(command, log)
        except subprocess.CalledProcessError as error:
            if error.returncode >= 0:
                raise
            run(command, log, {'LOD_PRESERVE_TOPOLOGY': '1'})
            result['preserve_topology'] = True
        run([PYTHON, HERE / 'unwrap_lods.py', built, node, bake_dir,
             ','.join(f'{k}:{SIZES[k]}' for k in levels)], log)
        run([PYTHON, PROJECT / 'scripts/transfer_textures.py', built, node, bake_dir], log)
        run([PYTHON, HERE / 'apply_bake.py', built, node, bake_dir, baked, ','.join(map(str, levels))], log)
        run([sys.executable, PROJECT / 'scripts/repair_far_winding.py', baked], log)
        if audit.exists():
            shutil.rmtree(audit)
        audit.mkdir()
        run([PYTHON, HERE / 'lod_split.py', audit, work / 'installed.glb', baked], log)
    elif phase == 'finish':
        assert all((audit / model / f'lod{level}_{view}.png').exists()
                   for model in ('installed', step) for level in range(4)
                   for view in ('front', 'q34', 'side')), 'Run lod_audit.py through the approved Blender wrapper first'
        with open(audit / 'scores.tsv', 'w') as out:
            subprocess.run([PYTHON, str(HERE / 'lod_score.py'), str(audit)], stdout=out, check=True)
        table = scores(audit)
        entry = {'step': step, 'ratios': [ratios[k] for k in levels],
                 'installed': {k: table[('installed', k)] for k in [1] + levels},
                 'repaired': {k: table[(step, k)] for k in [1] + levels},
                 'pass': {k: passes(table[(step, k)], k, table[('installed', 1)]) for k in levels if k in GATE}}
        result['steps'] = [e for e in result['steps'] if e['step'] != step] + [entry]
        shutil.copytree(audit, work / f'audit_{step}', dirs_exist_ok=True)
        result['passed'] = all(entry['pass'].values())
        result['chosen'] = step if result['passed'] else None
        if result['passed']:
            shutil.copy(baked, PROJECT / 'export' / f'{stem}.glb')
        print(stem, step, entry['repaired'], entry['pass'], flush=True)
    else:
        raise ValueError(phase)
    result_path.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    repair(*sys.argv[1:])
