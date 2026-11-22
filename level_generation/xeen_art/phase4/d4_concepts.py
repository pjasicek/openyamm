#!/usr/bin/env python3
"""MU-4 eye-level concepts for D4 Lakeside and Blackfang: one `codex exec` image call per picture (A6, phase 4).

    d4_concepts.py paint arrival|signature [--note TEXT]   -> d4/raw/d4_<view>_vN.png, its prompt (.txt) and log

As phase3/d1_concepts.py: reference 1 is d4_render.py's blockout of the sketch's camera (red marks where the named
things stand); the others give the look (the MU-5 Darkside house painting, the towers kit, the xeendark1 sky in
game). Raw returns are kept unchanged.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent
sys.dont_write_bytecode = True      # leave phase2's folder untouched
sys.path.insert(0, str(ART / 'phase2'))
from concepts import WORKER  # noqa: E402  (the same one-image worker brief)

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for an outdoor map of a new
world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a
person's eye height, landscape format. Hand-painted, slightly stylised, the look of Might and Magic VI-VIII outdoor
maps re-imagined with richer painted detail: readable shapes, game-ready proportions (roads 3-4 m wide, doors and
people at human scale, trees spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below and beyond it a black starfield. This is its shadowed face, the Darkside: by day the sky is a low
amber-gold cloud band at the horizon under a muted dusky zenith, with a small, pale, weak sun; the light is the colour
of old brass; greens are desaturated, rock and roofs are grey slate.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the shores, the island, the crag, the hills and the town stand in the frame, and how large they
are. Its grey, brown and olive boxes are buildings, towers and trees at those positions. The small red circles and
red words only say what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': ['phase4/d4/blockout_arrival.png', 'mu5_houses/paintref_darkside_town.png',
                 'sky/check/02-xeen_darkside_day-12.png'],
        'prompt': """
The scene: Lakeside and Blackfang, the arrival. The player has just come over a heath ridge on the road from the
south and looks north, about 75-degree field of view, down over a lake country opening below. Daytime under the
amber sky of Reference 3: a low amber-gold cloud band at the horizon, a dusky mauve-brown zenith, a small pale sun;
long soft shadows, a little haze over the water.
- Foreground and middle: dry olive-and-ochre heath with heather and a few wind-bent pines; a pale pebble road runs
  from the bottom of the frame down the slope to a small fork with a stone wellhead and a wooden signpost, then on to
  the town.
- Left half, below: Lakeside, a small low town on the lake shore: about fifteen grey rounded boulder-stone houses and
  a few dressed grey-ashlar buildings (Reference 2's style exactly: boulder-stone walls, dark timber posts, dark slate
  roofs, chimneys), round a little flagstone square; one larger two-storey ashlar guildhall; a grey plank jetty
  running out into the water with a small ferry boat moored at its end and a second, smaller boat pulled up on the
  shingle beside it. Shutters closed, an uneasy stillness; a thin smoke or two.
- Centre: the lake, wide, dark and still, steel-blue near the shore and almost black farther out. In its middle a rocky
  island of dead grey trees with a ruined round stone tower.
- Right of centre, far across the water on the north shore: a tall black crag rising straight from the lake, and on
  its top Castle Blackfang, a dark castle of slate-blue stone with tall thin towers and dark slate cone roofs, a few
  windows lit; around its towers a swirling dark cloud of bats, like a storm.
- Far left on the horizon: a snow-capped grey mountain over a dark forest.
- Right edge: grey crags; at the far right the lake narrows to a race of water that pours over the edge of the world,
  and above that north-east horizon the sky glows a paler gold, as if a brighter world lay beyond.
Mood: a beautiful, cold, haunted lake country; the town is quiet and frightened.""",
    },
    'signature': {
        'refs': ['phase4/d4/blockout_signature.png', 'kits/towers_sheet.png', 'sky/check/02-xeen_darkside_day-12.png'],
        'prompt': """
The scene: Lakeside and Blackfang, the signature view, about 60-degree field of view. Late afternoon under the amber
sky of Reference 3. The player stands at the end of a grey plank ferry jetty on the south shore of a great dark lake
and looks north-north-east across the water.
- Lower half: the lake, dark steel-blue and still, small ripples, the pale reflection of the sky; nothing in the
  foreground but water and the jetty's last planks at the very bottom edge.
- Left of centre, a few hundred metres out: the Isle of Lost Souls, a low rocky island of grey stone and dead white
  trees, old leaning grave stones, and a ruined round tower of grey stone with a broken top and one dark doorway.
- Centre-right, beyond the island, rising straight out of the water from the far shore: a tall crag of black rock
  with a sheer cliff face into the lake. On its top Castle Blackfang: a dark vampire's castle of slate-blue coursed
  stone and black rubble (Reference 2: the slate-blue and black tower stone with carved skull friezes), tall slender
  towers with steep dark slate cone roofs, one narrow lit window on each storey of each tower, a heavy keep. Around
  the towers a great swirling storm of black bats, thick like smoke, wheeling round the castle. At the crag's foot on
  the shore, a squat gatehouse with a great closed double gate.
- Left, far: a snowy upland with a white river tumbling down rapids into the lake.
- Right: the lake runs on to a grey headland; above the north-east horizon the sky glows a paler gold, as if a
  brighter world lay beyond the edge.
Mood: dread and beauty; the castle is unreachable across the water.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = HERE / 'd4' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd4_{args.view}_v*.png')))
    target = raw / f'd4_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str(ART / ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print('d4', args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
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
