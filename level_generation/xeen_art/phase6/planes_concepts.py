#!/usr/bin/env python3
"""The planes' MU-4 eye-level concepts: one `codex exec` image call per picture (A6's planes sub-agent, 2026-11-21).

    planes_concepts.py p1|p2|... [--note TEXT]   -> planes/raw/<key>_arrival_vN.png, its prompt (.txt) and log (.log)

Reference 1 is planes_render.py's blockout of the arrival camera (composition; blue marks name what stands there); the
others give the look (this world's approved concepts and the element's shipped textures). Raw returns are kept
unchanged; one call per image, no retries unless an image is unusable.
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ART = HERE.parent
ROOT = ART.parents[1]
OUT = HERE / 'planes'
sys.dont_write_bytecode = True
sys.path.insert(0, str(ART / 'phase2'))
from concepts import WORKER  # noqa: E402  (the shared one-image worker brief)

COMMON = """Asset: an eye-level concept painting (a "MU-4" mood and silhouette concept) for one of the four elemental
planes of a new world for a Might and Magic VI-VIII style first-person RPG. It shows what the player sees the moment
they arrive, from a person's eye height, about 74-degree field of view, landscape format. Hand-painted, slightly
stylised, the look of Might and Magic VI-VIII maps re-imagined with richer painted detail: readable shapes,
game-ready proportions (paths 3-4 m wide, a statue twice a man's height, standing stones, a dais and a couch at human
scale, not a photograph). The map is small and compact: everything important is in view, nothing is miles away.
Reference 1 is a crude blockout render made from the map plan at this camera: keep its composition exactly - the
horizon height, where each shelf, island, path, ring, statue and tower stands in the frame, and how large it is. The
small blue circles and blue words only say what stands there: paint the thing itself and never the circles, words or
boxes.
No text, no labels, no letters, no numbers, no frame, no user interface, no people and no monsters."""

VIEWS = {
    'p1': dict(refs=[OUT / 'p1/blockout_p1.png', ART / 'phase5/d6/raw/d6_signature_v1.png',
                     ROOT / 'level_generation/textures_x4/masters/mm6/orfyrlga.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gcav2flr.png'],
               prompt="""
The scene: the Plane of Fire, a lake of lava in a crater of black volcanic glass. There is no sun and no sky colour
but fire: the sky is a ceiling of churning red-black smoke lit orange from below (MM8's Plane of Fire), embers
drifting. Reference 2 is this world's concept of another lava map: paint lava, crust and basalt the same way (do not
copy its castle, pods or desert). Reference 3 is the molten lava texture, Reference 4 the black lava rock of the paths.
- Foreground: the player stands on a low shelf of cooled black crust, cracked, with faint orange glow in the cracks.
- From the shelf a causeway of black crust, 3-4 m wide with low ragged banks, runs left across the lava to a round
  crust shelf where a tall statue of a figure made of flame, carved in red stone, stands on a black plinth (left
  middle distance).
