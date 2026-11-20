#!/usr/bin/env python3
"""Far LODs (LOD2, LOD3 and their shadows) of a reduced project export, by the lod_repair_claude route
(`../../lod_repair_claude/README.md`; scripts copied unchanged from its scripts/ folder): MeshLab collapse of LOD0 on
positions only, xatlas UVs, far textures filled from LOD0, audit at the switch sizes, first ladder step that passes.
LOD0 and LOD1 stay byte-for-byte. Same ladder and gate as lod_repair_claude/scripts/repair.py; the difference is the
input: an explicit GLB (a project export that is not installed) instead of assets_source.
Usage: repair_glb.py <in.glb> <work dir> <out.glb>   (LOD_REPAIR_PYTHON = Python with pymeshlab, xatlas, scipy)"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PYTHON = os.environ.get('LOD_REPAIR_PYTHON', 'python3')
LADDER = [(0.25, 0.125), (0.3, 0.16), (0.35, 0.2), (0.4, 0.25)]
SIZES = {2: 512, 3: 256}
GATE = {2: (6.0, 16.0), 3: (13.0, 19.5)}
sys.path.insert(0, str(ROOT / 'tools'))
from build_actor_lods import read_glb  # noqa: E402


def lod_node(path):
    doc, _ = read_glb(path)
    nodes = [n for n in doc['nodes'] if 'mesh' in n and 'skin' in n
             and (doc['meshes'][n['mesh']].get('extras') or {}).get('openyamm_lods')]
    triangles = lambda n: sum(doc['accessors'][p['indices']]['count'] for p in doc['meshes'][n['mesh']]['primitives'])
    return max(nodes, key=triangles)['name']


def run(command, log, environment=None):
    with open(log, 'a') as out:
        out.write('$ ' + ' '.join(map(str, command)) + '\n'); out.flush()
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


source, work, final = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
work.mkdir(parents=True, exist_ok=True)
log = work / 'repair.log'; log.write_text('')
shutil.copy(source, work / 'installed.glb')
node = lod_node(source); levels = [2, 3]
result = {'source': str(source), 'node': node, 'steps': []}
chosen = None
for r2, r3 in LADDER:
    step = f'r{round(r2 * 100)}_{round(r3 * 100)}'; ratios = {2: r2, 3: r3}
    built, baked, bake_dir = work / f'{step}.built.glb', work / f'{step}.glb', work / f'bake_{step}'
    try:
        plan = ','.join(f'{k}:{ratios[k]}' for k in levels)
        try:
            run([PYTHON, HERE / 'build_lods.py', source, node, built, plan], log)
        except subprocess.CalledProcessError as error:
            if error.returncode >= 0:
                raise
            run([PYTHON, HERE / 'build_lods.py', source, node, built, plan], log, {'LOD_PRESERVE_TOPOLOGY': '1'})
            result['preserve_topology'] = True
        run([PYTHON, HERE / 'unwrap_lods.py', built, node, bake_dir, ','.join(f'{k}:{SIZES[k]}' for k in levels)], log)
        run([PYTHON, HERE / 'transfer_textures.py', built, node, bake_dir], log)
        run([PYTHON, HERE / 'apply_bake.py', built, node, bake_dir, baked, ','.join(map(str, levels))], log)
    except subprocess.CalledProcessError as error:
        result['steps'].append({'step': step, 'error': str(error)}); continue
    audit = work / 'audit'
    if audit.exists():
        shutil.rmtree(audit)
    run([HERE / 'audit.sh', audit, work / 'installed.glb', baked], log)
    table = scores(audit); lod1 = table[('installed', 1)]
    entry = {'step': step, 'ratios': [ratios[k] for k in levels],
             'installed': {k: table[('installed', k)] for k in [1] + levels},
             'repaired': {k: table[(step, k)] for k in [1] + levels}}
    entry['pass'] = {k: passes(table[(step, k)], k, lod1) for k in levels}
    result['steps'].append(entry)
    shutil.copytree(audit, work / f'audit_{step}', dirs_exist_ok=True)
    print(step, entry['repaired'], entry['pass'], flush=True)
    if all(entry['pass'].values()):
        chosen = step; break
if chosen is None:
    candidates = [s for s in result['steps'] if 'error' not in s]
    chosen = candidates[-1]['step'] if candidates else None
result['chosen'] = chosen
result['passed'] = bool(chosen) and all(next(s for s in result['steps'] if s.get('step') == chosen)['pass'].values())
if chosen:
    shutil.copy(work / f'{chosen}.glb', final)
(work / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
print('RESULT', node, chosen, 'pass' if result['passed'] else 'NOT PASSING', flush=True)
