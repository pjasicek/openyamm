#!/usr/bin/env python3
"""MU-4 eye-level concepts for D6 The Forbidden Zone: one `codex exec` image call per picture (A6, phase 5).

    d6_concepts.py paint arrival|signature [--note TEXT]   -> d6/raw/d6_<view>_vN.png, its prompt (.txt) and log

As phase4/d4_concepts.py: reference 1 is d6_render.py's blockout of the sketch's camera (red marks where the named
things stand); the others give the look (the Ancient technology kit sheet, the xeendark1 sky in game). Raw returns are
kept unchanged.
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
people at human scale, rocks and ruins spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below and beyond it a black starfield. This is its shadowed face, the Darkside: by day the sky is a low
amber-gold cloud band at the horizon under a muted dusky zenith, with a small, pale, weak sun; the light is the colour
of old brass. This map is a volcanic waste: grey ash plains, black basalt, rivers and lakes of glowing orange lava with
dark cracked crust at their edges, and fine grey ash drifting down through the air like dull snow. The machines of a
vanished star-faring race (the Ancients) are dark teal-grey riveted steel with glowing cyan lines (Reference 2).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the lava, the castle, the pod, the hills and the road stand in the frame, and how large they
are. Its boxes are buildings, towers and machines at those positions. The small red circles and red words only say
what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': ['phase5/d6/blockout_arrival.png', 'kits/ancient_sheet.png', 'sky/check/02-xeen_darkside_day-12.png'],
        'prompt': """
The scene: The Forbidden Zone, the arrival. The player has just climbed a long mountain road to a saddle of black rock
(Griffin Pass) and looks north, about 75-degree field of view, down over a volcanic waste opening below. Daytime under
the amber sky of Reference 3: a low amber-gold cloud band at the horizon, a dusky brown zenith, a small pale sun; grey
ash falling gently through the whole picture; a red underglow on the haze above the lava.
- Foreground: the top of the pass, broken black and grey rock and ash; a pale pebble road winds down from the bottom
  of the frame into the plain to a small fork.
- Middle, right of centre: a lake of glowing orange lava in a basin of black crust, and standing in it, nose-up and
  half sunk, a crashed escape pod of the Ancients: a tall scorched capsule of dark riveted steel, lit red and orange
  from below by the lava, steam and heat shimmer round it.
- Far, left of centre: on a flat-topped basalt mesa ringed by a horseshoe of glowing lava, Castle Alamar: a severe
  fortress of dark teal steel and black stone with square towers and a keep, EVERY window lit a cold white, thin cyan
  energy-field curtains humming between steel pylons on its approach. Small with distance but unmistakable.
- Far left at the horizon: lava pouring over the world's edge into the black starfield (a lava fall at the rim), its
  smoke rising.
- Right: a field of grey rock heaved up by buried Ancient metal: plates, spars and broken pylons of teal steel sticking
  out of the ground, going away to a dark ridge.
- The plain between is grey ash and cinder, a few black dead trees, low basalt ridges.
Mood: forbidden, hot and deathly still; the castle watching.""",
    },
    'signature': {
        'refs': ['phase5/d6/blockout_signature.png', 'kits/ancient_sheet.png', 'sky/check/02-xeen_darkside_day-12.png'],
        'prompt': """
The scene: The Forbidden Zone, the signature view, about 60-degree field of view. Afternoon under the amber sky of
Reference 3, with grey ash drifting down through the air. The player stands on a black crust shore and looks west
across a lake of lava.
- Lower third: the lava lake, glowing orange and yellow with darker cracked crust plates floating on it, its heat
  lighting everything from below; the near shore black, cracked and steaming.
- Left of centre, in the middle distance: Corak's escape pod, a tall capsule of dark riveted teal-grey steel standing
  nose-up out of the lava, half sunk, its hull scorched black and buckled at the waterline (Reference 2's burnt hull
  plating), glowing red where the lava touches it, a round hatch midway up its side facing the viewer just above a
  low tongue of black crust; a small black islet with a glinting golden lamp just right of it.
- Right of centre, far beyond the lake and a moat of lava: Castle Alamar on its flat-topped basalt mesa: a fortress of
  dark teal steel and black stone, square towers and a keep, every window lit a cold white, cyan energy-field curtains
  glowing between tall steel pylons on the ramp up to its gate. Smaller with distance but clear against the amber
  band.
- Far: the grey ash plain, low basalt ridges, the amber cloud band, a small pale sun.
Mood: awe and heat; the pod is a fallen star, the castle a cold eye beyond it.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = HERE / 'd6' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd6_{args.view}_v*.png')))
    target = raw / f'd6_{args.view}_v{version}.png'
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
    print('d6', args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
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
