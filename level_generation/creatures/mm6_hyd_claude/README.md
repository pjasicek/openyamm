# MM6 hydra (hyd) — 3D model, 2026-10-09 (v4: grafted head models, lofted joints; chin seam fix)

Hydra (descriptors BHydra A/B/C, 559–561; palettes 754/755/756), installed as
`assets_dev/worlds/mm6/models/mm6_hyd.glb`, bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via
`debug.actor_models=true`).
Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_hyd_claude/review/viewer/> (checked with
`claude_shared/check_viewer.mjs`). In-game capture: `review/ingame_tiers_v4.png`; head close-ups, 15k source against
the shipped head: `review/head_budget_check.png`.

| Item | Value |
|---|---|
| Body | Meshy `multi-image-to-3d` (four views, 20k; second tail removed), bent-pose reduction to 11k, old heads cut off |
| Heads | five separate head models: Codex head masters (`references_heads/h<k>/`, five views each) → Meshy Smart Topology 15k → retexture on clean UVs (2K) → cut behind the skull, reduced (1.4–2.4k each), placed rigidly and joined to the necks by lofted tubes |
| LOD0/1/2/3 | 17,590 / 8,790 / 3,150 / 1,020 (body and necks 6.6k, joint tubes 1.9k, heads 9.1k: olive 1.4k, purple 1.8k, green 1.4k, red 2.4k, blue 2.1k) |
| Textures | body set 2048² (body and necks); head set 1536×1024 (one 512×512 tile per head); normal maps at the same sizes, metal/roughness (AO in R) and masks at half size |
| Rig | 74 bones: body chain (Body_Root, Tail_01..) + five neck chains (Neck<k>_00.., Head<k>), k left to right in the front view; skulls rigid on Head<k> |
| Clips (24 fps) | Standing 3.0 s, Walk/Attack/Hit/Fidget 0.75 s, Death 0.625 s (native timing), Dead (last Death pose) |
| Tiers | 17 regions over five materials (`Hydra`, `HydraB` on the body set; `HeadsA/B/C` on the head set): body, five necks, five skulls, five neck stubs, head 4's fins |
| Scale | 273 (native stand frame 210 px × frame scale 1.3 against the 1 m model); B/C via `scale_reference` (1.45, 1.6) |
| Meshy credits | 160 of 300 (v4 used none): body model 30; v2 head retextures 50 and a 200k remesh 5 (both superseded); five Smart Topology heads 25; five head retextures 50 |

## Pipeline (scripts/)

1. Body: `prepare_hyd.py` (→ `hd_source.blend` uncut, `hd_base.blend`), `remove_tail.py` on `hd_base`,
   `rig_hyd.py` on `hd_base`, copy `rig_v1.blend`/`rig.json` to `rig_20k.*`,
   `reduce_bent.py 11000 red_11000.blend 99999`, `rig_hyd.py` on `red_11000` (→ `rig_v1.blend`, `rig.json`).
2. Heads: Codex briefs `references_heads/h<k>/CODEX_BRIEF.md` (five masters per head) →
   `requests/head<k>_smart_topology_v1.json` (5 credits each) → `head_fit.py` (neck centreline, trims, clean UVs,
   `texturing/head<k>_st_upload.glb`) → `requests/head<k>_retexture_v2.json` (10 credits each).
3. `build_heads_pipeline.sh [--install]`: `graft_heads.py` (→ `rig_graft.blend`, heads cut and lofted onto the
   necks; the retextured heads placed the same way as `heads_hi.blend`) → `uv_atlas.py` (→ `hd_atlas.blend`) → `bake_hydra.py` (both sets: base colour,
   roughness, normal, AO) → `anim_hyd.py` → `dump_uv3d.py` → `compose_hyd.py --assemble` (padding; loft texels copied from the necks) → `grade_basecolor.py` per
   set → `compose_hyd.py` → `build_runtime.sh` → `viewer_tiers.py`.
4. Gates: `check_heads.py` on `anim_v1.blend` (no head triangle intersects another head, neck or the body in any
   frame of any clip: currently 0 everywhere), `update_viewer_manifest.py` + `check_viewer.mjs`, the
   `mm6_hydra_actor_model_tiers_follow_sprite_scales` regression.

## Notes

- **v3 (user review of v2: "head textures are smeared", junction smear; 512² per head wanted).** The v2 heads were
  the full-body model's own heads: ~3% of its mesh and ~150 reference pixels each, crude in shape, and their
  retextures were painted onto hundreds of UV slivers. v3 gives each head its own Codex masters and its own Smart
  Topology model (the whole budget of a 15k mesh and a 2K texture per head), unwrapped before the retexture
  (smart projection at 66°: 0–3% of the area stretched past 2:1; normal-binned charts left 12–55% within 2× density),
  and baked into its own 512² tile.
