#!/usr/bin/env python3
"""X3 MU-4 eye-level concepts: one `codex exec` image call per picture (lane A5; the route of A6's mu1.py/concepts.py).

    python3 level_generation/projects/xeen/x3/paint.py arrival [--note TEXT]
    python3 level_generation/projects/xeen/x3/paint.py signature [--note TEXT]

Writes mockups/raw/x3_<view>_vN.png with its prompt (.txt) and log (.log) beside it; raw returns are kept unchanged.
Reference 1 is render.py's blockout of the sketch camera (composition); the others give the look.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOCK = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x3') / 'mockups'
ROOT = HERE.parents[3]
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
Might and Magic VII outdoor maps (Tatalia's swamp, Harmondale) re-imagined with richer painted detail: readable
shapes, game-ready proportions (roads 3-4 m wide, doors and people at human scale, small low buildings, trees spaced
as in a game map, not a photograph, not a modern fantasy blockbuster).
The world is flat: a square continent floating in space; where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the water, shores, hills and buildings stand in the frame, and how large they are. Its grey,
brown and orange boxes are buildings and models at those positions. The small red circles and red words only say
what stands there: paint the thing itself and never the circles, words or boxes.
Reference 2 is an in-game view of a shipped swamp map (Might and Magic VII, Tatalia): copy its ground (muddy dark
green-brown swamp grass and soil), its pale-green willow-like swamp trees and its scale of houses.
No text, no letters, no signs with writing, no labels, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    'arrival': {
        'refs': [MOCK / 'blockout_arrival.png', ART / 'mu2_materials/views/mm7_7out13/06-se-high.png',
                 ART / 'mu5_houses/paintref_cloudside_town.png', ART / 'kits/royal_castle_sheet.png'],
        'prompt': """
The scene: Lifeforce Lagoon, the arrival from the east. A damp, still late afternoon under a pale grey-green
overcast; soft diffuse light, a little haze over the water. The player stands on a pebbled dirt road that comes over
a low grassy gap and runs gently down to the west into swamp country.
- Foreground and middle: rough swamp meadow of patchy green-brown grass, mud and small black pools, clumps of reeds,
  a few pale willow-like swamp trees and one dead grey tree; the road runs ahead, slightly left of centre, down to a
  wooden signpost at a crossroads (no readable text on it).
- Centre, a short way beyond the crossroads: Ebenezer's camp: one large faded red-and-ochre striped canvas tent with
  its flaps open, a small square shrine of rough fieldstone with a dark shingle roof and a plank door (Reference 3's
  fieldstone service house, scaled small), a camp fire with thin smoke, a cart with timber and a few crates.
- Right: a steep green rise climbing above the camp; on its flat top the ruins of a small castle: broken walls of
  weathered brown-grey castle stone (Reference 4's "staged ruin" pieces: rough reddish-brown ashlar, a broken arched
  gateway, an empty window), one stump of a corner tower, rubble and scaffolding poles; a footpath zigzags up to it.
- Left, beyond the meadow and lower: the Lifeforce Lagoon opens out, a wide sheet of still dark green water fringed
  with reeds; far off on a small rock islet in the lagoon stands a tall slender grey wizard tower of rubble stone with
  dark timber bands and a black slate cone roof, small with distance and hazy.
- Far left edge: a soft grey bank of mist lying on the lagoon's far shore (a cursed town hides in it; only a faint
  roof or two shows).
- Behind the ruin on the right, dark wooded hills rise to a bare dark peak.
Mood: quiet, damp, a little melancholy but inviting: the camp's fire is the first warm thing you see.""",
    },
    'signature': {
        'refs': [MOCK / 'blockout_signature.png', ART / 'mu2_materials/views/mm7_7out13/06-se-high.png',
                 ART / 'kits/towers_sheet.png', ART / 'mu5_houses/paintref_cloudside_town.png'],
        'prompt': """
The scene: Lifeforce Lagoon, the signature view. Standing on the lagoon's reedy north shore at the head of a stone
causeway, looking south-east across the water at dusk-like grey light under a low overcast; mist on the water.
- Foreground: a gentle grassy slope with reeds and a few pale swamp willows going down to the water's edge; muddy
  dark green-brown ground as Reference 2.
- Right third: a low causeway of grey stone blocks, two paces wide, runs out from the shore across the still water to
  a rocky islet; on the islet the Tower of High Magic rises tall and slender: a round tower of grey rubble stone in
  its lower storeys, then paler plaster storeys banded with black timber friezes and carved dark posts, small lit
  windows, a steep black slate cone roof with a thin finial (Reference 3: the wizard towers' kit, Bracada style).
  It dominates the right side and reflects in the water.
- Centre, middle distance: a small black rock at the end of a spit of dark stones, just off the far shore (a
  mermaid's rock; no figure needed, or a tiny one sitting on it).
- Left, across the lagoon on its far east shore: Nightshadow, a small huddled town of dark half-timbered houses with
  grey daub and steep dark shingle roofs and one tall thin temple spire (Reference 4's house style, darkest grades),
  half drowned in a thick grey mist that lies only over the town; behind it a bare dark ridge.
- The lagoon: wide, still, dark green-black water with reed beds and lily pads near the shore, pale mist trails.
- At the very horizon far beyond the town, faint and hazy, the land simply ends.
Mood: eerie and beautiful, quiet; the most striking view on the map: the tower and the town in its mist facing each
other across the water.""",
    },
}


def cmd_paint(args):
    view = VIEWS[args.view]
    raw = MOCK / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'x3_{args.view}_v*.txt')))
    target = raw / f'x3_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(MOCK), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1500)
    print(args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('view', choices=sorted(VIEWS))
    parser.add_argument('--note')
    args = parser.parse_args()
    cmd_paint(args)


if __name__ == '__main__':
    main()
