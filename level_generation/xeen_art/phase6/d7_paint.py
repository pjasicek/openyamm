#!/usr/bin/env python3
"""D7's two MU-4 eye-level concepts: one `codex exec` image call each (A6 sub-agent, 2026-11-21; after X9's
paint_x9.py).

    d7_paint.py arrival|signature [--note TEXT]     d7/raw/d7_<view>_vN.png, the prompt (.txt) and the log (.log)

Reference 1 is d7_render.py's blockout of the camera (composition), reference 2 X9's approved concept (how this
world's walkable clouds and cloud-stone read), reference 3 the Darkside's amber day sky (xeen_darkside_day at noon),
which the Skyroads' preset inherits. Raw returns are kept unchanged; one call per image, no retries.
"""
import argparse
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent / 'd7'
ROOT = Path(__file__).resolve().parents[3]
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

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for a sky map of a new world
for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a person's eye
height, about 72-degree field of view, landscape format. Hand-painted, slightly stylised, the look of Might and Magic
VI-VIII maps re-imagined with richer painted detail: readable shapes, game-ready proportions (roads 4-6 m wide, doors,
stalls and statues at human scale, not a photograph).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where each cloud island, road, building and creature stands in the frame, and how large it is. Its
pale slabs are walkable cloud islands and cloud roads, the grey cones under them their hanging undersides, pale boxes
buildings, gold shapes gold domes and capstones, small dark marks flying creatures, dark grey boxes stone golems. The
small blue circles and blue words only say what stands there: paint the thing itself and never the circles or words.
Reference 2 is this world's approved concept of another sky map: paint the clouds and cloud-stone the same way (solid
walkable cloud tops, soft rounded edges, pale stone flags) but NOT its blue sky, castle, booths or banners.
Reference 3 is this map's sky, the Darkside of Xeen by day: a low amber-gold haze at the horizon, a muted warm
zenith, a small pale sun; paint the whole sky in that light, and below the horizon (the islands float in open sky)
the same amber haze over a far sea of soft clouds. The clouds of the islands take the warm amber light.
No text, no labels, no letters, no signs with writing (sign boards are blank), no frame, no user interface, no
characters in the foreground, no people.
"""

SCENES = {
    'arrival': """The scene: the Skyroads, the roads of the gods over the Darkside. The player has just climbed a rope up
out of the sky below onto a broad cloud on the edge of the map, and looks east along a road into the sky.
- Foreground left: a weathered wooden signboard on a post, its board blank, at the start of the road.
- The road: a causeway of packed white cloud with a band of pale cloud-stone flags down its middle, about 5 m wide,
  running straight ahead and slightly upward over open sky to a cloud island in the middle distance. Nothing holds it
  up: it floats.
- On that island: an old white marble jetty sticking out into the sky with no boat at it (a launch the gods no longer
  use), and two or three heavy grey stone golems standing guard on the cloud.
- Far left, higher than everything: Olympus, a small city of white marble on its own raised cloud - a gold dome, pale
  roofs, gilded gateposts - glinting in the amber light, clearly the goal.
- Centre distance: a golden pyramid capstone floating a little above its own cloud, with three pale winged dragons
  circling it.
- Right: more cloud islands and thin cloud roads receding, one wide bowl-shaped cloud holding a little lake that
  catches the light, rope bridges between small clouds.
Mood: high, warm, quiet wonder; a highway in the sky with deadpan roadside signs - the danger (golems, dragons) is
real.""",
    'signature': """The scene: Olympus, the city of the gods, seen across the cloud roads of the Skyroads under the
Darkside's amber sky.
- Foreground: a broad causeway of white marble flags laid on a tongue of cloud, running straight ahead and gently up
  toward the city's east gate, open sky on both sides of it.
- Middle distance, centre and filling about half the width: Olympus on a raised cloud paved in white marble, a low
  marble balustrade along its rim; compact and grand: a dozen white marble houses and halls with pale grey roofs and
  gold bands, colonnades, a temple with a gold dome and a portico of six columns rising above the rest; the east gate
  is a pair of tall gilded gateposts at the causeway's head (no wall, no door).
- Left of the city, nearer: a slender marble jetty sticking out from the cloud over the void, a small golden sky-boat
  with a curved prow moored at its end.
- Right: a second causeway leaving the city northward to a long cloud road that runs off along the far right.
- Left, far: a thin cloud road leaving the city south-west over the void toward small distant clouds, one with a rope
  hanging out of the sky.
- The city's cloud has a soft rounded underside hanging over open sky; far below, the amber haze over a sea of clouds.
Mood: serene, golden, a little smug; the gods live up here, and the people below are so small they look like ants.""",
}

REFS = {
    'arrival': [HERE / 'blockout_arrival.png', ROOT / 'output/studio_cal/x9/mockups/raw/x9_signature_v1.png',
                ART / 'sky/check/02-xeen_darkside_day-12.png'],
    'signature': [HERE / 'blockout_signature.png', ROOT / 'output/studio_cal/x9/mockups/raw/x9_signature_v1.png',
                  ART / 'sky/check/02-xeen_darkside_day-12.png'],
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('view', choices=sorted(SCENES))
    parser.add_argument('--note')
    args = parser.parse_args()
    raw = HERE / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'd7_{args.view}_v*.txt')))
    target = raw / f'd7_{args.view}_v{version}.png'
    prompt = COMMON + '\n' + SCENES[args.view]
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in REFS[args.view]:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print(args.view, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


if __name__ == '__main__':
    main()