- **Graft** (`graft_heads.py`, v4 after user review: "heads are not joined properly", distorted texture at the
  joints): each head is cut just behind its skull (a plane across its own neck; only surface near the neck axis is
  cut, so horns and fins sweeping back stay whole) and placed rigidly: snout on our snout tip, skull axis on our Head
  bone, scaled so the skull is 1.3× our neck width. Our neck is cut 6 cm further back and a lofted tube joins the
  two rings: a Hermite centreline leaving the skull along its own neck direction and arriving along ours, with the
  cross-sections blended between the two ring shapes and zipped to both. v3 bent each Meshy neck stub onto our neck
  instead; the stubs arch the opposite way and some are separate shells, so they folded and tore. The old head goes
  by a flood fill from its snout through everything in front of our cut, plus old horn and fin parts in a 15 cm band
  behind it. The loft's texture is a copy of the neck just behind it, matched by angle round the neck (baked from the
  20k model, the lofts showed the old heads' pale, smeared surface); its normal map is flat. Weights blend from
  Head<k> at the skull to the neck's weights at our ring. Budget pass: head budgets 1.4–2.4k and joint tubes of 24 sides with 2.5 cm ring spacing (they were 40 sides at
  1.2 cm: 2.9k triangles for smooth tubes) took LOD0 from 20.9k to 16.75k with no visible change in same-camera
  front, side and back close-ups (`work/budget/cmp_{f,s,b}.png`). Per-head scale corrections (`SCALE_FIX`, head 1 0.8,
  head 4 0.88) and a lateral squeeze of head 2's jaw spikes and head 4's fins keep the heads from touching.
- **Chin seam (user review, 2026-10-09: the purple head's chin/throat looked "badly textured/stitched").** Two
  causes: the zip between a dense head ring and a 24-sided loft fanned into long sawtooth triangles, and the heads
  were cut 0.46 behind the snout, so each kept a stub of Meshy's own neck paint (the Codex masters' neck colours)
  ending in a jagged edge. Now heads 1, 2, 3 and 5 are cut at the skull/neck colour split (`CUT_N` 0.40, so no
  stub); head 4 keeps 0.46 (its fins are rooted behind the split; at 0.40 they came off and the old body's grey fins
  showed). Our necks are still cut at 0.46 + 6 cm (`PIECE_N`), so the old heads go exactly as before and the joint
  tubes are 2–3 cm longer; the loft takes as many sides as the head ring (24–64). Head versus neck colour
  follows the graft's skull flag (horns, fins and crests behind the split stay head-coloured). The head bake runs
  per head against its own high-res model, a tight pass (cage 8 mm; wider washed out the fins) then a wide pass that
  only fills its misses. Close-ups: `review/chin_fix.png`.
- **Joint-tube smears (user check 2026-10-09: streaks behind heads 3 and 5).** The loft texels copy the neck behind
  them; their angle and arc used to be measured against the bone chain, and on the outside of a tight bend many texels
  projected onto one joint, so one band of neck was stretched into streaks. The graft now writes each loft vertex's
  distance from the skull ring (`loft_s`) and the matching point on our neck ring (`loft_ref`); `dump_uv3d.py` carries
  them and `compose_hyd.loft_transfer` copies by those. Before (top) and after: `review/loft_smear_fix.png`.
- **Clips with wide heads**: `anim_hyd.pose` turns neighbouring necks apart whenever two heads come closer than at
  rest; the Fidget's inward look became an outward look of the outer heads (inward, the horns and fins swung into
  the neighbours).
- **Junction smear fixed**: the tube unwrap distorts where the necks merge; faces whose tube map is anisotropic
  (clusters ≥ 15 faces) get an angle-based unwrap instead.
- **Neck and body ramps by palette transfer** (2026-10-09, `NECK_TRANSFER` in `compose_hyd.py`): each stop takes
  the native sample pixels nearest in luminance in palette 754, read in the tier's palette (claude_shared/
  native_shading.py `transfer_ramps`, gain 1.25). No brightness bake: the necks bend in every clip. Pre-transfer
  files: `textures_pre_native/`.
- **Ramps**: no luminance remapping; every region has its own native samples. Head samples stop at the 85th
  percentile (the brightest native head pixels are eyes and glints, which turned tier B's red head white-eyed).
  Head 4's fins are their own region (tan, blue-grey, green per tier). Ivory (horns, teeth), eyes and mouths keep
  their raw colour; the region labels are padded past island borders so no raw-colour lines show at plate edges.
- **Second tail**: the left and right body references put the tail on opposite sides and Meshy built both;
  `remove_tail.py` cuts the right-hand branch and caps only that cut; the bake reads the uncut source, with texels
  inside the old tail root filled from the capped mesh.
- Known limits: the eyes stay yellow in every tier (tier C's are green natively); head 2's back-of-skull crest is
  dark in tier A; Dead is the last Death pose (necks lying forward), not the native corpse pose.
