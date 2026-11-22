#!/usr/bin/env python3
"""D3's MU-4 eye-level concepts: one `codex exec` image call per picture (A5, 2026-11-20).

    paint_d3.py VIEW [--note TEXT]      mockups/raw/d3_<view>_vN.png, the prompt beside it (.txt) and the log (.log)

The route is A6's (level_generation/xeen_art/phase3/d1_concepts.py) and X4's (paint_x4.py): reference 1 is
render_d3.py's blockout of the sketch's camera (composition), the others give the look (the MU-5 Sandcaster house
painting, the sandcaster kit sheet, the xeendark1 sky in game, MM7 Tularean Forest for the trees). Raw returns are
kept unchanged; one call per view, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/d3') / 'mockups'
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
(roads 3-4 m wide, doors and people at human scale, trees spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield. This is its shadowed face, the Darkside: by day the sky is a low amber-gold
cloud band at the horizon under a muted dusky zenith, with a small, pale, weak sun; the light is the colour of old
brass; greens are desaturated. Beyond the east rim, low in the eastern sky, stands the glow of the world's other,
bright face: a pale gold-white band of light rising from behind the edge of the world.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the walls, towers, river, forest and rim stand in the frame, and how large they are. Its
sand-coloured boxes are buildings and walls, cones are towers, triangles are market tents, ovals are trees. The small
red circles and red words only say what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': [HERE / 'blockout_arrival.png', ART / 'mu5_houses/paintref_sandcaster.png',
                 ART / 'sky/check/02-xeen_darkside_day-12.png', ART / 'kits/sandcaster_sheet.png'],
        'prompt': """
The scene: Sandcaster and the Aging Forest, the arrival from the west. Daytime under the amber sky of Reference 3. The
player has just come down a caravan road out of wooded hills (behind) and stands on the road in a dry, open valley of
dusty olive scrub and sand, looking east-north-east.
- Left half: Sandcaster, a walled merchant city on a low sandstone terrace, its walls about two storeys high of
  smooth ochre sandstone with brick quoins and square corner towers (Reference 2 and 4: the t07 ochre and orange
  sandstone, flat gravel and terracotta roofs, pointed windows). Behind the wall the flat roofs and upper storeys of
  sandstone houses. At the far left one tall slender sandstone tower, much taller than the rest, with a short
  wooden jetty sticking out sideways from its very top into empty air (a mooring for sky boats; no boat). In the
  middle of the city, raised on an inner terrace, a cluster of pink-beige ashlar wizard towers with dark pointed
  roofs and balconies.
- Centre, far off along the road: a few striped market awnings and small tents (the Crossroads market), tiny with
  distance; a ruined stone wall stub by the roadside on the right of the road.
- Right: the edge of a forest of old broad trees whose crowns are red, orange and gold as in autumn (the Aging
  Forest), dark green older woods behind them.
- Far east on the horizon, right of centre: the pale gold-white glow rising behind the edge of the world.
- Foreground: dry trodden road and sparse olive scrub, a few small rocks and thorn bushes.
Mood: a hot, busy, slightly sinister merchant city at the edge of a strange forest.""",
    },
    'signature': {
        'refs': [HERE / 'blockout_signature.png', ART / 'sky/check/02-xeen_darkside_day-12.png',
                 ART / 'mu2_materials/views/mm7_7out04/01-centre-n.png'],
        'prompt': """
The scene: Sandcaster and the Aging Forest, the signature view: the River of Wrath falls off the edge of the world.
Late afternoon under the amber sky of Reference 2. The player stands in grassy river meadows on the river's south
bank and looks east.
- Middle ground: a fast, foaming river of blue-green water runs from the left middle across and away from the
  viewer to the right of centre, where it reaches the edge of the world and pours over it: the river simply ends at
  a sheer cliff edge and drops out of sight in a white spray, into blackness.
- Beyond the edge, below the horizon line: a black starfield (the space under the floating world), clearly visible
  past the cliff edge on the right half of the frame.
- Above the edge, low in the eastern sky behind the falls: a broad pale gold-white glow rising from behind the rim,
  the light of the world's other, bright face; it lights the spray and the cliff's lip.
- Left: rising stony hills with a few dark trees, and on a knoll near the edge a tall, slender, dark grey stone tower
  with a pointed slate roof and no windows low down (the Great Eastern Tower), its silhouette against the amber sky.
- Between them, on a small bluff above the falls, the broken stone walls of a ruined watch post.
- Foreground and right: meadow grass, a few broadleaf trees (Reference 3's trees, desaturated), reeds at the
  river's edge.
Mood: awe and loneliness; the end of the world, and the light of another one beyond it.""",
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
    version = 1 + len(list(raw.glob(f'd3_{args.view}_v*.txt')))
    target = raw / f'd3_{args.view}_v{version}.png'
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
