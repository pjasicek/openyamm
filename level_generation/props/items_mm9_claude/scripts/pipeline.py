"""Moves designs through every step whose inputs are ready, in order: prep (guides), paint brief, Codex paint
(16 sessions at once), registration, bake and the textured review render. Run it again whenever more inputs exist
(built geometry, downloaded Meshy models); finished steps are skipped.

    python3 -I scripts/pipeline.py [--no-paint] [--rebake] <design> [...]     (no designs: every design of designs.json)

Inputs per design: work/procedural/<d>.glb (blender, plate, hybrid; build_mm9.py) or
meshy/meshy/<d>_st_v1/model_urls_glb.glb (meshy). Writes pipeline_status.json (the step each design reached)."""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESIGNS = json.load(open(os.path.join(HERE, 'designs.json')))
SCRIPTS = os.path.join(HERE, 'scripts')
PREP_PARALLEL = 6
START = __import__('time').time() if '--rebake' in sys.argv else 0


def path(*parts):
    return os.path.join(HERE, *parts)


def source(design):
    if DESIGNS[design].get('geometry') == 'procedural':
        return path('work', 'procedural', f'{design}.glb')
    return path('meshy', 'meshy', f'{design}_st_v1', 'model_urls_glb.glb')


def newest_raw(design):
    folder = path('codex_tex', design)
    raws = [os.path.join(folder, name) for name in os.listdir(folder)
            if name.startswith(('paint_mask_raw_v', 'paint_raw_v'))] if os.path.isdir(folder) else []
    return max(raws, key=os.path.getmtime) if raws else None


def prep(design):
    guide = path('codex_tex', design, 'guide_top.png')
    if os.path.exists(guide) and os.path.getmtime(guide) >= os.path.getmtime(source(design)):
        return design, 'prepared'
    # A rebuilt model invalidates its guides and any painting of them: set the paintings aside.
    folder = path('codex_tex', design)
    stale = [name for name in os.listdir(folder) if name.startswith(('paint_mask_raw_v', 'paint_raw_v'))] \
        if os.path.isdir(folder) else []
    if stale:
        os.makedirs(os.path.join(folder, 'superseded'), exist_ok=True)
        for name in stale:
            os.replace(os.path.join(folder, name), os.path.join(folder, 'superseded', name))
    result = subprocess.run(['blender', '--background', '--python', os.path.join(SCRIPTS, 'codex_texture.py'), '--',
                             'prep', design], capture_output=True, text=True)
    ok = os.path.exists(guide)
    if ok:
        subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, 'mm9item.py'), 'paint-brief', design],
                       capture_output=True, text=True)
    return design, 'prepared' if ok else 'prep failed: ' + result.stdout[-300:].replace('\n', ' ')


REBAKE = '--rebake' in sys.argv


def bake(design):
    raw = newest_raw(design)
    export = path('work', 'codex_tex', f'{design}_export.glb')
    if not REBAKE and os.path.exists(export) and os.path.getmtime(export) >= os.path.getmtime(raw):
        return design, 'baked'
    registered = subprocess.run([sys.executable, os.path.join(SCRIPTS, 'register_views.py'), design],
                                capture_output=True, text=True).stdout.strip().splitlines()
    result = subprocess.run(['blender', '--background', '--python', os.path.join(SCRIPTS, 'codex_texture.py'), '--',
                             'bake', design], capture_output=True, text=True)
    if not (os.path.exists(export) and os.path.getmtime(export) >= max(os.path.getmtime(raw), START)):
        errors = [line for line in result.stdout.splitlines() if 'Error' in line]
        return design, 'bake failed: ' + (errors[-1] if errors else result.stdout[-200:])
    subprocess.run(['blender', '--background', '--python', os.path.join(SCRIPTS, 'review_render.py'), '--', export,
                    path('review', 'final', design)], capture_output=True, text=True)
    registration = registered[-1] if registered else ''
    return design, 'baked' + ('' if 'REGISTERED' in registration else ' (registration: ' + registration + ')')


def main():
    arguments = sys.argv[1:]
    paint = '--no-paint' not in arguments
    designs = [a for a in arguments if not a.startswith('--')] or list(DESIGNS)
    status_path = path('pipeline_status.json')
    status = json.load(open(status_path)) if os.path.exists(status_path) else {}
    ready = [d for d in designs if os.path.exists(source(d))]
    with ThreadPoolExecutor(PREP_PARALLEL) as pool:
        for design, state in pool.map(prep, ready):
            status[design] = state
            print('PREP', design, state, flush=True)
    briefs = [path('codex_tex', d, 'CODEX_BRIEF_paint.md') for d in ready
              if status.get(d) == 'prepared' and not newest_raw(d)]
    if paint and briefs:
        subprocess.run([sys.executable, '-I', os.path.join(SCRIPTS, 'mm9item.py'), 'codex'] + briefs)
    painted = [d for d in ready if newest_raw(d)]
    with ThreadPoolExecutor(PREP_PARALLEL) as pool:
        for design, state in pool.map(bake, painted):
            status[design] = state
            print('BAKE', design, state, flush=True)
    with open(status_path, 'w') as handle:
        json.dump(status, handle, indent=1, sort_keys=True)
        handle.write('\n')
    counts = {}
    for state in status.values():
        key = state.split(':')[0].split(' (')[0]
        counts[key] = counts.get(key, 0) + 1
    print('STATUS', json.dumps(counts))


if __name__ == '__main__':
    main()
