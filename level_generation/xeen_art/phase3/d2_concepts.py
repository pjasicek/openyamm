#!/usr/bin/env python3
"""MU-4 eye-level concepts for D2 Sprite Forest and Ogre Pass (A6, phase 3): one `codex exec` image call per picture.

    d2_concepts.py paint arrival|pass [--note TEXT]   -> d2/raw/d2_<view>_vN.png, its prompt (.txt) and log

As phase2/concepts.py (its worker text and the common brief are reused unchanged): reference 1 is d2_render.py's
blockout of the sketch's camera; the others give the look (the Darkside day sky, MU-2 in-game views). Raw returns are
kept unchanged.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent
sys.dont_write_bytecode = True   # nothing written into phase2/ (shared)
sys.path.insert(0, str(ART / 'phase2'))
import concepts as base  # noqa: E402

DARKSIDE = """This map lies on the world's shadowed face (Darkside): by day the sky is a low amber-gold band of cloud at the
horizon under a muted warm sky and a small, pale sun; light is warm and soft, greens are desaturated toward olive and
grey, rock is dark slate. Reference 2 is this world's Darkside sky at noon in the game: match its colours."""

VIEWS = {
    'arrival': {
        'refs': ['phase3/d2/blockout_arrival.png', 'sky/check/02-xeen_darkside_day-12.png',
                 'mu2_materials/views/mm8_out07/01-centre-n.png'],
        'prompt': """
The scene: the Sprite Forest, the arrival from the west. The player stands on a stony dirt road at the edge of an old
enchanted forest, having just come from an open vale behind (west).
- Centre-left: the road runs ahead to a wooden signpost at a fork. The left branch, the wider caravan road, climbs
  away to the left toward stony foothills with scattered trees; the right branch, a narrow forest track, bends right
  into the forest.
- Right two thirds: the Sprite Forest: tall, dark, old broadleaf trees with heavy olive-grey canopies and mossy
  trunks, spaced as in a game map (Reference 3: these game trees, but older, darker and larger). At the trees' feet
  and along the track, clusters of glowing mushrooms: teal-cyan caps softly lit from within, knee to waist high, a few
  as tall as a person, a faint glow on the moss around them.
- Right of centre, far behind the canopy: the great tree of the Temple of Bark, a colossal ancient tree rising three
  to four times higher than the forest, a vast trunk and a huge spreading crown whose top fades into the amber haze,
  faint glowing fungus shelves on its bark. It must read as a landmark a few kilometres away.
- Soft warm haze between the trees; a small pale sun in the amber sky.
Mood: mysterious, quiet and inviting; the forest glows a little even by day.""",
    },
    'pass': {
        'refs': ['phase3/d2/blockout_pass.png', 'sky/check/02-xeen_darkside_day-12.png',
                 'mu2_materials/views/mm7_out10/01-centre-n.png'],
        'prompt': """
The scene: Ogre Pass, where the caravan road crosses a spur of the Gemstone Range. The player stands on the stony
caravan road on an open slope below the pass, looking up the road toward the saddle.
- Left, on a rocky knoll above the road: the west fort of the ogres: a crude palisade of sharpened tree trunks lashed
  with rope, a squat two-storey log blockhouse with a hide-and-plank roof behind it, a gate of logs facing the road,
  ragged hide banners on poles, smoke rising from inside. Two big crude ogres stand by the gate, small in the frame.
- Centre: the road climbs to a saddle between two rocky shoulders. In the saddle a ring of stones round a bonfire
  sending up a tall column of smoke, a crude log seat, a wooden signpost.
- Right, beyond the saddle on its own knoll: the east fort, a second palisade and blockhouse in the same crude style.
- Background, filling the upper frame: the Gemstone Range: dark grey-blue slate crags and peaks; veins and clusters of
  glowing violet and teal crystal break out of the rock faces (Reference 3: a dark rocky mountain map, for the slate).
- On the slopes sparse dark firs, boulders and dry grass; by the road at the left a half-burned, overturned caravan
  wagon.
Mood: rugged and threatening, a toll road held by brutes; the crystals give the mountains a strange beauty.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = HERE / 'd2' / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd2_{args.view}_v*.png')))
    target = raw / f'd2_{args.view}_v{version}.png'
    prompt = base.COMMON + '\n' + DARKSIDE + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE / 'd2'), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str(ART / ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=base.WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print('d2', args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
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
