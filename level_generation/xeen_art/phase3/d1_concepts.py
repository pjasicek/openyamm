#!/usr/bin/env python3
"""MU-4 eye-level concepts for D1 Castleview Vale: one `codex exec` image call per picture (A6, phase 3).

    d1_concepts.py paint arrival|signature [--note TEXT]   -> d1/raw/d1_<view>_vN.png, its prompt (.txt) and log

As phase2/concepts.py: reference 1 is d1_render.py's blockout of the sketch's camera (red marks where the named things
stand); the others give the look (the MU-5 Darkside house painting, the royal castle kit, the xeendark1 sky in game).
Raw returns are kept unchanged.
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
person's eye height, about 75-degree field of view, landscape format. Hand-painted, slightly stylised, the look of
Might and Magic VI-VIII outdoor maps re-imagined with richer painted detail: readable shapes, game-ready proportions
(roads 3-4 m wide, doors and people at human scale, trees spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield. This is its shadowed face, the Darkside: by day the sky is a low amber-gold
cloud band at the horizon under a muted dusky zenith, with a small, pale, weak sun; the light is the colour of old
brass; greens are desaturated, rock and roofs are grey slate.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the walls, hills, river, rise and cliff stand in the frame, and how large they are. Its grey,
pale and brown boxes are buildings and models at those positions. The small red circles and red words only say what
stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': ['phase3/d1/blockout_arrival.png', 'mu5_houses/paintref_darkside_town.png',
                 'sky/check/02-xeen_darkside_day-12.png'],
        'prompt': """
The scene: Castleview Vale, the arrival. The player has just stepped out of an ancient stone travel pyramid (behind
the camera, not visible) onto a low grassy knoll and looks south-east at a besieged walled town. Daytime under the
amber sky of Reference 3: a low amber-gold cloud band at the horizon, a dusky mauve-brown zenith, a small pale sun
low on the left; long soft shadows, a little haze.
- Right half: Castleview's town wall, LOW (about two storeys high), of grey rounded boulder-stone with grey dressed
  ashlar at the corners, square towers with dark slate caps, and a squat gatehouse with a heavy closed timber gate and
  a purple-and-grey banner; a small paper notice nailed beside the gate. Behind the wall the dark slate roofs and
  chimneys of low stone houses like Reference 2 (grey boulder-stone walls, dark timber posts, dark slate roofs), a few
  thin smokes; above the roofs one tall round tower of dark stone with a conical slate roof.
- Before the walls, the siege works: a dry ditch, rows of sharpened wooden stakes, broken wicker mantlets and old
  earth trenches, all abandoned. A pale flagstone road runs from the foreground to the gate; beside it, well clear of
  the road, a small wooden market stall with a blank painted signboard.
- Left: the ground falls into a narrow rocky gorge with a river at its bottom. A rope footbridge once spanned it: its
  ropes are sawn through and the two halves hang down against the gorge walls. On the near rim of the gorge stands a
  burnt-out stone watermill, roofless, with blackened timbers and a charred waterwheel.
- Dry olive grass and desaturated greens, grey and slate; the far distance fades into amber haze, low hills beyond.
Mood: a strange, tired, beautiful land under a weak sun; the town is grim but holding out.""",
    },
    'signature': {
        'refs': ['phase3/d1/blockout_signature.png', 'kits/royal_castle_sheet.png',
                 'sky/check/02-xeen_darkside_day-12.png', 'mu5_houses/paintref_darkside_town.png'],
        'prompt': """
The scene: Castleview Vale, the signature view. Late afternoon under the amber sky of Reference 3 (a low amber-gold
band at the horizon, a dusky zenith, a small pale sun). The player stands on a small grassy knoll beside a little open
stone shrine on the south bank of a river and looks north across the vale.
- Foreground and near middle ground: the knoll's grass slopes down to a calm, slow river crossing the whole frame from
  left to right; reeds along it; on the near shallows the wreck of a small wooden boat lies on its side.
- Left of centre, beyond the river, on a rocky rise whose south face is a cliff dropping to the river: Castle
  Kalindra, a royal castle of white stone with round towers, a high keep and purple banners (Reference 2: the royal
  castle kit's white stone and purple banner) - but OUT OF PHASE: the whole castle is translucent and ghostly, faintly
  glowing pale blue-white, the amber sky and the hill visible through its walls, its outlines shimmering and doubled
  like a reflection in a window pane. It must clearly read as a ghost of a castle, not a solid one.
- Centre, in the middle distance across the vale: the Dark Grove, a dense dark forest; from its middle rises one
  enormous tree, three times the height of the others, and a single thin rope hangs straight down into its crown from
  high in the sky, the rope's top lost in the amber clouds.
- Right, further away across open grass: the low grey walls, square towers and dark slate roofs of the walled town
  Castleview (Reference 4's houses), one tall round dark tower among the roofs.
- At the far left edge the land ends at a cliff, the edge of the world, with a black starfield below the horizon
  beyond it.
- Desaturated greens, olive grass, grey stone; soft amber haze over the distance.
Mood: wonder and melancholy; the land's three promises in one look.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = HERE / 'd1' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd1_{args.view}_v*.png')))
    target = raw / f'd1_{args.view}_v{version}.png'
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
    print('d1', args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
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
