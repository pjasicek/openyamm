#!/usr/bin/env python3
"""Repair the far LODs of installed creatures: for each model, try the ratio ladder (LOD2, LOD3 of LOD0's
triangles), build (build_lods.py), unwrap (unwrap_lods.py), fill the textures (transfer_textures.py), apply
(apply_bake.py) and audit (audit.sh) each step, and
keep the first step whose new levels pass the gate. LOD0 and LOD1 stay as installed.

Gate (audit.sh scores, each switch seen at its switch size, worst of three views): LOD2 outline <= 6 % and colour
<= 16 (or no worse than the installed LOD1 switch, for models whose texture already shimmers at that size);
LOD3 outline <= 13 % and colour <= 19.5. Calibrated on the 2026-10-22 audit of all installed creatures (healthy
switches: LOD2 median 3.5 % / 11.7, LOD3 median 9.4 % / 16.2).

Source (--source, default `installed`): `installed` starts from the current installed GLB
(assets_source/worlds/*/models/<stem>.glb), which carries every texture pass, clip and fix since the first repair
(LOD playbook section 7); `original` from originals/<stem>.glb, the installed GLB before its first repair (2026-10-22
behaviour: drops everything since; copied from assets_source when missing); a path to a .glb (one stem only).
The source is copied to work/[<run>/]<stem>/installed.glb (also the rollback copy) and its sha256 recorded.
Writes work/<stem>/<step>.glb per step, work/<stem>/result.json and, for the chosen step, export/<stem>.glb.
LOD_REPAIR_RUN=<name> writes to work/<name>/<stem> instead and skips the export (experiments, batches).

Ladder (--ladder, default `fallback`; steps are LOD2/LOD3 ratios of LOD0, a `c` prefix = curvature-weighted collapse,
build_lods.py LOD_CURVATURE_WEIGHT, weight 8 unless that variable is set):
  plain     r25_12, r30_16, r35_20, r40_25 (the 2026-10-22 ladder)
  fallback  the plain ladder, then the same four curvature-weighted (c25_12 .. c40_25), then 45/30 plain and curved
            (r45_30, c45_30; still below LOD1's 50 %): thin features (wing bones, twigs, ribs, feather cards) that
            the plain collapse erodes (lod-step1b, 2026-11-12)
  <spec>    comma-separated steps, e.g. `0.25/0.125,c0.4/0.25` (also LOD_LADDER=<spec>, the fork's variable)
--not-worse: a passing step must also be no worse than the installed far levels (outline + 0.5 points, colour + 1.0
at LOD2 and LOD3), else the ladder goes on (batch reruns of models that already pass). When no step is accepted the
result keeps the step closest to the gate (smallest worst ratio of score to limit) for review, marked not passing.
LOD_LINING_FIX=0 (build_lods.py, transfer_textures.py) turns the default lining fix off.
Usage: repair.py [--source installed|original|<glb>] [--ladder plain|fallback|<spec>] [--not-worse] <stem>...
       (model in assets_source/worlds/*/models/<stem>.glb)"""
import argparse
import csv
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
ROOT = HERE.parents[3]
PYTHON = os.environ.get('LOD_REPAIR_PYTHON', 'python3')  # needs pymeshlab, numpy, scipy (README)
PLAIN = [(0.25, 0.125), (0.3, 0.16), (0.35, 0.2), (0.4, 0.25)]
LADDERS = {'plain': [(r2, r3, False) for r2, r3 in PLAIN],
           'fallback': [(r2, r3, False) for r2, r3 in PLAIN] + [(r2, r3, True) for r2, r3 in PLAIN]
           + [(0.45, 0.3, False), (0.45, 0.3, True)]}
CURVATURE = os.environ.get('LOD_CURVATURE_WEIGHT') or '8'
NOT_WORSE = {'outline': 0.5, 'colour': 1.0}
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


def ladder_steps(spec):
    """(LOD2 ratio, LOD3 ratio, curvature-weighted) per step of a named ladder or a spec `0.25/0.125,c0.4/0.25`."""
    if spec in LADDERS:
        return LADDERS[spec]
    steps = []
    for item in spec.split(','):
        item = item.strip()
        curved = item.startswith('c')
        r2, r3 = (float(x) for x in item.lstrip('c').split('/'))
        steps.append((r2, r3, curved))
    return steps


def not_worse(entry, levels):
    """The step's far levels score no worse than the installed ones beyond the noise tolerance."""
    return all(entry['repaired'][k][0] <= entry['installed'][k][0] + NOT_WORSE['outline']
               and entry['repaired'][k][1] <= entry['installed'][k][1] + NOT_WORSE['colour'] for k in levels)


def gate_ratio(entry, levels):
    """Worst ratio of score to gate limit over the step's levels (below 1 = passes)."""
    lod1 = entry['installed'][1]
    worst = 0.0
    for k in levels:
        outline, colour = entry['repaired'][k]
        limit_outline, limit_colour = GATE[k]
        if k == 2:
            limit_colour = max(limit_colour, lod1[1] + 3)
        worst = max(worst, outline / limit_outline, colour / limit_colour)
    return worst


