# MM7 Archer (m154): Archer / Bowman / Elite Archer — Claude rig-first project

MM7 batch A, model 5 ([batch file](../mm7_batches/BATCH_A.md)). Same route and chain as the batch's fighters
([`mm7_m406_claude`](../mm7_m406_claude/README.md)) with the bow, string and arrow rules of the elf archer
[`mm7_m214_claude`](../mm7_m214_claude/README.md), mirrored: the native archer holds the bow in the RIGHT hand and
draws with the LEFT, from a quiver over the left shoulder. **Installed 2026-10-20 (reduced exports).**

[Review viewer](review/viewer/index.html) · [action sheet](review/shots/actions_sheet.png) ·
[gates](review/gates_final.txt)

**Accepted, reduced and installed (2026-10-20):** installed 2026-10-20 from [`../mm7_batches/BATCH_A_stage/`](../mm7_batches/BATCH_A_stage/README.md). **Reduced (user: "reduce tris"):** the exports to install are now the ones in [`../mm7_m154_reduce_claude/`](../mm7_m154_reduce_claude/README.md) (body LOD0 10,253 -> 8,383, bow 988 -> 524, arrow 342 -> 210; same UVs, textures, tiers and clips; install commands there). This project's `export/` is their source and rollback.

## Deliverables

| File | What |
|---|---|
| `export/mm7_m154.glb` | runtime body: LODs 11,583 / 5,789 / 2,074 / 687 triangles (LOD0 incl. bow 988 and arrow 342 before the split; body 10,061 + string tube 192), shadow LODs, 3 tier variants (`m154_a/b/c`), head material merged, clips Standing, Walking, Running, Attack, Hit, Death, Dead, Fidget, `Socket_Arrow_Release` |
| `export/mm7_m154_bow.glb` | bow attachment on node `Bow` (988 / 494 / 176 / 58 triangles) |
| `export/mm7_m154_arrow.glb` | nocked-arrow attachment on node `Arrow` (342 / 171 / 60 / 24; node scale 0 = hidden) |
| `export/mm7_m154_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (viewer source) and editable master |
| `textures/`, `integration/actors.yml` | texture sets, region mask, `m154_ramps.json`, string swatch; staged binding |

Install later (user decision):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m154_claude/export/mm7_m154.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m154_claude/export/mm7_m154_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m154_claude/export/mm7_m154_arrow.glb --world mm7
```

then append `integration/actors.yml` (`Archer A/B/C`, scale 103.0 = `m154sa0` 219 px × dsft 0.8 = 175.2 units over
1.70 m; walk stride 1.683 m, run stride 2.031 m; impact and arrow release 1.167 s on `arrow_release`; look 60°/35°;
bow on `Bow`, arrow on `Arrow`). Speeds 140/150/160 are below the run threshold (2.4 × 103 = 247): every tier walks.

## Model

- HD masters `references_hd/`: primary v2 **mirrored** (the return put the quiver over the right shoulder; the design
  is otherwise symmetric, recorded in `generation_runs.json`), four views, `bow.png` (bow and arrow); head turnaround
  `references_head/`.
- Smart Topology (15,086 triangles, 25 parts, nothing removed): tunic with gorget, pauldrons and short sleeves (one
  shell), legs and boots, head, separate hands, mail forearms, helmet + horns + spike, mail coif, diagonal strap, fur
  quiver and its seven arrows, buckle, eyes. Reduced after weighting to 10,061 (head and hands protected).
- Rig: source-frame rig; Meshy elbows, wrists and **ankles** (`ANKLE_FROM=meshy`: the ankle rings sat at the boot tops,
  z 0.196 vs 0.128); fingers by connectivity on the gloves (`fit_fingers.py` falls back to the smallest piece as the
  thumb when no piece lies near the carried thumb base).
- Weights (`weights_fix.py`): m406's rules on the tunic shell P00, but the "no arm weight below the chest" rule only
  medial of the armpits (the shell also carries the pauldrons and sleeves; the plain rule left 17 shoulder vertices
  unweighted, which stood up as spikes from the corpse); quiver and arrows rigid on `B_Spine2`; strap copies the skin
  without arm weight; helmet group rigid head; coif copies the skin.
- Bow, string, arrow (`make_bow.py` from `bow.png`, python3 then Blender): limbs traced as octagon rings, 1.29 m,
  17 cm brace; arrow 0.80 m (shaft, flat head, three vanes). `bow_tracks.py` puts `Bow` on the solved right fist
  (`R_HANDLE=0.016`), +Y up at full draw, +X toward the string chosen so the full-draw pinch lies in the bow plane;
  `StringNock`, `Socket_Arrow_Release` (arrow rest in front of the grip) and `Arrow` (child of `B_Pelvis`, keyed in
  world terms). The string is a 6-sided tube in the body mesh (`Bow` ends, `StringNock` middle, a linen swatch of the
  body texture).

## Clips

