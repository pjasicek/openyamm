#!/usr/bin/env python3
"""MU-4 eye-level concepts for D5 Desert of Doom: one `codex exec` image call per picture (A6, phase 5).

    d5_concepts.py paint arrival|signature [--note TEXT]   -> d5/raw/d5_<view>_vN.png, its prompt (.txt) and log

As phase4/d4_concepts.py: reference 1 is d5_render.py's blockout of the sketch's camera (red marks where the named
things stand); the others give the look (the xeendark1 sky in game, MM6's pyramid stone, the Ancient kit). Raw
returns are kept unchanged.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent
ROOT = ART.parents[1]
sys.dont_write_bytecode = True      # leave phase2's folder untouched
sys.path.insert(0, str(ART / 'phase2'))
from concepts import WORKER  # noqa: E402  (the same one-image worker brief)

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for an outdoor map of a new
world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a
person's eye height, landscape format. Hand-painted, slightly stylised, the look of Might and Magic VI-VIII outdoor
maps re-imagined with richer painted detail: readable shapes, game-ready proportions (roads 3-4 m wide, doors and
people at human scale, trees spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space. This is its shadowed face, the Darkside: by day the sky is a
low amber-gold cloud band at the horizon under a muted dusky zenith, with a small, pale, weak sun; the light is the
colour of old brass; greens are desaturated, rock is red-brown and slate.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the dunes, the pyramids, the boulders, the trees and the road stand in the frame, and how large
they are. Its grey, olive and sand boxes and triangles are boulders, trees and pyramids at those positions; a row of
pale translucent columns far off is a shimmering energy curtain on distant highlands. The small red circles and red
words only say what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': ['phase5/d5/blockout_arrival.png', 'sky/check/02-xeen_darkside_day-12.png',
                 'kits/ancient_sheet.png'],
        'prompt': """
The scene: the Desert of Doom, the arrival. The player has just walked out of a dark fir forest along a level valley
and looks west, about 75-degree field of view, as the desert opens ahead. Daytime under the amber sky of Reference 2:
a low amber-gold cloud band at the horizon, a dusky brown-mauve zenith, a small pale sun; heat haze far off.
- Foreground: the valley floor of dry olive grass and stony soil, a few last dark firs at the frame's edges; a pale
  stony road runs from the bottom of the frame west and down into the desert.
- Middle: the road passes a field of large wind-polished grey boulders standing in the sand beside it, with a small
  weathered wooden sign by the road; beyond, rolling amber dunes.
- Centre, far off (about four kilometres): the Great Pyramid, a huge smooth sandstone pyramid with a gilded capstone,
  rising alone out of the dunes, softened by haze; its shadow side darker.
- Right, nearer, on a slope: a small broken pyramid of dark teal-grey Ancient metal plates (Reference 3's riveted
  steel), cracked open, its capstone fallen and lying at its foot.
- Far right on the horizon: high red-brown cliffs lifting a cold grey plateau, and along it, very faint, a line of tall
  thin metal frames with a pale green shimmering curtain between them.
- Left: high dunes rolling away to the south.
Mood: vast, hot, empty and ominous; the pyramid draws the eye.""",
    },
    'signature': {
        'refs': ['phase5/d5/blockout_signature.png', 'sky/check/02-xeen_darkside_day-12.png',
                 '../textures_x4/masters/mm6/egybigb.png'],
        'prompt': """
The scene: the Great Pyramid of the Dragon Pharaoh, the signature view, about 60-degree field of view. Late afternoon
under the amber sky of Reference 2. The player stands on the crest of a high dune south-east of the pyramid and
looks north-west across the sand.
- Foreground and lower third: rippled amber dunes with sharp wind-cut crests and long soft shadows, a few dry grass
  tufts; no road.
- Centre: the Great Pyramid, huge and alone, rising straight out of the dunes about a kilometre away: a smooth-faced
  pyramid of great pale sandstone blocks (Reference 3's big carved blocks, weathered, a few hieroglyph bands near the
  foot), a gilded gold capstone catching the weak sun; its right face in shadow. Sand drifts heaped against its foot.
  At its left corner a small torn canvas tent, ropes and a ladder against the lowest blocks: a tomb robbers' camp.
- Behind and left of the pyramid: the small pale sun low in the amber-gold cloud band, a soft glow round it, the
  pyramid's apex just to its right.
- Far right on the horizon: red-brown cliffs of a highland and, very faint, a line of thin metal frames with a pale
  green shimmering curtain between them.
Mood: awe, heat and stillness; an ancient thing far older than the desert.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = HERE / 'd5' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd5_{args.view}_v*.png')))
    target = raw / f'd5_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str((ART / ref).resolve())]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print('d5', args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    paint = sub.add_parser('paint')
    paint.add_argument('view', choices=sorted(VIEWS))
    paint.add_argument('--note')
    paint.set_defaults(run=cmd_paint)
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
