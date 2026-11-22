#!/usr/bin/env python3
"""X6's MU-4 eye-level concepts: one `codex exec` image call per picture (A5, 2026-11-20).

    paint_x6.py VIEW [--note TEXT]      mockups/raw/x6_<view>_vN.png, the prompt beside it (.txt) and the log (.log)

The route is D3's (paint_d3.py) and X4's (paint_x4.py): reference 1 is render_x6.py's blockout of the sketch's
camera (composition), the others give the look (MM8 Ironsand and MM7 Bracada for the desert ground, the towers kit
sheet for Castle Basenji, the shipped Cloudside sky). Raw returns are kept unchanged; one call per view, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x6') / 'mockups'
ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / 'level_generation/xeen_art'

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image(s) as reference images and the IMAGE PROMPT below.
   Output size: 1536x1024 (landscape).
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for an outdoor map of a new
world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a
person's eye height, about 80-degree field of view, landscape format. Hand-painted, slightly stylised, the look of
Might and Magic VI-VIII outdoor maps re-imagined with richer painted detail: readable shapes, game-ready proportions
(roads 3-4 m wide, doors and people at human scale, plants and palms spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield, visible even by day. This is the world's bright face: a hot, clear day, a pale
blue sky bleaching to a warm white haze at the horizon, a high bright sun, strong light and short shadows (the
shipped "clear" sky with a dry, arid tint). Ground and plants like Reference 2: ochre and tan sand, dry thorn
scrub, a few rocks; MM8 brightness.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the castle, sphinxes, mesas, palms, buildings and rim stand in the frame, and how large they
are. Its coloured boxes are buildings, walls and statues, dark cones are tower roofs, ovals on sticks are trees and
palms. The small red circles and red words only say what stands there: paint the thing itself and never the
circles, words or boxes.
No text, no labels, no letters, no signs with writing, no frame, no user interface, no characters in the
foreground, no modern objects."""

VIEWS = {
    'arrival': {
        'refs': [HERE / 'blockout_arrival.png', ART / 'mu2_materials/views/mm8_out04/01-centre-n.png',
                 ART / 'kits/towers_sheet.png', ART / 'sky/check/11-fair-12.png'],
        'prompt': """
The scene: the Desert of the Sphinx, the arrival from the east. Midday, hot and clear (Reference 4's sky, paler and
drier). The player has just come over a low saddle on a pebbled caravan road and looks west-north-west across a wide,
flat desert pan of hard tan sand and cracked clay with sparse dry scrub.
- Centre-left, a few kilometres off along the road: a small caravan stop - a cluster of date palms round a well, a
  low flat-roofed tavern and a stables of ochre plaster and fieldstone with striped cloth awnings, a camel pen behind
  (tiny at this distance).
- Right, in the middle distance: a colossal sandstone sphinx lying in the dunes, facing left (south), its paws
  stretched out in front of it, its lion body long and low and its head raised, weathered pale ochre stone; low
  rolling dunes round it. Its size reads clearly against the palms: it is many times taller than any house.
- Between the caravan stop and the sphinx, further off: two or three flat-topped red-rock mesas with steep sides,
  and a small red rock knoll with a thin dark stone obelisk on top.
- Far off on the horizon slightly right of centre, small and hazy: a dark castle of grey rubble stone and black
  timber with pointed black slate tower roofs (Reference 3's wizard-tower style), standing on top of a high cliff;
  behind the castle there is nothing but sky, because the world ends there.
- Left edge: low dry downs with a few rocks.
- Foreground: the pebbled road running away from the viewer toward the palms, dry scrub, a few stones.
Mood: heat, glare and silence; a vast desert with a sleeping giant in it.""",
    },
    'signature': {
        'refs': [HERE / 'blockout_signature.png', ART / 'mu2_materials/views/mm8_out04/01-centre-n.png',
                 ART / 'sky/check/11-fair-12.png'],
        'prompt': """
The scene: the Desert of the Sphinx, the signature view: the desert ends at the edge of the world. Late afternoon,
clear and hot, warm low light from the left (Reference 3's sky, drier). The player stands on a dune crest in high
golden dunes and looks north-west along the world's west edge.
- Left half: the dunes run on to the edge of the world and simply end: the sand pours over a sheer lip like a slow
  waterfall of sand, and the wind tears long streams and veils of sand off the lip, drifting out into empty space.
  Below and beyond the lip, under the horizon line, a black starfield (the space under the floating world) fills the
  lower left of the frame; the edge runs away from the viewer into the distance.
- Right of centre, in the middle distance: a second, smaller sphinx of weathered sandstone buried in the dunes up to
  its shoulders, only its head, neck and the top of its back showing, facing right; sand drifted against its chest.
- Far off on the right horizon, very small and hazy: a dark castle with pointed black roofs standing on a high cliff
  at the far corner of the world; a few date palms and a tiny stone hut with an awning nearer, beyond the sphinx.
- Foreground: rippled sand of the dune crest with wind ripples, a few dry grass tufts.
Mood: awe and loneliness at the end of the world; the sand going on falling into the stars.""",
    },
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('view', choices=sorted(VIEWS))
    parser.add_argument('--note')
    args = parser.parse_args()
    view = VIEWS[args.view]
    raw = HERE / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'x6_{args.view}_v*.txt')))
    target = raw / f'x6_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print(args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


if __name__ == '__main__':
    main()
