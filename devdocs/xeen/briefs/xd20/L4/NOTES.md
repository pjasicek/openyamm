# XD-20 The Warzone: L4 notes (lane A7, eleventh session, 2026-11-20)

Built from the approved MU-6 graph `devdocs/xeen/mockups/act4_graphs/xd20.graph.yml` and D-39 (XD-20 rows 1-5,
`mockups/act4_a7_decisions.md`) with A1's studio `arena` word (merge point 19, oymap 23:02:35). Hand-written L4 (an
arena of three rooms; no L1-L3 levels, no generator).

## What was built

| Room | Size | What |
| --- | --- | --- |
| Gate passage | 768 x 448, 448 high | The arrival `entrance:x6_yard` (256, 0) facing east; the arena gate's two leaves in the west wall (exits `exit:yard_l`/`yard_r`, MM7's `chb1dl`/`chb1dr` as X6's portal); two wall torches; X6's portal stone `chb1` |
| Hall of the War Games (lodge) | 1,536 square, 512 high | The lodge's door (one hinged leaf 192 x 384, `t5d1`); stone benches along north and south walls; four wall torches; the Arena Master's booth window in the east wall (`panel:booth_lodge`, `evt.SpeakNPC(4609)`) |
| The war floor | 16 sides, 3,584 across, sky at 1,536 | Sand (MM6 `6sandtyl`), the ring wall's 512 band `t5s1b` (7d05's friezes), `t5bs` above, the roof `sky: true` (atmosphere `open_sky` preset `clear`, X6's); the booth window on the north side at 96-352 (`panel:booth_floor`, clickable from the sand); four iron beast doors on the diagonals (dressing); the victors' gate west (two leaves, exits to X6); three heaps of bones (`dec29`, "Bones" / "There is nothing amongst the bones.") |

- **Arena** (objects.yml `arena`): monsters 11010-11699 (D-39 (1); A2's NoArena), party mark (4608, 0) facing
  north to the booth, a ring of 20 marks at radius 1,300 (about 410 apart: the graph's 2,400 floor grew to 3,584 so a
  Knight's or Lord's dragons have room). The build writes the scene's `arena` block and `runtime_restrictions` (no
  saving, no Lloyd's Beacon).
- 4 sectors (3 rooms), 106 faces, 1 door, 11 events; textures 9 (7d05's `t5bs`, `t5s1b`, `t5s1fl`, `t5s1c`, `t5d1`;
  MM6 `6sandtyl`; MM7 `chb1`, `chb1dl`, `chb1dr`), 0 new. Music 45. No chests, no monsters, no map qbits
  (118020-118029 unused), rest encounters 0.
- Way out: both the gate passage's leaves and the victors' gate to X6 `entrance:xd20_gate` (12288, -15872, 1504) facing
  west; measured: lands in the radius 150 at z 1,490-1,530.
- Original lines: xeen/aaze0085:5 and :6 (the bones), :7 "Exit the Warzone?" (the exit preset's meaning); aaze0085:0-4
  are Varro's (A4/A3). X6's "Enter the War Zone?" (aaze0006:4) is A5's.

## Checks

- `oymap validate` no issues; build 0 warnings; audit 0 errors, one info: the war floor is not reached on foot (the
  Arena Master's challenge moves the party there; by design, as MM7's arena).
- Playtests in `output/studio_cal/a7/root_s6` with a test row 9121 (A1's): `playtest.yml` (38 steps: arrival, saving
  refused, the door, Varro at the lodge's booth, a Page fight of 6-8 hostiles with the party on its mark, all killed,
  the floor's booth pays 1,000 and award 46, out by the victors' gate to X6), `playtest_exit.yml` (14, by the gate
  passage), `playtest_hostility.yml` (15: a Knight fight's 10-20 opponents all hostile, none target another, they go
  for the party). Four of four each: `output/studio_cal/xd20/a7_xrun/`, `output/studio_cal/a7/s11_xd20_three.out`.
- Installed with its bake (profile `tools/lighting/baked_indoors/profiles/xeen_xd20.yml`), `stale_bakes.py` 0.
- Pictures `output/studio_cal/xd20/sheet.jpg` (first version: the 7d05 `tfb2` floor read as tiles, replaced) and
  `sheet2.jpg` (the sand floor). A tour needs a scene with saving allowed (the run wrapper saves first): the tour
  edited the root's scene for the run and put it back.

## Waits

- **A2:** the map row 9121 (`source/map_rows.yml` maps XD-20: encounter 0, no slots, STONEROOM, music 45; `include:
  built` writes it now the map is installed). Until then the playtests run only from the scratch root.
- **A5:** X6's `door:xd20` (thing:arena_gate) is still sealed with its line: open it to `entrance:x6_yard`; then the
  playtests from `assets_dev`.

## Dressing exceptions

- The bones heaps stand in the sand about 150 from the ring wall (set dressing, not containers).

## Exit facings (2026-11-21, lane A7, thirteenth session; A5's report)

Three of the four ways out (`evt:victors_r`, `evt:yard_l`, `evt:yard_r`) arrived on X6 facing east (0): the studio gave
the neighbour's arrival facing only to the first exit that names it. `direction: 180` on the neighbour `exit:x6_yard`
now gives all four 1024 (west). Rebuilt in `output/studio_cal/a7/root_s6`, installed with bake 00:34, 12/12 from
`assets_dev` (`output/studio_cal/a7/s13_xd20_four.out`).