def source_glb(stem, choice):
    installed = next(ROOT.glob(f'assets_source/worlds/*/models/{stem}.glb'))
    if choice == 'installed':
        return installed, installed
    if choice == 'original':
        original = PROJECT / 'originals' / f'{stem}.glb'
        if not original.exists():
            original.parent.mkdir(exist_ok=True)
            shutil.copy(installed, original)
        return original, installed
    return Path(choice).resolve(), installed


def repair(stem, choice, ladder, require_not_worse):
    origin, installed = source_glb(stem, choice)
    run_name = os.environ.get('LOD_REPAIR_RUN', '')
    work = PROJECT / 'work' / run_name / stem
    work.mkdir(parents=True, exist_ok=True)
    log = work / 'repair.log'
    log.write_text('')
    # Work from a private copy: the installed file can change under a long run (another stream's install).
    source = work / 'installed.glb'
    shutil.copy(origin, source)
    node = lod_node(source)
    result = {'source': str(origin.relative_to(ROOT)) if origin.is_relative_to(ROOT) else str(origin),
              'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'world': installed.parts[-3], 'node': node, 'ladder': ladder, 'not_worse': require_not_worse,
              'lining_fix': os.environ.get('LOD_LINING_FIX', '1') != '0', 'steps': []}
    chosen = None
    levels = [level for level in (2, 3) if level <= lod_count(source, node)]
    if not levels:
        raise ValueError(f'{stem}: no LOD2 or LOD3 to repair')
    for r2, r3, curved in ladder_steps(ladder):
        step = f'{"c" if curved else "r"}{round(r2 * 100)}_{round(r3 * 100)}'
        ratios = {2: r2, 3: r3}
        built, baked = work / f'{step}.built.glb', work / f'{step}.glb'
        bake_dir = work / f'bake_{step}'
        build_env = {'LOD_CURVATURE_WEIGHT': CURVATURE if curved else '0'}
        try:
            try:
                run([PYTHON, HERE / 'build_lods.py', source, node, built, ','.join(f'{k}:{ratios[k]}' for k in levels)], log,
                    build_env)
            except subprocess.CalledProcessError as error:
                if error.returncode >= 0:
                    raise
                # MeshLab crashed (signal): retry with topology preserved, recorded in the result.
                run([PYTHON, HERE / 'build_lods.py', source, node, built, ','.join(f'{k}:{ratios[k]}' for k in levels)], log,
                    {**build_env, 'LOD_PRESERVE_TOPOLOGY': '1'})
                result.setdefault('preserve_topology', []).append(step)
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
        run([HERE / 'audit.sh', audit, work / 'installed.glb', baked], log)
        table = scores(audit)
        lod1 = table[('installed', 1)]
        entry = {'step': step, 'ratios': [ratios[k] for k in levels], 'curvature': curved,
                 'installed': {k: table[('installed', k)] for k in [1] + levels},
                 'repaired': {k: table[(step, k)] for k in [1] + levels}}
        entry['pass'] = {k: passes(table[(step, k)], k, lod1) for k in levels}
        entry['not_worse'] = not_worse(entry, levels)
        result['steps'].append(entry)
        shutil.copytree(audit, work / f'audit_{step}', dirs_exist_ok=True)
        print(stem, step, entry['repaired'], entry['pass'], 'not worse' if entry['not_worse'] else 'worse', flush=True)
        if all(entry['pass'].values()) and (entry['not_worse'] or not require_not_worse):
            chosen = step
            break
    accepted = chosen is not None
    if chosen is None:
        # Keep the step closest to the gate for review; the result marks it as not accepted.
        candidates = [s for s in result['steps'] if 'error' not in s]
        chosen = min(candidates, key=lambda s: gate_ratio(s, levels))['step'] if candidates else None
    result['chosen'] = chosen
    result['passed'] = bool(chosen) and all(next(s for s in result['steps'] if s.get('step') == chosen)['pass'].values())
    result['accepted'] = accepted
    if chosen and not run_name:
        (PROJECT / 'export').mkdir(exist_ok=True)
        shutil.copy(work / f'{chosen}.glb', PROJECT / 'export' / f'{stem}.glb')
    (work / 'result.json').write_text(json.dumps(result, indent=1) + '\n')
    print('RESULT', stem, chosen, 'accepted' if accepted else ('pass, worse' if result['passed'] else 'NOT PASSING'),
          flush=True)


def main():
    parser = argparse.ArgumentParser(description='Repair the far LODs of installed creatures (module docstring).')
    parser.add_argument('--source', default='installed', help='installed (default), original, or a .glb (one stem)')
    parser.add_argument('--ladder', default=os.environ.get('LOD_LADDER', 'fallback'),
                        help='plain, fallback (default) or a spec such as 0.25/0.125,c0.4/0.25')
    parser.add_argument('--not-worse', action='store_true',
                        help='a passing step must also score no worse than the installed far levels')
    parser.add_argument('stems', nargs='+')
    arguments = parser.parse_args()
    if arguments.source not in ('installed', 'original') and len(arguments.stems) != 1:
        parser.error('--source <glb> takes one stem')
    ladder_steps(arguments.ladder)
    for stem in arguments.stems:
        repair(stem, arguments.source, arguments.ladder, arguments.not_worse)


if __name__ == '__main__':
    main()
