#!/usr/bin/env python3
"""X4's MU-4 eye-level concepts: one `codex exec` image call per picture (A5, 2026-11-20).

    paint_x4.py VIEW [--note TEXT]      mockups/raw/x4_<view>_vN.png, the prompt beside it (.txt) and the log (.log)

The route is A6's (level_generation/xeen_art/phase2/concepts.py, mu1_world/mu1.py `paint`): reference 1 is
render_x4.py's blockout of the sketch's camera (composition), the others give the look (MM8 out03 in game, the
Cloudside house kit painting, the royal castle kit sheet). Raw returns are kept unchanged.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x4') / 'mockups'
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
person's eye height, landscape format. Hand-painted, slightly stylised, the look of Might and Magic VI-VIII outdoor
maps re-imagined with richer painted detail: readable shapes, game-ready proportions (roads 3-4 m wide, doors and
people at human scale, trees spaced as in a game map, not a photograph, not a dense forest). Ground and trees like
Reference 2 (shipped MM8 grass, broadleaf trees).
The world is flat: a square continent floating in space; at its north edge the land ends in a sheer cliff and below
it lies a black starfield (not visible in every view).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the castle, hills, river, road and mountains stand in the frame, and how large they are. Its
coloured boxes and ovals are buildings, stands, pavilions and trees at those positions. The small red circles and
red words only say what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no signs with writing, no frame, no user interface, no characters in the
foreground, no modern objects."""

VIEWS = {
    'arrival': {
        'refs': [HERE / 'blockout_arrival.png', ART / 'mu2_materials/views/mm8_out03/01-centre-n.png',
                 ART / 'mu5_houses/paintref_cloudside_town.png'],
        'prompt': """
The scene: Burlock Savannah, the arrival from the south. A fair, dry late-summer afternoon, warm light, a few high
clouds. The player stands on a pebbled road at the top of a gentle rise, having just come up from the river gorge
behind (south), and looks north-north-west across a rolling savannah of golden, patchy grass with scattered
broadleaf trees and dry hollows of cracked earth.
- Left: the land falls to the Great River, a modest blue river in a shallow green-banked valley running away to the
  north; on its near bank a small wooden landing: a plank jetty on posts, a mooring post and a little timber
  boathouse with a shingle roof (Reference 3's poor-grade house style).
- Centre: the road runs down to a fork with a wooden signpost, then on north beside the river; far up that road a
  single covered merchant's wagon with two mules stands by the roadside. Very far off in the middle of the frame, on a
  rise, the small pale silhouette of a white castle with grey slate cone roofs and banners (tiny at this distance).
- Right: rounded hills of red rock and red earth with sparse dry grass and a few bushes (the red dwarf hills),
  rising toward the right edge.
- Horizon across the frame: a long range of bare grey mountains, hazy with distance, jagged peaks, no snow, no
  trees on them.
Mood: open, warm, inviting; a royal country of horses and roads.""",
    },
    'signature': {
        'refs': [HERE / 'blockout_signature.png', ART / 'mu2_materials/views/mm8_out03/01-centre-n.png',
                 ART / 'kits/royal_castle_sheet.png', ART / 'mu5_houses/paintref_cloudside_town.png'],
        'prompt': """
The scene: Burlock Savannah, the signature view: Castle Burlock above its jousting lists. A bright fair morning,
crisp light from the right, banners stirring. The player stands at the south end of the King's jousting lists on
dry trodden grass and looks north.
- Right foreground and middle: the lists - a long wooden tilt barrier (a low painted rail on posts) running away
  from the viewer toward the castle, a timber grandstand with a striped canopy on its right side, two small round
  pavilions (one red, one blue, striped, with pennants) at its far end.
- Middle ground across the frame: a low grey stone town wall, and behind it the roofs of a small compact village of
  half-timbered houses (Reference 4: ochre plaster, dark oak beams, shingle roofs) with a stone chapel.
- Behind the village, raised on a rocky rise: Castle Burlock, a royal castle of pale cream ashlar with orange-tan
  quoins and crenellations on grey stone footings (Reference 3: the hc and cs textures), a tall square keep in the
  middle, four round towers with dark slate cone roofs, a gatehouse facing the village, blue-and-gold banners with a
  crowned tower.
- Background, rising above and behind the castle across the whole frame: the Gargoyle Range, high bare jagged
  grey mountains with no snow and no trees; on the right a thin waterfall drops out of the range.
- Savannah grass, a few broadleaf trees left and right, a dirt track along the left side of the lists.
Mood: proud, sunny, chivalric; the royal seat of the land.""",
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
    version = 1 + len(list(raw.glob(f'x4_{args.view}_v*.txt')))
    target = raw / f'x4_{args.view}_v{version}.png'
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
