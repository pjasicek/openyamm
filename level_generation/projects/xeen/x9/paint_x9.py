#!/usr/bin/env python3
"""X9's MU-4 eye-level concept: one `codex exec` image call (A5, 2026-11-20). After X7's paint_x7.py.

    paint_x9.py [--note TEXT]      mockups/raw/x9_signature_vN.png, the prompt beside it (.txt) and the log (.log)

Reference 1 is render_x9.py's blockout of the signature camera (composition), reference 2 X8's approved bridge
concept (how this world's walkable clouds and rope bridges read), reference 3 the xeen_cloud_sea sky at noon. Raw
returns are kept unchanged; one call, no retries.
"""
import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[4])  # the repository root
import argparse
import subprocess
import time
from pathlib import Path

HERE = pathlib.Path(_REPO_ROOT, 'output/studio_cal/x9') / 'mockups'
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

PROMPT = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for a sky map of a new world
for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees from one spot, at a person's eye
height, about 72-degree field of view, landscape format. Hand-painted, slightly stylised, the look of Might and Magic
VI-VIII maps re-imagined with richer painted detail: readable shapes, game-ready proportions (paths 3-4 m wide, doors,
booths and statues at human scale, not a photograph).
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where each cloud island, the castle, the booths and the rock spurs stand in the frame, and how large
they are. Its pale slabs are walkable cloud islands, the grey cones under them their hanging undersides, dark boxes
and cylinders the castle, red-and-cream boxes market booths, grey blocks rock spurs, small dark marks birds. The small
blue circles and blue words only say what stands there: paint the thing itself and never the circles, words or boxes.
Reference 2 is this world's approved concept of another sky map: paint the clouds, cloud-stone and rope bridges the
same way (solid walkable cloud tops, soft rounded edges, pale cloud-stone flags; Reference 3 is the sky over the cloud
sea). Do not copy its bridge, statue or nests.
No text, no labels, no letters, no signs with writing (sign boards are blank), no frame, no user interface, no
characters in the foreground, no people.

The scene: the Clouds of Xeen, walkable clouds high above the world, the villain's own sky. Bright high sun, deep
blue zenith fading to a pale horizon, a sea of white cumulus far below the islands stretching to the horizon.
- Foreground: the player stands on the north lip of a broad cloud (packed, walkable cloud with a few pale cloud-stone
  flags), where it thins to wisps over an open gap. Left of centre in the near foreground a weathered wooden signpost
  with a blank board.
- Centre, crossing the gap: straight ahead runs a barely visible way, a faint line of thin wisps hanging over the
  open sky toward a lower cloud nose some 50 m away (it should be hard to see: a hint, not a bridge). On that nose a
  small post and the start of a road of pale cloud-stone flags.
- Middle distance: beyond the nose a broad cloud plaza rises gently, paved with pale cloud-stone, with a carnival on
  its left half: four small fairground booths under red-and-white striped awnings (one with a tall high-striker pole
  and bell, one with a little race track, one with a treadmill, one with a straw bullseye target), bunting between
  poles; the stone road climbs along its right side.
- Centre distance, highest: Castle Xeen on its own cloud at the top of the road - black stone walls with gold friezes,
  four round corner towers with gold caps, a taller square keep behind, a double gate with gold leaves at the head of
  a broad causeway; grand, cold and menacing against the bright sky, clearly the destination.
- Right: a high cloud ringed with broken grey rock spurs holding huge ragged nests of whole branches, with great
  brown rocs (giant eagles) circling over it - the castle's aviary.
- Far right, higher still: a lone small cloud with a rock shaped like a dragon's head, out of reach.
- Left middle ground: small lone clouds stepping away northward, joined by sagging rope bridges, a stone statue on
  one of them; a few rocs far off.
Mood: bright, airy and vertiginous; a cheerful carnival at the gate of an evil lord's castle - the world winks, the
danger is real."""

REFS = [HERE / 'blockout_signature.png', ART / 'phase2/x8/raw/x8_bridge_v1.png',
        ART / 'sky/check/14-xeen_cloud_sea-12.png']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--note')
    args = parser.parse_args()
    raw = HERE / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob('x9_signature_v*.txt')))
    target = raw / f'x9_signature_v{version}.png'
    prompt = PROMPT
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(HERE), '--skip-git-repo-check']
    for ref in REFS:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print('signature', version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


if __name__ == '__main__':
    main()
