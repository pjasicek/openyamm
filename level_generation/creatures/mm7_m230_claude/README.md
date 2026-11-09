# MM7 Plate Fighter (m230): Initiate / Champion / Master of the Sword — Claude rig-first project

MM7 batch A, model 3 ([batch file](../mm7_batches/BATCH_A.md)). Same route and scripts as
[`mm7_m222_claude`](../mm7_m222_claude/README.md) / [`mm7_m226_claude`](../mm7_m226_claude/README.md), with its own
mesh, rig, weights, textures and longsword. **Installed 2026-10-20 (reduced exports).**

[Review viewer](review/viewer/index.html) · [viewer shots](review/shots/)

**Accepted, reduced and installed (2026-10-20):** installed 2026-10-20 from [`../mm7_batches/BATCH_A_stage/`](../mm7_batches/BATCH_A_stage/README.md). **Reduced (user: "reduce tris"):** the exports to install are now the ones in [`../mm7_m230_reduce_claude/`](../mm7_m230_reduce_claude/README.md) (body LOD0 8,898 -> 7,492, sword unchanged; same UVs, textures, tiers and clips; install commands there). This project's `export/` is their source and rollback.

## Deliverables

| File | What |
|---|---|
| `export/mm7_m230.glb` | runtime body: LODs 9,552 / 4,773 / 1,715 / 568 triangles (LOD0 incl. the 654-triangle longsword before the split), shadow LODs, 3 tier variants (`m230_a/b/c`), head (helm) material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget |
| `export/mm7_m230_sword.glb` | longsword attachment on node `Sword` (654 / 326 / 116 / 38 triangles) |
| `export/mm7_m230_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export and editable master |
| `textures/`, `integration/actors.yml` | texture sets, region mask, `m230_ramps.json`, class maps; staged binding |

Install later (user decision):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m230_claude/export/mm7_m230.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m230_claude/export/mm7_m230_sword.glb --world mm7
```

then append `integration/actors.yml` (`Fighter Plate A/B/C`, scale 104.8 = `m230sa0` 198 px × dsft 0.9 = 178.2 units
over 1.70 m, plume included in both; walk stride 1.71 m, run stride 1.8 m; impact 0.983 s; look 60°/35°; longsword on
`Sword`). Speeds 250/300/350: A walks (~1.4x the clip), B and C exceed the run threshold (2.4 × 104.8 = 251.5) and run.

## Model

- HD masters `references_hd/` (primary v2, four views, `longsword.png`); helm turnaround `references_head/`.
- Smart Topology 15k returned the plate armour as **separate segments with no skin under them** (thigh plates, helm,
  cuirass/tabard top, gauntlets with separate fingers, greaves, eagle crest, pauldrons and upper arms, belt, sabatons,
  tabard skirts, knee cops, vambraces and couters, gorget, buckle, nine plume strands). Cleanup: a 1-triangle part
  removed; a strand from the left upper-arm plate to the belt cut (outside the mirrored right plate's extent).
  Reduced after weighting to 8,898 triangles (gauntlets protected).
- Rig: source-frame rig; ring fits do not work on plate segments (line-fit elbows nonsense, wrists asymmetric), so
  **elbows and wrists come from Meshy's auto-rig** (`ELBOW_FROM=meshy WRIST_FROM=meshy`, symmetric, wrists at the
  gauntlet cuffs); ankles from rings; fingers by connectivity on the gauntlets.
- Weights (`weights_fix.py`): Meshy weights on the plates (no plate reaches 80 % on one bone; rigid plates would open
  holes at the joints, there is no skin under them) with the shoulder fade and no arm weight on the lower cuirass,
  **smoothed 8 passes inside each arm plate** (elbow tears: p99 2.48 → 2.09); helm, crest and plume rigid head;
  tabard skirts pelvis → thighs with the left/right mix per vertex (each panel spans both legs).
- **T visor painted** into the helm texture (`compose_m230.py`): the Smart Topology helm is a plain cylinder and the
  head retexture painted no visor; slit and gold edge from the master's proportions on the front-facing helm texels.
- Longsword (`make_sword.py`): outline and texture from `references_hd/longsword.png`, diamond double-edged blade with
  the wavy outline, gold guard and pommel, 1.3 cm grip (= the solved fist), 1.05 m; roll 90°.

