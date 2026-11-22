# X3 Lifeforce Lagoon: L1 notes (MU-3 and MU-4, gate G1)

Lane A5, 2026-11-20. A plan only: there is no geometry. Nothing gets built until the user has seen the board.

## What the plan holds

- **The lagoon** (water at 860, about 900 cells) sits in the middle of the map. The **Tower of High Magic** (XD-11)
  stands on a rock islet in it. A stone causeway joins the islet to the north shore. The Lagoon Water drains west
  through the Black Fen to X5.
- **East, by the X2 road:** Ebenezer's camp (1,020) holds tent 4101 (tavern) and shrine 4102 (temple), open from day
  one. Above the camp, Newcastle's ruin sits on its rise (1,750). It has the XD-13 stair, the mirror 4121 at the gate
  and Emerson's work yard. The Crow Hills rise behind it to the Crow's Crown (3,450).
- **Nightshadow** stands on the lagoon's east shore, in a misty hollow under the east ridge. It has 16 buildings
  (A4's 4103-4120), and the square holds the 3 sundials, the sign and mirror 4110. The XD-24 crypt is in the
  churchyard. Mirabeth (4202) stands on a black-rock spit off the quay.
- **West and south:**
  - the Bogwood (rangers' camp), north-west;
  - the Black Fen (the road to X5), west;
  - the Gloomwood with the Tomb of a Thousand Terrors (XD-08), south-west;
  - the Drowned Shore (Lifeforce Spring, the wreck, night bats), south, ending at the world rim cliff at y 104.
- **Q-C7 on the square:**
  - **The sundials:** three on the dial walk. While all three read 9 the map sets q-c7.dials_set (112142), and clears
    it when one is turned off 9. Plinths 1 and 2 carry q-c7.clue_stitch and q-c7.clue_cat.
  - **The signs:** q-c7.sign_nine at the dial walk's entrance and q-c7.rhyme on a signboard by the coffin.
  - **The coffin:** Count Draco's coffin (q-c7.coffin with q-c7.sign_night on its plinth) is now XD-24's entrance,
    no longer a mausoleum in the churchyard.
  - **The town well:** q-c7.well.
- **Quest hooks:** m8.site (Ebenezer's camp and the ruin), m9.walls and m11.keep (Newcastle's stage groups),
  m10.tomb_door, m13.tower_door, q-c12.lagoon_rock and Q-C7 (sundials, sign, crypt). Each is named in a plan goal or
  POI.

## Figures (plan against MAPS)

| figure | target | plan |
|---|---|---|
| hostiles at load | 135 | 135: 46 markers (Swamp Thing 2-3, Toad 2-4, Zombie 2-3) + 15 placed (rangers 7, bats 8) |
| kill XP per member | 14.0k | about 14.1k (tier mix A/B/C 50/35/15 assumed; A2 settles) |
| encounter areas | 3-8 of 6-30 blocks | 5: Bogwood 18, Black Fen 14, Gloomwood 15, Drowned Shore 14, Crow Hills 11 |
| quiet land | at least a third | 51 % of land cells, 39 % of blocks |
| first fight | 2,000-6,000 | east 5,120, west 4,857, north 5,271 |
| POIs | 25-30 | **31**, one over: A3's Q-C7 rhyme board and town well added 2 (census with service doors 36, nearest-neighbour median 1,846) |
| chests | 4-10 with a reason | 9 |
| dungeon entrances | 3-6 | 4 |
| roads | 1-4 % of land | 3.2 % |
| height range | at least 2,500 | 860-3,450 |
| empty land | no 6,000 stretch | farthest land 5,937 from a place or fight |
| Nightshadow | compact | 16 buildings on 191 cells of footprint (8.3 per 100), 5,900 x 9,500, square 2,560 |

The figures come from `output/studio_cal/x3/tools/x3lib.py`, using indicative marker spots. The studio places the
real markers.

Two figures are outside a reference:
- **Camp and gate.** The nearest monsters are about 8,200 from the camp's doors and from the Newcastle gate (X1's town
  measured 4,500-6,800). This is meant as a safe base.
- **X8 falls.** A fall from X8 lands round the Tower, and the nearest group to the causeway head is about 9,700 away.

## Choices made

- **Edges:**
  - East to X2: the road at **y 40**, on X2's west road line.
  - West to X5: the road at **y 59** and the river at **y 62**.
  - North to X4: the road at **x 50**. X4's lane aligns its south road to it.
  - The heights at all three edges match the neighbours' frames.
- **Kits:**
  - Nightshadow: `cloudside_town` in its darkest grades, with the temple and manor in chb1 fieldstone.
  - Newcastle: `royal_castle`'s staged ruin pieces (ch1b1) at stages 0-1.
  - The Tower: `towers` (hwm2 base, hwp1 storeys).
- **Signature view:** the causeway head, looking south-east at the Tower, Mirabeth's rock and Nightshadow in mist.
- **Moved from the source (C4/D4):** Newcastle and the camp go east beside the X2 road. The Tower goes into the lagoon,
  as M12's text says.

## Original lines

- The sign: "The Count wakes at nine and sleeps at nine."
- The sundial plinths: "Only at night can you put up a fight." and "If the Dials are properly set, The count will
  definitely be upset."
- Count Du Monay's fee is in A4's house 4105.

## Open questions for the user

1. Keep the signature view, or use Nightshadow's square instead?
2. Is it fine that Newcastle and the camp moved east by the X2 road?
3. Is it fine that the Tower stands on an islet with a causeway?
4. Should the mist lift once q-c7 is done?
5. Should the camp and gate stay a safe base?
6. Is +2 Endurance right for the Lifeforce Spring?

## Files

- Brief: `devdocs/xeen/briefs/x3/L1/{project,plan,sketch}.yml`. It is written by
  `output/studio_cal/x3/tools/gen_l1.py`; edit the script, not the YAML.
- Run everything with `output/studio_cal/x3/run_l1.sh`: generate, `oymap fmt`, `oymap validate` (no issues), draw.
- Drawings in `output/studio_cal/x3/mockups/`:
  - `plan_x3.svg` and `plan_x3.png`
  - `blockout_arrival.png` and `blockout_signature.png`
  - `concept_arrival.png` and `concept_signature.png`
  - `board_x3.png`
  - `figures.json`
- Codex raw returns: `mockups/raw/` (each image with its prompt and log; one call per image, none retried).
- Tools: `render.py` (it imports A6's `plan_render.blockout`), `paint.py` and `board.py`.
