#!/usr/bin/env python3
"""P5's two MU-4 eye-level concepts: one `codex exec` image call per view (A5 sub-agent, 2026-11-21). After X9's
paint_x9.py.

    paint_p5.py walk|shrine [--note TEXT]   mockups/raw/p5_<view>_vN.png, the prompt beside it (.txt), the log (.log)

Reference 1 is render_p5.py's blockout of the view's camera (composition), reference 2 X9's approved concept (D-50:
how this world's walkable clouds and cloud-stone read), reference 3 the xeen_cloud_sea sky at noon; the shrine view
adds reference 4, the three portraits (the Dragon Pharaoh, Prince Roland, Queen Kalindra; A4's npc15453, npc14405,
npc15001). Raw returns are kept unchanged; one call per view, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'mockups'
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

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for the finale map of a new
world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a person's
eye height, about 72-degree field of view, landscape format. Hand-painted, slightly stylised, the look of Might and
Magic VI-VIII maps re-imagined with richer painted detail: readable shapes, game-ready proportions (a road 4 m wide,
huts, boards, a dais and figures at human scale, not a photograph).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where each cloud, building, board and figure stands in the frame, and how large it is. Its pale slabs
are walkable cloud, the grey cones under them their hanging undersides, small beige dashes flagstones, cream
rectangles on brown legs blank billboards, brown boxes wooden huts, coloured blocks figures. The small blue circles and
blue words only say what stands there: paint the thing itself and never the circles, words or boxes.
Reference 2 is this world's approved concept of another sky map: paint the clouds and the pale cloud-stone the same way
(solid walkable cloud tops with soft rounded edges, pale cloud-stone flags; Reference 3 is the sky over the cloud sea:
bright high sun, deep blue zenith fading to a pale horizon, a sea of white cumulus far below). Do not copy its castle,
carnival, statues or birds.
No text, no labels, no letters, no numbers, no writing anywhere: every sign and billboard face is blank (plain painted
colour in a frame). No frame, no user interface."""

VIEWS = {
    'walk': dict(refs=['blockout_walk.png'], prompt="""
The scene: the Clouds of the Ancients, the last place in the world, a ring of cloud road high in a bright, calm sky.
The player has just stepped out onto the road; it is a long walk round to the shrine.
- Foreground and right: a broad road of packed white walkable cloud, 4 m wide, running straight ahead into the
  distance and turning left far away; down its middle a dashed line of pale cloud-stone flagstones, exactly like a
  highway's centre line (a gentle joke: a highway in the sky).
- Right, along the road's outer edge: two or three roadside billboards on little lobes of cloud - tall wooden boards on
  two legs facing the road, each a different bright colour in a painted frame, all blank. Beyond them a small wooden
  roadside rest stop: an open-fronted hut with a shingle roof, a plain bench inside, and a blank green sign board on a
  post above its front, like a highway rest stop.
- Centre distance: where the road turns, a round tower of pale stone with a copper dome and a closed observing slit -
  an observatory - standing beside the road on its own widening of cloud.
- Left, across an open gap of sky and a little higher than the road: a round cloud paved in pale gold stone, seen
  from below and to the side; on it two great stone hands rise from a low dais, open palms up, as if offering
  something to the sky - the Pharaoh's shrine, the goal, clearly visible across the gap.
- Far left: the road's ring continues on the far side of the shrine, small boards along it.
Mood: serene, wide and quiet, the end of a long journey; no monsters, no people. The world winks (rest stops and
billboards in the sky) but the light is clear and solemn."""),
    'shrine': dict(refs=['blockout_shrine.png', 'portraits'], prompt="""
Reference 4 shows the three characters' portraits (left to right): the Dragon Pharaoh (a golden dragon wearing a blue
and gold striped royal headdress), Prince Roland (dark hair, gold circlet, silver armour with blue), Queen Kalindra
(long dark hair, silver crown, purple gown). Paint them as small full-figure people in the middle distance, matching
these looks; not portraits, no close-up faces.
The scene: the Clouds of the Ancients, the end of the road, just after the ceremony that made the world whole.
- Foreground: the top of a pale cloud-stone causeway arriving on a round cloud paved in pale gold stone.
- Centre: a low wide dais of pale gold stone; from its two front corners rise two great stone hands, open palms up,
  each taller than a man. In the left hand floats a glowing blue cube of light (the Cube of Power); the right hand
  holds an ornate golden sceptre upright (the Scepter).
- Just behind the dais, between the hands: the Dragon Pharaoh, standing upright like a man, a golden dragon in a blue
  and gold striped headdress and a white and gold robe, holding an open book, reading the vows.
- Behind him: a wedding pavilion - a white canvas canopy with gold trim and gold tassels on four slim gold posts,
  garlands of white flowers, open to the front. Under it Prince Roland and Queen Kalindra stand side by side, facing
  the viewer, newly married. A small round table with a tall white cake inside the pavilion.
- Background, centre: far beyond the pavilion, across the sky, a round pale-stone observatory with a copper dome on
  its own cloud; to the left and right, low in the distance, the ring of cloud road with small blank billboards.
Mood: warm, joyful and a little funny (a dragon officiating a royal wedding on a cloud), warm light, the
happy ending of a long adventure, under the same bright high sun."""),
}

REFS_COMMON = [ROOT / 'output/studio_cal/x9/mockups/raw/x9_signature_v1.png',
               ART / 'sky/check/14-xeen_cloud_sea-12.png']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('view', choices=sorted(VIEWS))
    parser.add_argument('--note')
    args = parser.parse_args()
    view = VIEWS[args.view]
    raw = HERE / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'p5_{args.view}_v*.txt')))
    target = raw / f'p5_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    refs = [HERE / view['refs'][0]] + REFS_COMMON
    if 'portraits' in view['refs']:
        refs.append(pathlib.Path(_REPO_ROOT, 'output/studio_cal/p5') / 'src/portraits.png')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in refs:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print(args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


if __name__ == '__main__':
    main()