## Clips

As m222/m226: Standing Standard Idle; Walking Mixamo Walk (1.71 m; constant 2.0 cm floor lift); Running Standard Run
+ run fit; Attack Sword And Shield Slash (2) planted + 20 % legs, 0.3 s lead, blow 0.983 s; Hit set Unarmed get-hit
F1; Death Falling Back Death (travel halved); Fidget Sword And Shield Power Up planted. Left fingers keep 50 % of the
source curl, the **left thumb stays at rest** (`THUMB_CURL=0`: its mis-fitted base tore the web 6.3x).
**`arm_clear.py`** (new, m230): the bulky thigh plates take hands the source swung past a slimmer body; the upper arm
swings outward by the least angle that clears the hand/forearm (walk L ≤ 7°, attack L ≤ 8°, death R ≤ 24°).

## Gates (2026-10-20)

- G4 arm stretch p99 ≤ 2.09, max 3.23 (attack, right elbow plate). G5 right ≤ 3.25x, left ≤ 2.67x.
- G6: walk and attack clean; Death right hand 2.9 cm into the body while lying (5 frames beyond the 24° swing limit).
- Soles: grounded within −1.7…+1.6 cm (walk −0.9…+0.9).
- Blade (double-edged): edge-leading share attack 0.66, walk 0.97, fidget 0.81, hit 0.98.
- Viewer: 24/24 tier/clip switches, no console errors. In game: not checked (nothing installed).

## Textures and tiers

`compose_m230.py`: body/head 1K sets (body retexture with Meshy UVs copied back, worst 0.01 mm; helm retexture on our
head UVs); AO graded; ORM per class; no skin. One recolour region **R = green textile and plume** (tabard green half,
leaf heraldry, plume): palette entries that differ between the tiers and are green in palette 54; ramps per tier
from the native pixels: A 54 green, B 55 blue, C 233 red. The white tabard half, steel, gold and stains stay.

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head (helm) retexture 10.

Feet (review 2026-10-20, "slightly angled on the boot edge"): the project's `foot_level.py` also levels the sole's roll
about the heel–toe line on grounded frames (the clips had rolled the boots onto their outer edges; the rest pose is
flat) and moves the pelvis by the change of the lowest sole point, so floor contact is unchanged; the run gets
`Running:rollonly`. Soles and gates re-measured after the rebuild (`review/gates_final.txt`). Walk and run take one constant roll per foot in the foot's own frame and one constant pelvis shift (review 2026-10-20: the per-frame roll switched on and off as the feet landed and lifted, a visible ankle twitch; foot rotation per frame is back to the source's). Hit, Attack, Fidget, Death and Standing: the roll is weighted by flatness (planted and level lengthwise), capped at 20 deg and smoothed over the clip (batch C's rule, mm7_m218_claude; peer report 2026-10-20: the groundedness-only roll snapped a stepping foot in Hit up to 22 deg and a lifting foot in Death up to 65 deg per frame); every clip's foot turn per frame is now within 2 deg of the source's. Walk bob (review 2026-10-20, "uneven head bob"): `walk_bob.py` after `clip_timing.py` smooths the walk's pelvis height over the loop (both steps alike, ankles kept reachable) and re-solves the legs to the same ankle paths and foot rotations; the retarget's floor rule had left a zigzag and up to 3.7 cm frame jumps.

## Replay

`TOKEN=<lease> STAGE=rig WRIST_FROM=meshy ELBOW_FROM=meshy scripts/rebuild.sh`, then `STAGE=anim DEATH_UNTIL=12
R_HANDLE=0.013 LEAD=0.3 LEFT_CURL=0.5 THUMB_CURL=0 scripts/rebuild.sh` (twice on a fresh project); `make_sword.py`
(python3, then Blender); texture chain; `compose_m230.py`; `scripts/build_runtime.sh`; `viewer_tiers.py`;
`update_viewer_manifest.py`.

## Known limits / for user review

- The plates bend slightly at the joints (smoothed Meshy weights) instead of articulating rigidly.
- Meshy painted a hammered stipple over the plates; the eagle crest is a soft blob; the plume is a solid ribbon.
- Death: the sword hand presses into the body while lying; the attack's overhead swing is fast (source).
