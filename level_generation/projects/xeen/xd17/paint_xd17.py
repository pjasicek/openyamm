#!/usr/bin/env python3
"""XD-17's MU-4 eye-level concepts: one `codex exec` image call per picture (A5, 2026-11-20).

    paint_xd17.py VIEW [--note TEXT]      mockups/raw/xd17_<view>_vN.png, the prompt beside it (.txt) and the log

The route is X7's (paint_x7.py): reference 1 is render_xd17.py's blockout of the camera (composition), reference 2 the
approved Cloudside town kit (MU-5, the houses' look), reference 3 X7's approved signature concept (how Mount
Firestone, its black rock and its smoke read). Raw returns are kept unchanged; one call per view, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/xd17') / 'mockups'
ROOT = Path(__file__).resolve().parents[4]
ART = ROOT / 'level_generation/xeen_art'
KIT = ART / 'mu5_houses/raw/cloudside_town_v2.png'
FIRESTONE = ROOT / 'output/studio_cal/x7/mockups/raw/x7_signature_v1.png'

WORKER = """You are an image-generation worker. Do exactly this and nothing else:
1. Call the built-in image_gen tool ONCE using the attached image(s) as reference images and the IMAGE PROMPT below.
   Output size: 1536x1024 (landscape).
2. Copy the generated PNG file unchanged to {target}.
3. Reply with only the absolute path of the copied file.
Do not read other files, do not inspect, edit, resize or retry the result.

IMAGE PROMPT:
{prompt}
"""

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for a small hidden town in a
new world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a
person's eye height, about 80-degree field of view, landscape format. Hand-painted, slightly stylised, the look of
Might and Magic VI-VIII towns re-imagined with richer painted detail: readable shapes, game-ready proportions (lanes
3-4 m wide, doors and people at human scale, houses spaced as in a game map, not a photograph).
The place: Shangri-La, a secret green valley hidden inside the black volcanic flank of Mount Firestone. A ring of
sheer black basalt cliffs, 25-35 metres high and jagged along the top, closes the valley on every side; inside it the
air is cool and clear: bright midday under a clean blue sky with a few white clouds, deep green lawns, flowering
shrubs, fruit trees, flagstone lanes and packed-earth paths, white-plastered houses with timber framing and warm
red-brown tile or thatch roofs in the style of Reference 2 (the approved house kit; use its materials, not its exact
houses). The valley is small and tidy, very pleased with itself, a little whimsical. Over the cliff rim to the
north-east rises the black cone of Mount Firestone with a thin thread of grey smoke (Reference 3 shows how the volcano
reads - take only the black mountain and its smoke, NOT its ash, lava, reddish sky or grey ground: inside the valley
everything is green and bright).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the cliffs, the buildings, the pyramid, the tower, the waterfall and the volcano stand in the
frame, and how large they are. Its flat coloured boxes are buildings (red-brown tops are roofs), the white cylinder
with the gold cone is a tower with a gilded dome, the pale triangle is a small stone pyramid, the white slab on the
cliff is a waterfall, the dark wall is the cliff ring, the dark cone is the volcano and the grey wedge its smoke, tan
strips are paths. The small blue circles and blue words only say what stands there: paint the thing itself and never
the circles, words or boxes.
No text, no labels, no letters, no signs with writing, no frame, no user interface, no characters in the
foreground, no monsters, no modern objects."""

VIEWS = {
    'arrival': {
        'refs': [HERE / 'blockout_arrival.png', KIT, FIRESTONE],
        'prompt': """
The scene: the first view of Shangri-La. The player has just stepped out of a dark, hot cave mouth in the south cliff
(behind the viewer) and looks north into the valley. Midday, cool bright air.
- Foreground: a paved little square of worn flagstones with grass at its edges, opening straight ahead.
- Left: Tavern Xanadu, a two-storey timber-framed inn with white plaster, a deep porch and a hanging sign showing only a
  little domed palace (no letters); a smaller crooked house beyond it.
- Right, close: Arm and Hammer, a long low stone forge with a tall chimney between two doors, a faint wisp of forge
  smoke, an anvil by the wall.
- Centre, beyond the square: a flagstone lane leads to a wide green lawn (the court) with a low round stone well in
  its middle; a white unicorn grazing near it, small in the distance.
- Far end of the valley, centre: a small, perfectly kept stone pyramid on a low terrace against the north cliff.
- Right of centre in the middle distance: a slender round white tower with a gilded dome rising above the roofs.
- Far right on the east cliff: a tall thin white waterfall dropping from a notch in the black rock.
- Everywhere behind: the ring of black basalt cliffs; over the north-east rim the black cone of Mount Firestone with a
  thin thread of smoke, distant and hazy blue-grey.
Mood: relief and surprise - after fire, a green, cool, sunny secret garden town.""",
    },
    'signature': {
        'refs': [HERE / 'blockout_signature.png', KIT, FIRESTONE],
        'prompt': """
The scene: Shangri-La seen from the top of the Public Library's broad stone steps on a low terrace at the valley's
west side, looking east-north-east across the whole valley. Late morning, cool clear light, long soft shadows.
- Foreground: the edge of the library terrace, pale stone steps going down, a few flowerpots; lower left the white
  wall and red roof of a schoolhouse with a little bell cote.
- Middle: a wide green lawn (the court) ringed by a flagstone walk, a low round stone well in its middle, a white
  unicorn grazing beside it; white-plastered houses with timber frames and red-brown roofs around the lawn, each a
  different shape; a round hut with a dark-blue roof painted with little gold stars on the right; lower right, close,
  the red roof corner of a crooked little house.
- Left of centre beyond the lawn: a small stone pyramid on a terrace against the north cliff.
- Centre: a slender round white tower with a gilded dome, the tallest thing in the valley.
- Right of centre beyond the houses: a small cold pool of clear blue water at the foot of the east cliff, a little domed
  garden pavilion with open arches on its far shore, and a tall thin white waterfall pouring into the pool from a
  notch high in the black cliff, mist at its foot.
- Far right: rows of small fruit trees (an orchard), one old gnarled tree among them with a face-like knot in its
  trunk (a talking tree, subtle).
- Behind everything: the ring of jagged black basalt cliffs; above the cliffs, centre, the black cone of Mount
  Firestone with a thin thread of grey smoke against the blue sky.
Mood: a hidden utopia; peaceful, a little smug; green and white against the black rock.""",
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
    version = 1 + len(list(raw.glob(f'xd17_{args.view}_v*.txt')))
    target = raw / f'xd17_{args.view}_v{version}.png'
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
