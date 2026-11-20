# Project-local paths for the shared repair.py ladder; installed worlds remain untouched.
#!/usr/bin/env python3
"""Repair the far LODs of installed creatures: for each model, try the ratio ladder (LOD2, LOD3 of LOD0's
triangles), build (build_lods.py), unwrap (unwrap_lods.py), fill the textures (transfer_textures.py), apply
(apply_bake.py) and audit (audit.sh) each step, and
keep the first step whose new levels pass the gate. LOD0 and LOD1 stay as installed.

Gate (audit.sh scores, each switch seen at its switch size, worst of three views): LOD2 outline <= 6 % and colour
<= 16 (or no worse than the installed LOD1 switch, for models whose texture already shimmers at that size);
LOD3 outline <= 13 % and colour <= 19.5. Calibrated on the 2026-10-22 audit of all installed creatures (healthy
switches: LOD2 median 3.5 % / 11.7, LOD3 median 9.4 % / 16.2).

Every repair starts from originals/<stem>.glb, the installed GLB before its first repair (copied from
assets_source on the first run; also the rollback source). Writes work/<stem>/<step>.glb per step, work/<stem>/result.json and, for the chosen step, export/<stem>.glb.
LOD_REPAIR_RUN=<name> writes to work/<name>/<stem> instead and skips the export (experiments).
Usage: repair.py <stem> [<stem>...]   (model in assets_source/worlds/*/models/<stem>.glb)"""
import csv
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
HERE = PROJECT.parent / 'lod_repair_claude/scripts'
PYTHON = os.environ.get('LOD_REPAIR_PYTHON', 'python3')  # needs pymeshlab, numpy, scipy (README)
LADDER = [(0.25, 0.125), (0.3, 0.16), (0.35, 0.2), (0.4, 0.25)]
SIZES = {2: 512, 3: 256}
GATE = {2: (6.0, 16.0), 3: (13.0, 19.5)}


def lod_node(path):
    """The body: of the skinned nodes with LODs, the one with the most LOD0 triangles. Separate effect meshes (flames,
    sparks, clouds) and death rubble keep their own LODs (retopology playbook, MM8 batch lessons)."""
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_actor_lods import read_glb
    doc, _ = read_glb(path)
    nodes = [n for n in doc['nodes'] if 'mesh' in n and 'skin' in n
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


def repair(stem):
    original = PROJECT / 'work/lod_original.glb'
    if not original.exists():
        original.parent.mkdir(exist_ok=True)
        shutil.copy(next(ROOT.glob(f'assets_source/worlds/*/models/{stem}.glb')), original)
    source = original
    run_name = os.environ.get('LOD_REPAIR_RUN', '')
    work = PROJECT / 'work' / run_name / stem
    work.mkdir(parents=True, exist_ok=True)
    log = work / 'repair.log'
    log.write_text('')
    shutil.copy(source, work / 'installed.glb')
    node = lod_node(source)
    installed = original
    result = {'source': str(source.relative_to(ROOT)), 'world': 'hesper', 'node': node, 'steps': []}
    chosen = None
    levels = [level for level in (2, 3) if level <= lod_count(source, node)]
    if not levels:
        raise ValueError(f'{stem}: no LOD2 or LOD3 to repair')
    for r2, r3 in LADDER:
        step = f'r{round(r2 * 100)}_{round(r3 * 100)}'
        ratios = {2: r2, 3: r3}
        built, baked = work / f'{step}.built.glb', work / f'{step}.glb'
        bake_dir = work / f'bake_{step}'
        try:
            try:
                run([PYTHON, HERE / 'build_lods.py', source, node, built, ','.join(f'{k}:{ratios[k]}' for k in levels)], log)
            except subprocess.CalledProcessError as error:
                if error.returncode >= 0:
                    raise
                # MeshLab crashed (signal): retry with topology preserved, recorded in the result.
                run([PYTHON, HERE / 'build_lods.py', source, node, built, ','.join(f'{k}:{ratios[k]}' for k in levels)], log,
                    {'LOD_PRESERVE_TOPOLOGY': '1'})
                result['preserve_topology'] = True
            run([PYTHON, HERE / 'unwrap_lods.py', built, node, bake_dir,
                 ','.join(f'{k}:{SIZES[k]}' for k in levels)], log)
            run([PYTHON, HERE / 'transfer_textures.py', built, node, bake_dir], log)
            run([PYTHON, HERE / 'apply_bake.py', built, node, bake_dir, baked, ','.join(map(str, levels))], log)
        except subprocess.CalledProcessError as error:
            result['steps'].append({'step': step, 'error': str(error)})
            continue
        audit = work / 'audit'
        if audit.exists():
            shutil.rmtree(audit)
        run(['bash', PROJECT / 'scripts/audit_lods.sh', audit, work / 'installed.glb', baked], log)
        table = scores(audit)
        lod1 = table[('installed', 1)]
        entry = {'step': step, 'ratios': [ratios[k] for k in levels],
                 'installed': {k: table[('installed', k)] for k in [1] + levels},
                 'repaired': {k: table[(step, k)] for k in [1] + levels}}
        entry['pass'] = {k: passes(table[(step, k)], k, lod1) for k in levels}
        result['steps'].append(entry)
        shutil.copytree(audit, work / f'audit_{step}', dirs_exist_ok=True)
        print(stem, step, entry['repaired'], entry['pass'], flush=True)
        if all(entry['pass'].values()):
            chosen = step
            break
    if chosen is None:
        # Keep the most generous step for review; the result marks it as not passing.
        candidates = [s for s in result['steps'] if 'error' not in s]
        chosen = candidates[-1]['step'] if candidates else None
    result['chosen'] = chosen
    result['passed'] = bool(chosen) and all(next(s for s in result['steps'] if s.get('step') == chosen)['pass'].values())
    if chosen and not run_name:
        (PROJECT / 'export').mkdir(exist_ok=True)
        shutil.copy(work / f'{chosen}.glb', PROJECT / 'export' / f'{stem}.glb')
    (work / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
    print('RESULT', stem, chosen, 'pass' if result['passed'] else 'NOT PASSING', flush=True)


for stem in sys.argv[1:]:
    repair(stem)
