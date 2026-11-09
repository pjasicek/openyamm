# MM8 Bone Dragon — m616

Rigged, textured and installed for Skeletal Dragon / Bone Dragon / Undead Dragon (merged IDs 163–165;
descriptors Bone Dragon A/B/C). Agent visual review and desktop checks are recorded here; user artistic
acceptance is not yet recorded.

[Interactive viewer](http://127.0.0.1:8912/level_generation/creatures/mm8_m616_claude/review/viewer/)
uses the shared creature viewer with native sprite anchors, all six clips, three tiers and frame feedback.
The existing shared server must be running. [Final close-up](review/final_stills/m616_a_Attack_1_quarter_head.png).

## Asset

- 44 fitted bones: four legs, jaw, three neck segments, ten tail segments, articulated paired wings with four
  finger controls each, and `Socket_Mouth`.
- Open ribcage and skeletal joints retained. The intact Meshy wing was mirrored to replace the incomplete far wing;
  shoulder blending, foot ownership and a geodesic lower-jaw selection prevent stretched tips and teeth.
- 12,635 / 6,306 / 3,124 / 1,532 triangles in the four colour LODs, with matching shadow LODs. Maximum four skin
  influences. Thin wing/bone shadow margins are 0.3 / 0.5 / 0.7 mm; the full-detail geometry stays unchanged.
- One shared 2K base colour, 1K normal and specular/roughness/metallic maps. Bone is matte, membranes rougher,
  metallic zero. AO is retained separately; the engine MR red channel stores specular. Generated bone grain is
  softened and its normal detail reduced. The native tiers all use palette 616, so a zero-coverage region mask
  preserves the same base colour for all three material variants.
- Five original 1536×1024 HD views, prompts, hashes and generation receipts are in `references_hd/`.
  Meshy T2.5 Smart Topology cost 5 credits; the four-view Meshy-7 texture return cost 10. Total: **15 credits**.
  All 17,723 returned position/UV vertices matched the local master; only maps were applied to the retained rig.

## Motion and native placement

| Role | Clip | Duration |
| --- | --- | --- |
| Standing, walking, fidget, run | Fly | 1.000 s, seamless loop |
| Melee / ranged | Attack | 1.333 s, release at 1.000 s |
| Cast contract | Cast | Separate 1.333 s clip; native family has no spell slot |
| Recoil | Hit | 0.750 s |
| Collapse | Death | 0.750 s |
| Held remains | Dead | 1.000 s, fixed final Death pose |

The native backward collapse grounds the ribs, turns the skull sideways to clear its horns, and lays the wings
and tail out. Death/Dead match exactly. Dense eighth-frame sampling found minimum death Z −3.47 mm; held corpse
body contact is +14 mm in the authoring scale. Fly tips sweep to −18.01 mm; normal actor flight supplies altitude.
There is no added hover lift, following the flyer playbook. Fly maximum height is 255.97 game units at tier A,
below the native 450-unit collision height.

Tier A scale is 302.66102850110536, measured from mean front alpha area across the eight native fly frames
with their 1.5 SFT scale. B/C use the native scale-reference ratios (1.2 and approximately 1.4667).
See `work/scale.json`. The original billboard's vertical padding and camera-facing lean are deliberately not
added as a model hover offset. Same-camera comparisons keep ordinary AI live, so facing, flight position and
flap phase vary between runs.

## Runtime and verification

Source: `assets_source/worlds/mm8/models/mm8_m616.glb`; cooked runtime:
`assets_dev/worlds/mm8/models/mm8_m616.glb`. Three bindings are in `assets_dev/worlds/mm8/models/actors.yml`.
The shared dark projectile effect launches from the mouth; ordinary movement, collision, attack timing and loot
rules remain native. The game replaces completed corpses with satchels; the review viewer retains the Dead pose.

- Development `openyamm` build passed. The exact review binary is pinned at `/tmp/openyamm-m616-review-bin`;
  SHA-256 `5cd61657940bb6cdb870735732c7edca75f8372a221c002032c9891d79c54f73`.
- Focused Bone Dragon regression: 1 passed. Broader MM8 actor cases: **37 passed, 0 failed**.
  MM6 Demon simulation/death case: 1 passed.
- All three viewer tiers and six clips load: 18 switches, no browser errors. Normal/quarter-speed playback,
  skull, shoulders, recoil and corpse close-ups inspected.
- Blender-to-glTF reimport: maximum sampled surface discrepancy 0.0036 mm. No inverted closed components,
  duplicate-index triangles or zero-area triangles in the four colour LODs. UVs finite and nonzero-area.
- Original 135 sprite files and palette 616 verified unchanged.
- Native NVIDIA/OpenGL desktop captures: MM6 outdoor `oute3.odm`, indoor `6d19.blv`, native sprite comparisons,
  dark ranged attack, hit, collapse, satchels and forced LOD3. Evidence and run records: `review/ingame/`.
  Early downward indoor camera captures are retained separately; the final pair uses an upward camera to view flyers.

Reports: `review/static_audit.json`, `review/final_deformation_audit.json`, `review/texture_audit.json`,
`work/export_parity.json`, `review/regression/` and `review/delivery_checks.json`.

## Reproduction and limits

Claim the creature workspace before mutation; pass its current lease token to the shared wrappers.
`work/uv_master.blend` is the retained geometry/rig/action/UV authority and
`work/m616_textured_master.blend` is its textured export master.
`compose_bone.py` rebuilds maps from the retained texture return and AO;
`scripts/build_runtime.sh TOKEN --install` rebuilds the runtime package without another paid job.
The source frames and receipts are preserved, and all local edits are in `scripts/`.

Hidden anatomy and continuous motion are interpretations of the native sprites. The lowest LOD simplifies ribs,
claws and torn edges; its silhouette was checked in the game. Android was not built or tested.

## Texture quality pass (2026-10-31)

Pass of [the texture recipe](../claude_shared/TEXTURE_QUALITY_PASS.md) (user: "try the first three" of the MM6–MM8
ranking; worst MM6–MM8 atlas). Started from the installed GLB (reduction, floor fix and the lod_repair far LODs
included) and changed only UVs and maps: nodes, skin, six clips (byte-identical samplers), materials, variants, shadow
meshes and LOD2/LOD3 geometry are unchanged; LOD0 positions, normals, joints and weights are identical per triangle
corner (`work/texpass/structure_diff.py`). Before state: `work/before_texpass/`.

**Route (`scripts/`).**
1. `texpass_uv.py`: imports the installed GLB, welds the glTF seam duplicates that share weights (14,138 -> 4,718
   vertices), `claude_shared/uv_atlas.py` with `cut_closed=1 max_stretch=1.8 retry_stretch=3.0 merge_below=20 fine=250
   steps=0` (variant v4 of five in `work/texpass/`; the brute-force packer gave 48.3 %), head x1.8. Writes the corner
   UVs per GLB triangle and the neutral upload `texturing/bone_dragon_upload_texpass.glb`.
2. Retexture `requests/retexture_v2.json` (same four HD masters, meshy-7, **4K**, our UVs), job `retexture_v2`,
   **10 credits** (backup account). The return keeps the layout (`texture_quality.py`: 49.0 %).
3. `texpass_ao.py` (AO on the new UVs, as `bake_ao.py`), `compose_texpass.py` (compose_bone.py's bone/membrane
   recipe: colour 4K -> 2K and normal 4K -> 1K once, Lanczos; parts from `work/uv3d.npz` by nearest triangle) with
   `--soften 0 --crack-fill 6 --crack-lo 12 --crack-hi 40`, then `tone_texpass.py ... 1.0` -> `textures/texpass_20261031/`.
4. `patch_glb.py --corners` (LOD0 re-indexed, vertices split at the new seams) and the three maps; LOD1 from
   `texpass_lod1.py` (tools/build_actor_lods.py, the installed ratios 0.5/0.25/0.125, 4 influences; same 4,408
   triangles and positions as installed, new UVs); `far_lod_textures.py` refills the installed LOD2/LOD3 maps from the
   new LOD0 with lod_repair_claude's `transfer_textures.transfer` (meshes and their UVs kept; a `repair.py` rerun
   would rebuild other far meshes from its `originals/`). Output `export/mm8_m616_texpass.glb`.

