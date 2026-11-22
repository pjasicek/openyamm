#!/usr/bin/env python3
"""MU-4 eye-level concepts for phase 2 maps: one `codex exec` image call per picture (A6).

    concepts.py paint KEY VIEW [--note TEXT]   raw/<key>_<view>_vN.png with its prompt beside it (.txt) and log

The composition comes from the plan: reference 1 is plan_render.py's blockout of the sketch's camera (with red marks
where the named things stand); the other references give the look (MU-2 in-game views, MU-5 house paintings, kits).
The painting is Codex image generation only; raw returns are kept unchanged.
"""
import argparse
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent

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
person's eye height, about 75-degree field of view, landscape format. Hand-painted, slightly stylised, the look of
Might and Magic VI-VIII outdoor maps re-imagined with richer painted detail: readable shapes, game-ready proportions
(roads 3-4 m wide, doors and people at human scale, trees spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the ridge, hills, river and cliff stand in the frame, and how large they are. Its grey and
brown boxes are buildings and models at those positions. The small red circles and red words only say what stands
there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no frame, no user interface, no characters in the foreground."""

VIEWS = {
    ('x5', 'arrival'): {
        'refs': ['phase2/x5/blockout_arrival.png', 'mu2_materials/views/mm7_7out13/01-centre-n.png',
                 'mu5_houses/paintref_cloudside_town.png'],
        'prompt': """
The scene: Winterkill Tundra, the arrival from the east. A cold, bright winter afternoon under a high pale overcast,
soft light, faint blue shadows. The player stands on a stony road on the north bank of a river, having just come
from the warm lagoon country behind (east).
- Left half: the Lagoon Water, a dark open river with snowy banks and drifting ice floes, runs away to the west and
  disappears into a narrow gorge cut through the ridge; south of the river a flat fen of snow broken by brown sedge,
  black pools and scattered dark firs. A small hot spring steams on the near bank.
- Centre: the road runs ahead to a wooden signpost at a fork; from the fork a rough track climbs to the right up a
  long snowy slope toward a notch in the ridge (the pass).
- Background, across the whole frame: the Frostspine, a long wall of bare grey rock and snow, its peaks rising high,
  with the gorge at its left end and the pass notch right of centre. It reads as a barrier between this gentle
  valley and the harsher land beyond.
- Right: the snowy shoulder of the Ogre Hills with a few firs. On it Halon's workshop: a small half-timbered cottage
  (Reference 3: the town houses' style, dark oak beams, ochre plaster, shingle roof under snow) beside a tall narrow
  wooden water-clock tower with a big clock face, a frozen millpond with an iced-up waterwheel, smoke from the
  chimney.
- Snowy firs like Reference 2 (snow-laden pines), spaced as in a game map. Fresh snow everywhere except the dark
  river and the fen; rock shows on the steep faces.
Mood: quiet, cold, inviting; this is the gentle pocket of a harsh map.""",
    },
    ('x5', 'glacier'): {
        'refs': ['phase2/x5/blockout_glacier.png', 'mu2_materials/views/mm7_out10/01-centre-n.png',
                 'kits/ancient_sheet.png'],
        'prompt': """
The scene: Winterkill Tundra, the signature view: the end of the world in the Land of the Giants. Standing on a
rocky ledge at the edge of a high snowy plateau, looking west along the world rim. Winter overcast breaking, a
shaft of pale sunlight on the ice.
- Left third: the land ends in a sheer cliff of grey rock streaked with ice; beyond and below it, the black void of
  space full of stars (no sea, no clouds below: stars).
- Ahead: a great pale blue-white glacier, crevassed and ridged, flows down from between snowy crags and its broad
  tongue breaks off over the cliff edge: huge ice blocks and trails of powder snow tumbling away into the stars, a
  frozen icefall hanging over the void.
- Middle ground, on a rocky spur at the lip just left of the glacier: the Earth Reflector, an ancient machine of
  another age - a tall pylon of dull grey-green metal bearing a large round dish angled up at the sky, faint blue
  light in its panels, half buried in snow (its materials like Reference 3's metal and energy panels).
- Right: the plateau of the giants, wind-scoured snow, huge rounded boulders, a jagged crag of dark rock and snow
  rising high; far off, two one-eyed giants (cyclopes) as small silhouettes beside a ring of standing stones.
- Lower right foreground: the Waters of Great Magic, a round stone basin of glowing blue water steaming in the cold.
Mood: awe, danger and beauty; the most striking view on the map.""",
    },
    ('x8', 'bridge'): {
        'refs': ['phase2/x8/blockout_bridge.png', 'sky/check/14-xeen_cloud_sea-12.png'],
        'prompt': """
The scene: Cloudreach, a sky map of walkable cloud islands high above the world. Bright high sun, deep blue zenith,
a sea of white cumulus clouds below the islands stretching to the horizon (Reference 2: this world's sky over the
cloud sea).
- The player stands at the west end of a long rope bridge, on the eastern edge of the High Magic Clouds' largest
  island: a broad terrace of solid, walkable cloud-stone (pale grey-white, faintly golden in the sun, soft rounded
  edges like packed cloud). In the near foreground the bridge head: two tall timber posts with thick ropes, and on
  the right beside it a weathered stone statue on a plinth with a carved plaque (a rhyming statue).
- Centre: the long rope bridge of planks and thick ropes sags away across a wide gap of open sky to a small round
  cloud half way (where its two spans meet) and on to the Witch Clouds. Through a hole in the cloud sea under the
  bridge the green and blue land far below is visible: a lake, rivers, fields, tiny and hazy.
- Distance, across the frame: the Witch Clouds, a cluster of cloud islands on different levels joined by short rope
  bridges and cloud-stone ramps; left of centre a high cloud ringed with broken rock holding a huge ragged nest (the
  Harpy Queen's eyrie); right of centre three tall rock-and-cloud spires with big nests of sticks and bones on their
  tops; a stepped terrace with two stone offering statues at the bridge's far end; a few harpies circling.
- Left middle ground, lower: a small rock islet floating below the level of the terrace.
Mood: airy, bright, vertiginous and a little dangerous; the Fly spell does not work here, the bridge is the way.""",
    },
}


def cmd_paint(args):
    view = VIEWS[(args.key, args.view)]
    raw = HERE / args.key / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'{args.key}_{args.view}_v*.png')))
    target = raw / f'{args.key}_{args.view}_v{version}.png'
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
    print(args.key, args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    paint = sub.add_parser('paint')
    paint.add_argument('key')
    paint.add_argument('view')
    paint.add_argument('--note')
    paint.set_defaults(run=cmd_paint)
    args = parser.parse_args()
    args.run(args)


if __name__ == '__main__':
    main()
