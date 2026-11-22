#!/usr/bin/env python3
"""X7's MU-4 eye-level concepts: one `codex exec` image call per picture (A5, 2026-11-20).

    paint_x7.py VIEW [--note TEXT]      mockups/raw/x7_<view>_vN.png, the prompt beside it (.txt) and the log (.log)

The route is X6's (paint_x6.py): reference 1 is render_x7.py's blockout of the sketch's camera (composition), the
others give the look (MM7's red mountain ground, the shipped fair sky, X6's approved world-rim concept for how the
rim and the stars below it read). Raw returns are kept unchanged; one call per view, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x7') / 'mockups'
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
(roads 3-4 m wide, doors and people at human scale, rocks and scrub spaced as in a game map, not a photograph).
The world is flat: a square continent floating in space, so where the land ends there is a sheer cliff ("the world
rim") and below it a black starfield, visible even by day. This map is the world's volcanic corner: a day under a
dull, ash-hazed sky, greyish-brown above and ruddy toward the horizon, the sun a pale disc behind the haze; fine grey
volcanic ash drifting down through the air (light, sparse flakes, not a storm); MM7 brightness, not gloomy.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where the mountain, the range, the buildings, the cave mouths and the lava stand in the frame, and how
large they are. Its coloured boxes are buildings, walls, crags and statues, dark cones are tower roofs, the grey
wedge is the volcano's smoke plume, orange is lava, ovals on sticks are scrub. The small blue circles and blue words
only say what stands there: paint the thing itself and never the circles, words or boxes.
No text, no labels, no letters, no signs with writing, no frame, no user interface, no characters in the
foreground, no dragons or monsters in view, no modern objects."""

VIEWS = {
    'arrival': {
        'refs': [HERE / 'blockout_arrival.png', ART / 'mu2_materials/views/mm7_out10/04-ne-high.png',
                 ART / 'sky/check/11-fair-12.png'],
        'prompt': """
The scene: Mount Firestone's south slopes, the arrival from the south. Midday under the ash haze (Reference 3's
sky, dulled and browned by ash). The player has just come up a pebbled road from green hills behind and looks north
up a long, gently rising slope of red-brown stony earth, dry yellow grass tufts and low thorn scrub (Reference 2's
red mountain ground).
- The pebbled road runs straight away from the viewer up the slope toward a pass.
- Left of centre, beside the road some way up the slope: a small abandoned dwarf watch post - a square stockade of grey
  fieldstone and dark timber with a squat stone signal tower at its corner, a cold iron brazier on top.
- Right of centre, a little nearer: a red rock crag with a dark cave mouth at its foot (a hermit's cave), a little smoke
  from a cooking fire, a faint glint of gold inside.
- Across the whole middle distance: a range of bare red peaks (the Red Dwarf Range), not very high, with a clear
  saddle-shaped pass where the road disappears.
- Above and beyond the range, right of centre, far away: the black cone of a great volcano, a tall grey plume of
  smoke and ash leaning east from its crater, a faint red glow at the summit; it is clearly the highest thing in view
  and much farther than the range.
- Far left on the horizon, small and hazy: a thin black stone tower on a crag.
Mood: dry wind, a warm dull light, ash drifting; the mild near side of a dangerous mountain.""",
    },
    'signature': {
        'refs': [HERE / 'blockout_signature.png', ROOT / 'output/studio_cal/x6/mockups/raw/x6_signature_v1.png',
                 ART / 'mu2_materials/views/mm7_out10/04-ne-high.png'],
        'prompt': """
The scene: the lava falls at the edge of the world, below Mount Firestone. Late afternoon under the ash haze, the
light dull red-brown. The player stands on the lip of a cove where the world's edge bites into the land, and looks
south-east across the cove.
- Centre-left: across the cove, a lava river runs to the cove's far cliff wall and pours over it in a broad glowing
  orange-red fall, crusting black at its edges, dropping down the sheer black basalt cliff and on into empty space;
  streams of glowing droplets and sparks trail off into the void and cool to red embers.
- Below the cove's lip and in the lower left of the frame: the cliff walls of black basalt drop away, and beneath and
  beyond them is a black starfield (the space under the floating world, as in Reference 2's rim, which shows how the
  world's edge and the stars below it read - do not copy its desert or its sphinx).
- Right half: the land beyond the cove rises into the great black cone of Mount Firestone, its crater smoking, a tall
  grey plume of ash leaning east; the lava river comes down its flank as a winding orange ribbon through grey ash
  fields and black cooled flows (Reference 3's rock forms, in black and grey).
- Far left on the rim: a small rocky spit with a tiny pale machine on it.
- Foreground: the cove's lip of grey ash and black crusted rock, a few cracks with a dull red glow.
Mood: awe and heat at the end of the world; the lava falling forever into the stars.""",
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
    version = 1 + len(list(raw.glob(f'x7_{args.view}_v*.txt')))
    target = raw / f'x7_{args.view}_v{version}.png'
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
