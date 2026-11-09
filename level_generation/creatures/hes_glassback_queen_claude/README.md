# The Glassback Queen (Hesper boss 10101, D2 Filter Beds): Claude project

Round 3, Claude B of `design/kreegan_world/WORK_PACKAGES/CREATURE_BUILDS.md` (2026-10-23). The design: MONSTERS.md
row 10101 ("Crystal Walker C, x1.6, crystal spines grown into a crown"; immune to Energy and Light) and
`design/kreegan_world/zone1/dungeons/D2_PUMPING_STATION.md` (the Filter Beds, glass growths glowing faint blue).
**Staged** on the Hesper stage (`hesper_stage/monsters.yml` row 10101, `integration/actors.yml`); D2 has not placed
its monsters yet. Not installed in `assets_dev`. No Meshy credits. The Glassback projects
(`hes_glassback_claude/`, `hes_glassback_reduce_claude/`) are read and copied from, never modified.

[Concept](../../../design/kreegan_world/concepts/monsters/boss_glassback_queen.png) ·
[viewer shots](review/viewer_shots.png) · [crown build views](review/crown_v2_sheet.png) ·
[crown clearance](review/crown_clearance.json) · [in game, D1 smoke run](../hes_custodian_claude/review/ingame/d01_smoke_sheet.jpg) ·
viewer `http://127.0.0.1:8912/level_generation/creatures/hes_glassback_queen_claude/review/viewer/`

## Concept

`design/kreegan_world/concepts/monsters/CODEX_BRIEF_GLASSBACK_QUEEN.md`. First pair (candidates 1 halo, 2 swept):
the user asked for a redo (in both the "crown" read as a bigger crest running up behind the head, and the mineral
crust barely showed). Redo pair 3/4 (the brief's last section: a coronet on the skull, a bare-neck gap before the
crest, pale crust); the user picked **candidate 3** (`boss_glassback_queen.png`), straight upright crystals.
Records: `generation_runs_glassback_queen.json`.

## What she is made of

| File | What |
|---|---|
| `export/hes_glassback_queen.glb` | the approved reduced Glassback (`hes_glassback_reduce_claude/export/hes_glassback.glb`, copied to `work/`): geometry, rig, 9 clips, LODs **5,987 / 2,992 / 1,494 / 748** and textures unchanged; ONE skin `hgb_q` (her ramps, `scripts/body_variant.py`) replacing hgb_a/b/c |
| `export/hes_glassback_queen_crest_{spine1,spine2,spine3,tail1}.glb` | the family's `tall` crest (from `hes_glassback_claude/work/crest_v3.blend`, copied) without its Neck1 piece and without the two front midline plates on Spine3 (the bare neck under the crown); variant `hgb_q` |
| `export/hes_glassback_queen_crown_head.glb` | the crown on `Head` (`scripts/crown.py`): nine faceted glass spines on an ellipse round the crown of the skull (0.165 x 0.125 m at tier-A size), 0.38 m at the back to 0.16 m over the brow, splayed out a little, the rear ones upright; the family's crystal builder (`crystals.py`, copied) with glowing cracks, edge strips and root seams; LODs 568 / 333 / 72 / 45 |
| `integration/actors.yml` | staged binding (descriptor `hes_glassback_queen`, skin `hgb_q`, scale 200, the family's strides, look, beak socket, impact; 5 attachments) |

Glass in all: 2,426 triangles at LOD0 (crest 1,858 + crown 568); with the body 8,413.

## Colours (one tier)

- **Body** (`body_variant.py`): the family's region mask (R hide, G belly, A rust streaks). The hide (R and A) is a
  luminance-rank ramp: each of the 16 stops takes the queen palette's colour at that luminance's rank among the hide
  texels, so the dark scales and crevices are slate (16-85) and the brightest third of the plates pale mineral crust
  (118-165); belly pale ash (70-155). Viewer reviews 1-3 lowered it twice: the first palette (crust from rank 0.55,
  peak 230) read white next to the family's viewer shots (`review/viewer_shots_v1.png`).
- **Glass** (integrator review 2026-10-23: the crystals rendered near-black): the glass shells emit a dark navy
  (`emissiveFactor` [0.012, 0.035, 0.11]; 0.34 blue read flat light blue in the viewer), the cores, cracks, edge
  strips and root seams glow ice-blue at strength 2.5 (`emissiveFactor` [0.42, 0.68, 1.0] with
  `KHR_materials_emissive_strength`), crown and crest alike (`crown_post.py`); crack ramps ice-blue;
  the glass atlas is a copy of the family's with its teal glints turned ice-blue (`scripts/glass_hue.py`, hue +39
  degrees on saturated texels).

## Size and binding

x1.6 of the Glassback (tier B, scale 125) = **scale 200**: the back 2.38 m, about 3 m to the crown's tips, 5.7 m
long. Stage row: height 300, radius 160, reference `Crystal Walker C`. The Filter Beds' ceiling is 640 units above
the floor. Clips and timing are the family's (rear-up Attack, impact 1.083 s); at speed 250 the walk plays at 0.71
and the run at 0.43 of its rate.

## Checks

- **Crown clearance** (`scripts/crown_check.py`, every frame of every clip on the exported body: each crown spine as a
  tapered prism against every crest plate on another bone; its root against the deformed hide): min clearance
  Standing 14 cm, Walking 15, Running 18, Attack 15, Hit 10, Death 5.6, Dead 20, Fidget 16; roots worst gap -0.16
  sinks (never near -1, the open bottom); no tip inside the hide. Bite (the unbound secondary clip) touches by 3.6 cm
  on this conservative measure. The rear crown spines first raked back and met the crest's first plates when the
  head tips up; they now stand upright and the crest's two front midline plates are gone.
- Winding: 0 inverted closed parts on all 6 GLBs.
- Viewer `run_creature_review.py check`: 9/9 clips, no console errors; [shots](review/viewer_shots.png).
- Body gates unchanged from the reduced Glassback (floor, strides, corpse, LOD check: `hes_glassback_reduce_claude/README.md`).

## Doubtful / for review

- In the viewer one crown facet catches a white highlight from the front (the glass atlas' bright tile).
- The crown and crest glow is emissive factors on static attachments (no emissive texture); in game (D1 run,
  `../hes_custodian_claude/review/ingame/d01_fix_sheet.jpg`) the crest reads blue in a dim room.
- Her shots "glance off the glass" (EnergyImmune) are design/engine data, not the model.