**Drift and its fix.** The 4K paint covered the bone with a black crackle network (cells of 2-6 px dark lines; sheet
`review/texpass/probe_s0_sheet.png`) that neither the HD masters (smooth ivory) nor the approved paint have (bone luminance p5 19 against 92 approved),
and once the cracks were filled it was lighter and higher in contrast (p5/p50/p95 122/197/225 against 98/169/203). `--crack-fill 6`
fills thin dark lines on bone (black-hat of a radius-6 disk closing) from the surrounding bone; `tone_texpass.py`
maps each class's luminance quantiles onto the approved paint at the same surface points (points where both class maps
agree) and moves the class's mean chroma to the approved one (the membrane came back slightly blue). Result: bone
93/168/203, membrane 32/67/92 (approved 38/67/89). compose_bone.py's ivory blur is off (`--soften 0`). The membrane
keeps a finer pebbled grain than the old streaky mottling.

| Measure (`texture_quality.py`, LOD0) | Before | After |
|---|---|---|
| Atlas use (2K) | 7.2 % | **49.0 %** |
| Equivalent fully used square | 551 px | 1,433 px |
| Texels per creature size p10 / p50 / p90 | 635 / 764 / 817 | **1,988 / 2,080 / 2,296** (x2.72 linear) |
| Density spread p90/p10 | 1.29 | 1.16 |
| Islands / surface on fragments | 2,853 / 48.4 % | 578 / 4.8 % |
| UV stretch p90 | 1.63 | 1.29 |
| Meshy source | 2K on 7 % | 4K on 49 % (2,866 px equivalent) |

