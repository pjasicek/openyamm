# MM7 Peasant Human2 Male (m362): 9 outfits/tiers — Claude rig-first project

MM7 batch K, model 3 ([batch file](../mm7_batches/BATCH_K.md)). Humanoid playbook default route (source-frame rig with
gates) on the scripts of [`mm7_m352_claude`](../mm7_m352_claude/README.md) (unarmed peasant: no held prop, no attack,
no run, both hands loosely curled). **Not installed.**

[Review viewer](review/viewer/index.html) (serve the creatures folder over http) · [viewer shots](review/shots/) ·
[clay clips](review/g7_clay_front.png) · [G1 candidates](review/g1_front.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m362.glb` | runtime: LODs 9,448 / 4,718 / 1,695 / 558 triangles, shadow LODs, 9 variants `m362_aa` .. `m362_cc`, head material merged (4 atlases 2080×1024), clips Standing, Walking, Hit, Death, Dead, Fidget |
| `export/mm7_m362_lod0.glb`, `work/rig_v6.blend` | textured LOD0 export (tier A base colours) and editable master |
| `textures/` | body 1K set, head 1K set, region masks (R doublet, G hair, B jaw stubble), `m362_ramps.json`, material class maps |
| `integration/actors.yml` | staged binding for the nine descriptors |

Install later (user decision), from the repository root:

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m362_claude/export/mm7_m362.glb --world mm7
```

then append `integration/actors.yml` to `assets_dev/worlds/mm7/models/actors.yml` (descriptors `Peasant Human2
Male<A|B|C> <A|B|C>` = monsters 367–375, skins `m362_<outfit><tier>`; scale 91.3 = `m362sa0` 194 px × dsft 0.799988 =
155.2 units over the 1.70 m model; stride 1.784 m; look 60°/35°). Speed 140 is below the run threshold (2.4 × 91.3):
run → Walking. The native attack reuses the walk poses (`m363w` for both in `monster_descriptors.txt`), so
`attack_melee`/`attack_ranged` play Walking (no impact event); cast → Standing.

## Variants

One mesh, rig and clip set for all nine looks (identical native frames; only the palette changes). Three recolour
regions, ramps from each palette's own region entries (`scripts/compose_m362.py`, native stand/walk pixels):
R doublet and shoulder rolls (variants.json `purple_vest` indices plus the other purple entries that change;
ramp window 35–97 %), G hair (96–117), B jaw stubble (76–93: skin tones in tier A, beard colours in the others; a
soft 0.7 jaw mask on the head set only, as the native `jaw_stubble` region).

| Skin | Descriptor | Palette | Doublet / hair / stubble |
|---|---|---|---|
| m362_aa | MaleA A | 363 | violet / blond / none (skin) |
| m362_ab | MaleA B | 364 | green / brown / grey |
| m362_ac | MaleA C | 365 | red / black / black |
| m362_ba | MaleB A | 366 | violet / white / white |
| m362_bb | MaleB B | 367 | black / blond / blond |
| m362_bc | MaleB C | 368 | olive / ginger / none |
| m362_ca | MaleC A | 369 | grey / dark brown / none |
| m362_cb | MaleC B | 370 | brown / ginger / ginger |
| m362_cc | MaleC C | 371 | blue / grey / none |

## Model

- HD masters (Codex, `references_hd/`): primary v2 (corrective run, open hands) and four views; head turnaround in
  `references_head/` (clean-shaven). Gated against `source/native_standing_views.png`.
- Smart Topology 15k (14,284 triangles, 46 parts): head/neck/chest, two hand shells, breeches, doublet and its skirt,
  boots and boot cuffs, puffed shirt sleeves and cuffs, shoulder rolls, hair and strands, collar, belt, rapier hilt
  and scabbard, eyes, mouth, laces, studs. Nothing removed. Reduced after weighting to 9,448 (skin 6,000 with head and
  hands protected, shoulder rolls 600, hair 900, belt/collar/skirt/cuffs 800, rapier 500).
- Rig: source-frame rig (52 bones + 4 twist), Meshy auto-rig for the axial joints and elbows (t 0.51 / 0.49), ring
  centres for wrists (at the cuff opening)/ankles, fingers by connectivity on the hand shells (P01 left, P02 right).
  Frame error 0; hand frames within 28°.
- Weights (`weights_fix.py`): skin = Meshy + shoulder fade + jaw free of the shoulders; eyes/mouth rigid head; hair head
  → neck → chest by height; shoulder rolls copy the skin (arm share ≤ 0.35, smoothed); doublet skirt, collar, belt and
  boot cuffs copy the skin without arm weight; **rapier and scabbard rigid on B_Pelvis** (hung outside the left leg; no
  contact with the leg seen in the walk, hit or fidget clay renders); laces/studs rigid on the dominant bone. New rule:
  the doublet and shirt collars lose their head weight to B_Neck and the neck band gets 6 smoothing passes (a 4.4–6.5x
  tear at the nape when the fidget looks down). Finger webs as m352.

## Clips (G1: candidates rendered on this rig, `review/g1_front.png`)

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | feet levelled |
| Walking | Mixamo Standard Walk (upper arms out 6°) | constant foot tilt removed, floor lift; stride 1.784 m |
| Hit 1.0 s | Mixamo Standing React Large From Front, planted | one arm flung up, head thrown back (native `m362n*`); eased 0.2/0.2 s |
| Death 2.2 s | Mixamo Falling Back Death | falls backward with the legs up (native `m362d*`); travel halved, floor pass |
| Fidget 5.1 s | Mixamo Standing Idle 03 Examine, planted | looks at his raised hand |

Both hands keep 60 % of the source finger curl. Rejected: Head Hit (hands to the face), Looking Down.

## Gates (2026-10-20, `work/gates_final.txt`)

- G4 arm stretch p99 ≤ 1.99 in every clip except Fidget left 2.25 (the wrist band at the clip's strongest wrist bend:
  the hand shell starts inside the cuff, so the forearm twist reaches the hand base); max 2.64.
- G5 hands: right ≤ 2.20x, left ≤ 3.11x (Death).
- G6: forearms ≤ 3.4 cm under the open shirt-sleeve shells (proximity of open shells, not a skin crossing); the right
  hand 4.8 cm into the body for a few frames of the fall (source motion).
- Soles: Standing −1.4 cm, Walking −1.7…+1.7 cm, Hit/Fidget 0…0.7 cm.
- Jerk: follows the sources.
- Viewer: `tools/run_creature_review.py check` 54/54 tier/clip switches, no console errors; shots in `review/shots/`.
- In game: not checked (optional in batch K; nothing installed).

## Meshy

**30 of 100 credits**: Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10.

## Replay

```sh
TOKEN=<lease> STAGE=rig scripts/rebuild.sh; TOKEN=<lease> STAGE=anim scripts/rebuild.sh
# textures once: export_uploads.py -> Meshy jobs -> transfer_uv.py -> uv_raster.py (UVMap, HeadUV) -> bake_ao_natm.py
python3 scripts/compose_m362.py && python3 scripts/tier_preview.py
TOKEN=<lease> scripts/build_runtime.sh        # no install step
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
TOKEN=<lease> scripts/gates.sh                # G4, G5, G6, soles, jerk
```

## Walk and ankle fix (user review 2026-10-20)

Batch A/J's walk fixes (`mm7_m222_claude`, `mm7_m302_claude`), applied in the chain and replayed (STAGE=anim, runtime,
viewer); previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`. Measured by
`scripts/walk_probe.py` (head height second difference, foot world-rotation step change per frame):
- **Ankle twist:** `foot_level.py` updated to batch A's rule: the walk takes one constant roll per foot in the foot's
  own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted); the
  other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved
  to the same ankle paths).
- **Walk clip:** Mixamo Standard Walk replaces Mixamo Walk (as batch J's humans and the MM6 male peasant): Walk's own
  feet change up to 17° per frame, Standard Walk's 10–11°. Its forearms swing into the tunic side, so the walk's upper
  arms are turned out 6° (`abduct_arms.py`, from m442).
- Result: head second difference 6.31 → 0.78 cm; foot rotation step change 17.1° → 11.7/10.3° (batch J: 10.3–11.8);
  soles within −1.4…+1.0 cm; stride 1.784 m (binding updated); viewer check 54/54.

## Known limits / for user review

- The walk's left hand swings past the hanging scabbard (within a few millimetres at the back swing).
- No attack clip: the binding plays Walking in place for attacks, as the native sprite does.
- The scabbard hangs straight down beside the left thigh (the native angles it backward); rigid on the pelvis.
- Fidget left wrist band p99 2.25 (slightly above the ~2 guideline).
- The doublet keeps some of Meshy's darker mottling in every tier; the shoulder rolls' white stripes are irregular.
- The death ends with one knee raised (Mixamo); the native corpse lies flat.