| Clip | Source and adaptation |
|---|---|
| Standing | Mixamo Standard Idle; bow low in the right fist (native m154sa) |
| Walking | Mixamo Walk (1.683 m stride), floor lift |
| Running | Mixamo Standard Run + run fit (unused in game: all tiers walk) |
| Attack | Mixamo Standing Draw Arrow + Standing Aim Recoil, **mirrored** (`retarget_mixamo.py` `:mirror`), joined (`concat_actions.py`), **unplanted: he turns side-on** like m214 (`bow_stance.py`: the source's 0.9 m bow stance narrowed to 40 % of its spread from Standing's feet, pelvis raised 85 % of its drop, legs by IK, the pelvis turned back by the full-draw aim so the arrow points straight ahead: −0.9°, head +0.8° at the release; review 2026-10-20, planted he aimed 86° to his right), 0.1 s lead + 0.3 s blend-in from Standing: arrow taken from the quiver (0.43 s), nocked (0.67 s), drawn 68 cm to the cheek, **released at 1.167 s** (string snaps back with a 1 cm overshoot, arrow hidden), lowered; 1.83 s |
| Hit | humanoid set Unarmed get-hit F1, blended |
| Death / Dead | Mixamo Falling Back Death (travel halved, floor pass) / last pose held, arrow hidden |
| Fidget | Mixamo Sword And Shield Power Up, planted, bow carried in the right fist |

Feet (review 2026-10-20, "slightly angled on the boot edge"): `foot_level.py` also levels the sole's roll about the
heel–toe line on grounded frames (every clip had rolled the boots 4–11° onto their outer edges; now ≤ 1° standing,
attack and fidget, ~2° median walking) and moves the pelvis so floor contact is unchanged; `Running:rollonly`. Walk and run take one constant roll per foot in the foot's own frame and one constant pelvis shift (review 2026-10-20: the per-frame roll switched on and off as the feet landed and lifted, a visible ankle twitch; foot rotation per frame is back to the source's). Hit, Attack, Fidget, Death and Standing: the roll is weighted by flatness (planted and level lengthwise), capped at 20 deg and smoothed over the clip (batch C's rule, mm7_m218_claude; peer report 2026-10-20: the groundedness-only roll snapped a stepping foot in Hit up to 22 deg and a lifting foot in Death up to 65 deg per frame); every clip's foot turn per frame is now within 2 deg of the source's. Walk bob (review 2026-10-20, "uneven head bob"): `walk_bob.py` after `clip_timing.py` smooths the walk's pelvis height over the loop (both steps alike, ankles kept reachable) and re-solves the legs to the same ankle paths and foot rotations; the retarget's floor rule had left a zigzag and up to 3.7 cm frame jumps.

`arm_clear.py` swings the left upper arm out ≤ 24° where the draw anchor sank into the bulky helmet/coif; the bow is
cleared from the body like the fighters' blades (`sword_clear.py` with `BLADE_T=-0.6,0.6` along the grip axis).

## Gates (2026-10-20 after the aim and foot-roll review fixes, `review/gates_final.txt`)

- **G4 arm stretch p99 2.17 (left, full draw), max 5.02 on the right sleeve hem with the bow arm raised** — slightly
  over the ≲ 2 guideline (deviation). Smoothing the sleeve weights (6 passes) made it worse (2.40) and is off.
- G5 hand stretch: right 3.75x, left 3.54x.
- G6: walk/run clean of the bow; attack: the left hand stays up to 6 cm inside the helmet/coif around 1.25 s (just
  after the release; `arm_clear` unresolved at its 24° cap); fidget: the lower bow limb 4.7 cm into the boot around
  1.73 s; death: hands and bow up to 6 cm into the lying body (as the fighters).
- Soles: −1.8…+1.4 cm (walk −1.3…+1.3); attack −2.5…−1.2 (the side-on stance's left boot ~0.5 cm deeper than
  the ±2 cm guideline; Standing itself sits at −1.8). Jerk: the attack start no longer jerks (26° → ≤ 3.5° second difference after
  the 0.3 s blend-in); worst attack step 16° per 1/48 s while lowering the bow.
- Viewer: 24/24 tier/clip switches, no console errors; textured shots of every clip and tier inspected (full draw:
  arrow on the string at the left glove, string to the cheek; corpse flat). In game: not checked (nothing installed).

## Textures and tiers

`compose_m154.py`: body/head 1K sets (Meshy UVs copied back exactly, 0 mm); skin (head only; the gloves are leather)
repainted to one dark albedo; AO; ORM per class (gold limited to the gorget, pauldron trim, helmet and buckle, so the
olive boots and gloves stay leather). One recolour region **R = the green tunic**: the green palette entries that
differ between the tier palettes (56 entries, 143–203). Tiers: A 155 green (base), B 156 blue, C 157 red. The bow and
arrow have their own small textures (no tier region).

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5 (joint estimates), body retexture 10, head retexture 10. No paid
animation (Mixamo clips from the library).

## Replay

`TOKEN=<lease> STAGE=rig WRIST_FROM=meshy ELBOW_FROM=meshy ANKLE_FROM=meshy scripts/rebuild.sh`, then
`STAGE=anim DEATH_UNTIL=12 R_HANDLE=0.016 LEAD=0.1 LEFT_CURL=1 BLADE_T=-0.6,0.6 scripts/rebuild.sh` (twice on a fresh
project: the second pass uses the solved grip; the chain ends with `bow_tracks.py`); `make_bow.py` (python3, then
Blender); texture chain (`export_uploads.py`, Meshy jobs, `transfer_uv.py`, `uv_raster.py` UVMap/HeadUV 1024,
`bake_ao_natm.py`, `compose_m154.py`); `scripts/build_runtime.sh`; `viewer_tiers.py`; `update_viewer_manifest.py`.

## Known limits / for user review

- Tunic emblem: the HD masters (and so the texture) show a white **tree**; the native manifest calls it a white bird.
- Handedness follows the native sprites (bow right, draw left), mirrored from the Mixamo archery clips.
- G4 sleeve-hem stretch at full draw; left hand close to/inside the coif just after the release; bow tip brushes
  the boot in the fidget.
- The bow (988 triangles) is denser than the sword props; its LODs drop to 58.