Targets: atlas 49 % is below the 55-60 % automatic charts reach on solid bodies; this one is 78 thin closed pieces
(ribs, vertebrae, wing fingers, membranes as single sheets), and every packer variant gave 48-49 %. Fragments 4.8 %
(target 3) are charts of thin bones, not small pieces (pieces under 8 triangles are 0.1 % of the surface). Known
flaw: 10 triangles (0.03 % of the surface, 8-41 mm² each) have zero UV area and sample a line of texels.

**Checks.** Winding 0 inverted closed parts; flat-shading 0.00; `detached_parts_audit.py` identical to the installed
GLB (78 components, 5 detached in some pose, the same parts); floor audit Bone Dragon A/B/C ok; viewer `check` 18
switches, 0 errors; regressions `mm8_bone_dragon_actor_models_keep_native_tiers_and_motion` and
`mm6_mm7_mm8_actor_models_build_every_binding` (647 descriptors on 185 models) passed; LOD1 colour against LOD0 at the
same surface points as installed (mean 14.9 vs 13.8 levels). Installed with `tools/install_model.py --world mm8`
(desktop cook: 11 textures). Not done: in-game run, Android cook.

Sheets (review viewer, identical cameras; `review/texpass/shots.txt`, `claude_shared/texpass_viewer_shots.py`; the
viewer's `index.html`/`review.js` were restored from the Magreeb's with dragon focus presets):
`review/texpass/texpass_closeup_sheet.png` (head, side head, ribs, tail, feet), `texpass_body_sheet.png` (full body,
wings front/back, Attack, Dead), `texpass_tiers_sheet.png` (A/B/C; the tiers share one base), density heatmaps in UV
space on one scale `texpass_density_heatmap_uv.png`. Viewer manifest revision `mm8_m616_texpass_20261031`.
Rollback: `python3 tools/install_model.py level_generation/creatures/mm8_m616_claude/work/before_texpass/mm8_m616_installed.glb --world mm8 --name mm8_m616.glb`.
