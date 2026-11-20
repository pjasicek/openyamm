#!/usr/bin/env python3
"""Part 2 of the anim stream (Hit folds), one model after the other (from the repository root):

    hit_batch.py <world>:<id>:<factor> [...]

Per model: claim the lease (skip the model when another agent holds it), back up the installed GLB and actors.yml to
<project>/work/before_hit/, scale every joint of `Hit` toward its own first frame by <factor> (scale_keys.py; rotations
and translations), run finish_model.sh (winding, diff, audit, install, floor, gait, regression, viewer check), take
viewer shots of Hit before/after (shots_sheet.sh), append a dated README section, release the lease. Prints one JSON
line per model; the summary goes to the stream ledger by hand.

Diagnosis (hit_diag/select.py, 17 models): the shared humanoid-set `Unarmed Get Hit F1` turns the torso 46-93 deg in
0.5 s (pelvis up to 53 deg, neck 40); halving its amplitude takes the spine/head/arm folds under 12 % beyond Standing
on all but the dwarf (whose beard is skinned to the spine): the clip, not the weights, on this group.
"""
import fnmatch
import json
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[5]
TOOLS = Path(__file__).resolve().parent
A = TOOLS.parents[1]


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)


def descriptors(world, stem):
    data = yaml.safe_load((ROOT / f'assets_dev/worlds/{world}/models/actors.yml').read_text())
    entries = data if isinstance(data, list) else data['actors']
    return [e['descriptor'] for e in entries if isinstance(e, dict) and Path(e.get('model', '')).stem == stem]


def glob_for(names):
    prefix = names[0]
    for n in names[1:]:
        while not n.startswith(prefix):
            prefix = prefix[:-1]
    return (prefix or names[0]) + '*'


def main():
    for spec in sys.argv[1:]:
        world, ident, factor = spec.split(':')
        stem = f'{world}_{ident}'
        P = Path('level_generation/creatures') / f'{stem}_animfix_claude'
        (ROOT / P / 'review').mkdir(parents=True, exist_ok=True)
        r = run([sys.executable, 'tools/creature_workspace.py', 'claim', '--project', str(P), '--identity',
                 f'{world}:{ident}', '--owner', 'anim-anim'])
        if r.returncode:
            print(json.dumps({'stem': stem, 'skipped': (r.stdout + r.stderr).strip()[-300:]}), flush=True)
            continue
        token = json.loads(r.stdout)['token']
        try:
            bk = ROOT / P / 'work/before_hit'
            bk.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / f'assets_source/worlds/{world}/models/{stem}.glb', bk / f'{stem}.glb')
            shutil.copy(ROOT / f'assets_dev/worlds/{world}/models/actors.yml', bk / f'actors_{world}.yml')
            (ROOT / P / 'export').mkdir(exist_ok=True)
            run([sys.executable, str(TOOLS / 'scale_keys.py'), str(bk / f'{stem}.glb'), str(ROOT / P / 'export' /
                 f'{stem}.glb'), '--clip', 'Hit', '--joints', '*', '--factor', factor, '--ref', 'Hit',
                 '--translation-joints', '*', '--translation-factor', factor], check=True)
            # scaling the pelvis translation can let the feet dip (the Troll Peasant's 2.6 cm): raise only those keys
            exp = ROOT / P / 'export' / f'{stem}.glb'
            run([sys.executable, 'level_generation/creatures/claude_shared/floor/floor_fix.py', str(exp),
                 str(exp.with_suffix('.raised.glb')), '--raise', 'Hit'], check=True)
            exp.with_suffix('.raised.glb').replace(exp)
            names = descriptors(world, stem)
            fin = run(['bash', str(TOOLS / 'finish_model.sh'), str(P), world, stem, glob_for(names), stem],
                      env={**__import__('os').environ, 'BEFORE': 'work/before_hit'})
            out = fin.stdout
            shots = run(['bash', str(TOOLS / 'shots_sheet.sh'), str(P), token, 'hit_viewer_before_after',
                         'Hit:0.15:front:body', 'Hit:0.25:quarter:body', 'Hit:0.25:right:body'])
            changed = [l for l in out.splitlines() if l.startswith('Hit ')]
            ok = ('0 failed' in out and 'PASS' in out and '"consoleErrors": []' in out and 'inverted closed parts: 0' in out
                  and '0 with floor problems' in out)
            readme = ROOT / P / 'README.md'
            head = '' if readme.exists() else f'# {stem}: anim fix (2026-11-11)\n\nStream `anim` of the [MM6–MM8 audit fixes](../audit_mm678_20261111/fixes/ANIM.md).\n'
            with open(readme, 'a') as f:
                f.write(head + f"""
## Part 2: Hit folds the torso (2026-11-11)

The shared humanoid-set `Unarmed Get Hit F1` (or its Mixamo/Armed sibling) bends the torso too far for this body.
Fix (group decision, `../audit_mm678_20261111/fixes/anim_tools/hit_batch.py`): every joint of `Hit` scaled toward the
clip's own first frame by **{factor}** (`scale_keys.py --joints '*' --factor {factor} --ref Hit`, translations too): the
same flinch, timing and contact at a smaller amplitude. Before: `work/before_hit/` (GLB and actors.yml).

```
{chr(10).join(changed)}
```

Checks (`review/finish.txt`): winding, only Hit samplers changed, floor and gait audits, every-binding regression,
viewer check{' all clean' if ok else ' (see finish.txt: not all clean)'}; arm and hand gate: no new deformation, hands
inside the body as the audit's measurement (cmp line above). Sheet `review/hit_viewer_before_after.png` (top installed).
""")
            print(json.dumps({'stem': stem, 'factor': factor, 'ok': ok, 'changed': changed,
                              'sheet': str(P / 'review/hit_viewer_before_after.png'),
                              'shots': shots.stdout.strip()[-200:]}), flush=True)
        finally:
            run([sys.executable, 'tools/creature_workspace.py', 'release', '--project', str(P), '--token', token])


if __name__ == '__main__':
    main()