- Middle: a lake of bright churning lava, crusted plates floating on it, heat shimmer, small spurts of fire.
- Centre, far across the lava against the crater wall: the tallest spire of the wall, black glass, with a hall
  open to the sky cut into its foot (a ring of slim black columns, a pale red light inside: the sleeper's hall).
- Right of centre, on a basalt rise across the lava: the Crucible, a wide low ring of black obsidian pillars and
  walls, a red glow welling from its middle.
- Far right, nearer: a shelf of tall hexagonal basalt columns and spires.
- All round, the crater wall: black glassy cliffs, a lava fall pouring down it far left.
Mood: hot, red, dangerous and grand; a place that tests you."""),
    'p2': dict(refs=[OUT / 'p2/blockout_p2.png', ROOT / 'output/studio_cal/x9/mockups/raw/x9_signature_v1.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gwsphlfl.png'],
               prompt="""
The scene: the Plane of Air, islands of wind-carved white stone hanging in an endless bright sky with no ground under
them: the sky continues below the horizon, pale blue fading to white haze far below, a few cumulus clouds floating
beneath the islands as well as above. Reference 2 is this world's approved concept of a sky map: paint the sky, the
light and the cloud-stone the same way (do not copy its castle, carnival, statues or birds; there is no sea of clouds
here, only open sky). Reference 3 is the pale wind-carved stone of the islands.
- Foreground: the player stands on a flat island of white wind-scoured stone, at its edge.
- From the island's right a bridge of pale cloud-stone slabs, 3-4 m wide, crosses an open gap towards a round island
  in the centre-right where a tall statue of a winged figure in white stone, robes streaming, stands on a plinth.
- Left middle: an island crowned by a ring of hollow, pierced standing stones (the singing stones), wind-worn.
- Centre, beyond: the highest island carrying a pale open dome on slim columns (the sleeper's aerie).
- Right: a broad round island ringed by tall standing stones, dust and leaves circling in the calm middle.
- Every island has a rough rocky underside tapering downward like an upturned cone, with wisps of cloud.
Mood: bright, cold, airy and vertiginous; wind you can almost see."""),
    'p3': dict(refs=[OUT / 'p3/blockout_p3.png', ROOT / 'level_generation/xeen_art/sky/check/02-xeen_darkside_day-12.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gwspotwl.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gwsphlfl.png'],
               prompt="""
The scene: the Plane of Earth, a vast bowl of raw stone whose walls lean inward like a cavern's, open above to a
sky of thick brown dust with no sun and no stars: dim, warm, brownish light falls from the dust ceiling, motes of
dust hang in the air, a few pale crystals glint in the walls. Reference 2 shows this world's painting style for a
dim amber sky (use only its manner of light; the sky here is a low ceiling of brown dust, not clouds). Reference 3 is
the blue-grey rough rock of the bowl's walls, Reference 4 the pale carved stone of the terraces.
- Foreground: the player stands on a ledge of packed earth high on the bowl's wall; a broad stone ramp leads down
  and away to the right.
- Left middle: a broad terrace of flat stone where a squat giant statue of rough-hewn granite sits with its hands on
  its knees, on a plinth.
- Centre, lower: a terrace of tall stone pillars like petrified trees.
- Right, lower still, at the bottom of the bowl: a round floor of bare bedrock cracked at its middle, ringed by tall
  rough monoliths (the Anvil).
- Far right, deepest: a dark hollow under an overhang of the bowl's wall, roots of stone hanging from it, a faint
  amber glow inside (the sleeper's hollow).
- Between the terraces: drops of several metres to a floor of loose scree and boulders.
- All round: the bowl's huge leaning walls of layered stone, a quarry's cut steps far left.
Mood: heavy, ancient, silent and enclosed; the weight of the earth."""),
    'p4': dict(refs=[OUT / 'p4/blockout_p4.png', ROOT / 'output/studio_cal/x9/mockups/raw/x9_signature_v1.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gtempw1.png',
                     ROOT / 'level_generation/textures_x4/masters/mm8/gtempflr.png'],
               prompt="""
The scene: the Plane of Water, a great temple drowned in a calm green sea with no shore. The sky is the colour of
the sea: a sea-green zenith fading to pale aquamarine at the horizon, no sun disc, bright soft light from above,
slow wavering cloud like light on water; the sea runs to a misty horizon with tall sea stacks and broken arches
standing in it. Reference 2 is this world's approved concept of a sky map: paint the light and the stone the same
way (do not copy its castle, carnival, clouds or birds). References 3 and 4 are the pale marble walls and the
blue-grey flagstones of the drowned temple.
- Foreground: the player stands on a terrace of green-veined marble with spray on its edge; a colonnade walk 3-4 m
  wide, the top of a drowned wall, runs straight ahead over the water, low steps down to the sea on both sides.
- Centre: the temple's drowned forecourt rising from the water, a statue of a woman of green stone pouring water
  from a jar into a fountain basin at her feet.
- Behind it, slightly left: a dark grotto under a great sea arch (the sleeper's grotto), a faint blue glow inside.
- Right: a round court ringed by broken marble columns of different heights, the water turning in a pool at its
  middle (the whirlpool court).
- Left: a terrace grown over with coral and shells; far left, the masts of a sailing ship wrecked across a court.
- The water: clear green, gentle swell, foam where it laps the stone.
Mood: cool, luminous, restless and strange; a sea with no coast."""),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('key', choices=sorted(VIEWS))
    parser.add_argument('--note')
    args = parser.parse_args()
    view = VIEWS[args.key]
    raw = OUT / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    version = 1 + len(list(raw.glob(f'{args.key}_arrival_v*.txt')))
    target = raw / f'{args.key}_arrival_v{version}.png'
    prompt = COMMON + '\n' + view['prompt'].strip()
    if args.note:
        prompt += '\nCorrection for this attempt: ' + args.note
    target.with_suffix('.txt').write_text(prompt + '\n')
    command = ['codex', 'exec', '--json', '-s', 'workspace-write', '-C', str(raw), '--skip-git-repo-check']
    for ref in view['refs']:
        command += ['-i', str(ref)]
    started = time.time()
    with open(target.with_suffix('.log'), 'w') as stream:
        result = subprocess.run(command, input=WORKER.format(prompt=prompt, target=target), text=True,
                                stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
    print(args.key, version, 'ok' if result.returncode == 0 and target.exists() else 'FAILED',
          round(time.time() - started), 's')


if __name__ == '__main__':
    main()
