"""Independent review of a run by Codex (its default model, gpt-6-astra): concept against result, one job per shot.

  python3 source/astra_review.py [--map <stem>] review/<run> [shot ...]

For every shot with a concept (concepts/<shot>_A.png, or the study's v0X_A_target.png for the pilot views) the
reviewer gets concept, original and result; close-ups (close_*) get original and result only and are judged by the
rules alone. It writes review/<run>/astra/<shot>.md: every difference that matters, then a last line
`VERDICT: PASS` or `VERDICT: FAIL`. It is given the images and the rules, never our own notes on the run.
"""
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT.parents[2]
STUDY = ROOT / 'level_generation/geometry_study_20261111/concepts'
PILOT_CONCEPTS = {'tavern_v01': 'v01', 'armory_v03': 'v03', 'goblinwatch_v07': 'v07', 'bridge_v08': 'v08'}
PARALLEL = 8  # two map reviews may overlap: 16 Codex sessions at most
sys.path.insert(0, str(PROJECT / 'source'))
import maps  # noqa: E402

RULES = """Rules every addition must meet (these are what the user checks):
1. Material: every added piece (coping, caps, sills, plinths, bands, quoins, roof caps, fascia, posts) must belong
   to the material it sits on: the same colour family and grain as that wall or roof, at most a little lighter and
   smoother (dressed). A piece that looks pasted on (light grey on dark stone, white on red wood, red-brown on an
   orange roof) is a failure.
2. Size and outline: features the concept shows must have the concept's size, thickness, overhang and outline
   (a thick overhanging capstone is not matched by a thin strip; a pyramid cap is not matched by a flat band).
3. Support: nothing may hang in the air or stick out past the edge it stands on (a post base wider than the
   platform under it, a sill floating off the wall, a band past a corner).
4. Presence: every feature the concept adds is in the result; nothing is in the result that the concept does not
   have and that looks wrong.
5. Unchanged: textures, colours, lighting and composition of the original buildings stay as in the original."""

PROMPT = """You are reviewing a geometry upgrade of a Might and Magic VI town in a real-time game engine. Look at the
attached images carefully at full size; zoom into crops with a quick script if details are small.

{inputs}

{rules}

Write your review to {out} (markdown, overwrite it):
- One numbered line per difference that matters, most visible first: the object and where it is in the image,
  what the {target} shows, what the result shows, and which rule it breaks. Be concrete about size, colour and
  shape. Leave out differences in trees, characters, sky and clouds, and differences too small to see at 800 px wide.
- Then one line per feature that is right (short).
- Last line exactly `VERDICT: PASS` when a player comparing the images would say the result matches the {target}
  (no rule broken visibly), otherwise `VERDICT: FAIL`.
Do not modify any other file. Do not generate images."""


def concept_of(shot, stem='oute3'):
    name = shot.split('-', 1)[1] if shot[:2].isdigit() and '-' in shot else shot
    if stem == 'oute3' and name in PILOT_CONCEPTS:
        return STUDY / f'{PILOT_CONCEPTS[name]}_A_target.png'
    path = maps.concepts(stem) / f'{shot}_A.png'
    return path if path.exists() else None


def main():
    args = sys.argv[1:]
    stem = 'oute3'
    if '--map' in args:
        stem = args.pop(args.index('--map') + 1)
        args.remove('--map')
    run = Path(args[0]).resolve()
    out_dir = run / 'astra'
    out_dir.mkdir(exist_ok=True)
    shots = args[1:] or sorted(p.stem for p in run.glob('*.png'))
    jobs = []
    for shot in shots:
        concept = concept_of(shot, stem)
        name = shot.split('-', 1)[1] if '-' in shot else shot
        if concept is None and not name.startswith('close_'):
            continue
        images, lines = [], []
        if concept is not None:
            images.append(concept)
            lines.append(f'Input {len(images)}: the CONCEPT (target look, an image edit of the original).')
        original = maps.original(stem) / f'{shot}.png'
        if original.exists():
            images.append(original)
            lines.append(f'Input {len(images)}: the ORIGINAL game screenshot before the upgrade.')
        images.append(run / f'{shot}.png')
        lines.append(f'Input {len(images)}: the RESULT, the game screenshot after the upgrade (judge this one).')
        target = 'concept' if concept is not None else 'rules'
        out = out_dir / f'{shot}.md'
        prompt = PROMPT.format(inputs='\n'.join(lines), rules=RULES, out=out, target=target)
        args = ['codex', 'exec', prompt, '-c', 'model_reasoning_effort=high', '-C', str(ROOT), '-s',
                'workspace-write', '-o', str(out_dir / f'{shot}.last.md')]
        for image in images:
            args += ['-i', str(image)]
        jobs.append((shot, args, out))
    running = []
    for shot, args, out in jobs:
        while len(running) >= PARALLEL:
            running.pop(0)[1].wait()
        log = open(out_dir / f'{shot}.log', 'w')
        running.append((shot, subprocess.Popen(args, cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log,
                                               stderr=subprocess.STDOUT)))
    for _, job in running:
        job.wait()
    for shot, _, out in jobs:
        text = out.read_text().strip() if out.exists() else ''
        verdict = text.splitlines()[-1] if text else 'MISSING'
        print(f'{shot}: {verdict}')


if __name__ == '__main__':
    main()
