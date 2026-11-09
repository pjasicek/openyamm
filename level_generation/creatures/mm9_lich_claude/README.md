# MM9 Lich (mm9_lich) — 3D actor, 2026-10-30

## Dropped MM9 clips (2026-10-31, run2-clips-groupD) - current

The user lifted the hold on this approved project for clip grafting only. Missing: die2, Backpedal, BackpedalRun; all carried.
`scripts/extra_clips.sh` (roles `scripts/roles_lich_extra.json`, `scripts/floor_ops_extra.txt`, new `scripts/cloth_flat_extra.py` =
cloth_flat.py on Death2/Dead2) grafts them onto the installed export (`work/pre_clips_export.glb` kept); byte check OK,
21.15 -> 21.55 MB. Bound in the shared `&mm9_lich_script_clips` (Lich A and B): death2, dead2, backpedal, backpedal_run.
Gates (`review/clips_restore_D/`): floor Backpedal -1.9..+1.3, BackpedalRun -1.9..+3.0, Death2 -2.4 (accepted dying -3.9),
corpse 0 but, as the accepted Dead, it rides 14 cm up on its sleeves (cloth_flat could not lay Box01-04 flat); hands Backpedal L
2.0 cm on 3 frames, BackpedalRun L 1.7 cm on 1 (accepted Walking 0.8 / 1.0), forearm 3.5 cm (as Walking); limb bones within 6 %;
jitter arm joints 0 excess, Death2 shoulder skin 5.5 mm/f2 (accepted Death 3.4-3.6, also flagged). Strip `strip_new_0.png` read.
Not looked at in the viewer or in game.
Edits to approved files (opt-in, defaults unchanged; the patched `clips_mm9.py` rebuilds the accepted clips byte for byte): `clips_mm9.py` gained roles-json `soft_offsets` (the soft joint-offset line) and a per-role `hold`; `scripts/bind_actor.py` carries the new script clips.

Monster rows Lich L45 (`MONSTERS.txt` 207, descriptor `MM9 Lich A`) and Power Lich L55 (208, `MM9 Lich B`), `LICH.abc` with
skins `LICH1.dtx` / `LICH2.dtx`. The Lich King is a separate body (`lichking.abc`) and is not here. Built on the approved
MM9 humanoid route ([brief](../claude_shared/MM9_HUMANOID_BRIEF.md)): MM9 skeleton and clips, never Mixamo.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_lich.glb` (`tools/install_model.py --world mm9`; cooked copy in `assets_dev`) |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, block `mm9_lich_claude`: `scale: 120` (100 x MONSTERS Scale 1.2), `yaw_offset: -1.570796327`, look `Bip01 Neck, Bip01 Head`, stride 1.06 / run 2.66 |
| Triangles LOD0/1/2/3 | 9,601 / 4,798 / 1,725 / 573; LOD0: skull 3,000, cloak 2,250, hands 1,319, robe 759 + lining 759, boots 640, pants 280, belt 240, hood and boot linings 238 |
| Skeleton | 49 MM9 joints, rest rotations unchanged, translated onto the mesh; 64 in all with 12 new finger bones (`Tip*`, `L Pinky1/2`) and `XRobe1-3` |
| Clips | 30 fps from `LICH.abc`: Standing `stand`, Walking `walk`, Running `run`, Fidget `fidget1`, Fidget2 `fidget2`, Taunt, Search, AttackMelee `Hattack2`, AttackMelee2 `Hattack1`, AttackRanged `Rattack1`, ResurrectSpell, Resurrect, Hit `wince1`, Hit2 `wince2`, Death `die1`, Dead |
| Events | `Rattack` 0.386 s; `RangeAttack` 0.447 s, glow and release on `palm_left` (MM9 socket `LHand1`; `RangeAttack` is on that node) |
| Textures | body 2K / 1K, skull set 2K / 1K, region masks, eye emission mask; class maps `textures/lich_material_classes.png`, `lich_head_material_classes.png` (not in the GLB) |
| Meshy credits | **30 of 40** (body Smart Topology 5, skull Smart Topology 5, body retexture 10, skull retexture 10; backup account), no retries |

## Route (`scripts/`)

0. **HD masters**: Codex through `claude_shared/codex_slot.sh`, `references_hd/` (five views) and `references_head/` (five skull
   views), from renders of the MM9 model and skin. Pose = MM9's bind pose (a stride, hands at the hips).
1. **Meshy**: Smart Topology 15k. Returned well separated (cloak, robe, pants, boots, belt, hands, head). `step1_clean.py` mirrors
   it (Codex drew the other foot forward), scales to MM9's height, removes a strap and two ribbons, labels parts.
2. **Rig** (`fit_lich.py`): the rig is fitted by part. Fingers come from geodesic level sets: a finger is the earliest component
   that never splits again.
3. **Mesh** (`prep_v2.py`): skull-only Meshy model replaces Meshy's old-man head, sleeve entries capped, hems tattered as geometry,
   per-part reduction, inner linings (hood, robe, boot flares: back faces are culled in game).
4. **UVs** (`uv_lich.py`, `claude_shared/uv_atlas.py`, new default-off option `group_factors`): hands 1.5x, linings 0.4x.
5. **Paint**: 4K retextures, the body from masters flipped to match the mirrored mesh (`references_hd/mirrored/`).
   `compose_lich.py`: pads from inside the charts at 4K (Meshy's gutters are pale), repairs its hair-thin pale cracks along triangle
   edges and long pale strokes, downsamples once; linings take the outer paint at 0.3; gentle grade (`textures.sh`).
6. **Tiers** (`tier_ramps.py`): Lich A keeps the paint (only the trim has a ramp); Power Lich recolours cloth, trim and belt, wraps,
   eyes and bone from the LICH1/LICH2 pair, texel by texel. Eyes emit, red / green, gentle pulse.
7. **Runtime** (`build_runtime.sh [--install]`): `rig_fix.py` -> export -> `clips_mm9.py` -> `hand_rest.py` -> prepare -> LODs -> shadow
   fix -> tiers -> emission -> `cloth_flat.py` -> floor -> **`mirror_glb.py`** -> winding -> install. `viewer_update.sh` writes the viewer.

Never re-run `uv_lich.py`: the paid paints belong to that exact layout. `rig_fix.py` moves no UVs and is safe.

## Decisions and deviations

- **Handedness.** `convert_abc_model.py` keeps LithTech's left-handed numbers (+Z forward, left = -X) as glTF numbers, so MM9 GLBs
  are mirror images of the game's actor: `L Hand` measured on the anatomical right in `source/mm9/lich.glb` (-0.249 m along the
  anatomical left axis). Inferred from the coordinate system and bone names, not from game footage. `mirror_glb.py` (the Imp's tool,
  copied) is the last build step: `L Hand` now +0.196 m on the anatomical left, `R Hand` -0.258 m, 0 mm from an exact mirror in all
  16 clips. Cast socket and forward foot match MM9's names. `review/sheet_mm9_vs_ours.png` compares with the mirrored MM9 source.
- **Hands**: kept the design, as the brief asks for bone fingers. No MPFB graft: Meshy's five long fingers rigged by connectivity,
  three joints each. MM9's two finger bones are kept, the third (`Tip*`) follows MM9's distal curl. Thumbs cut at their last joint (a
  20 cm hoop). MM9's left pinky has no proximal bone (`LHand1` sits there), so ours follows the ring finger's curl.
- **Head**: a real skull with a hanging jaw; MM9 has no jaw bone, so the jaw is rigid. Sockets deep-painted, not deepened.
- **Skin alpha**: `LICH1` and `LICH2` cut the sleeve hems by alpha (`Transparent 1`). Carried over as real torn geometry on sleeves
  and robe hem, so no alpha material or extra draw. The tears are one pattern for both tiers (MM9's differ per skin).
- **Glow**: neither skin has `DTX_FULLBRITE` or `LIGHTDEFS`, and both are all-opaque beyond the cut-outs, so MM9 gives no glow mask.
  The eye emission is a gain, from the painted embers.
- **Spell sockets**: `LHand1`, `RHand1` kept and moved onto our palms. MM9's `RangeAttack` socket is on `LHand1`.
  **Not carried**: Power Lich FX0/FX1 (`bluedots`, `greenyeldots`, `DoFX`): `unsupported` in the effect library (`needs_body_anchors`).
  The engine's element charge glow plays at the hand instead. `ResurrectFX`, Power Lich's `Resurrect 1` have no engine hook here; the
  clips are bound as `script_clips`.
- **Corpse**: on her back the sleeves' drape bones and rear robe hung through the floor. `cloth_flat.py` turns `XRobe1` 14 deg and the
  Box bones up to 42 deg (Death ramps it, Dead holds it); the corpse still rides 12 cm up on its sleeves (21 cm before).
- **Viewer**: tier GLBs carry `specularFactor 0` to match the game's specular off; without it three.js puts a glass sheen on the dark collar.

## Checks (final GLB)

| Gate | Result |
|---|---|
| `check_winding.py` | 0 inverted closed parts |
| `flat_shading_check.py` | 0.00 on both materials |
| `detached_parts_audit.py` | 0 detached (24 fps) |
| `texture_quality.py` body | atlas 56.8 %, fragments 0.0 %, stretch p90 1.28, spread 2.6 (linings 0.4x and hands 1.5x, by design) |
| `texture_quality.py` skull | atlas 63.6 %, spread 1.1, fragments 0.3 %, stretch p90 1.18 |
| `arm_hand_gate.py --exact` (48 fps) | finger stretch max 2.98 (Resurrect), 2.09 elsewhere. Hand depth: 0 in Standing, Search, Running, AttackRanged; Fidget and ResurrectSpell R 5.5 cm, 19 frames; Taunt R 5.3 cm 5 frames, L 3.8 cm 6 frames; AttackMelee L 2.3 cm, 1 frame |
| `jitter_gate.py` | arm joints 0 excess over MM9 in every clip; 6 fails (AttackMelee, Death, Resurrect, both sides): shoulder skin 3-4 mm/f2 from floor offsets, hands within MM9 |
| `sleeve_gate.py` (12 fps, front and below only) | see-through worst 10 of 14,400 px |
| `floor_audit.py` | stand +/-0.1, walk -2.5..+2.3, living -2.5, dead 0 units; flagged: dying sinks to -3.9 (tolerance 2.5) |
| `mm9_actor_models_build_every_binding` | 73 descriptors on 35 models, 0 failed |
| `run_creature_review.py check` | 16 clips, 2 tiers, 0 errors |

## Open points

- Not checked: an in-game run (viewer and headless binding only), bloom on the eyes in game, the charge glow at `palm_left` in game. Arm, jitter and sleeve gates ran before the last texture-only rebuilds; clips were unchanged by those.
- Fingertips rest in the thigh in Fidget, ResurrectSpell and Taunt (our fingers are longer than MM9's). `hand_rest.py` cleared Standing
  and Search; the Fidget push caps at 7 cm and the need stays 9.6 cm cast. It reads as a hand resting on the leg in the viewer.
- A few short pale strokes remain on the hood and cape (Meshy paint cracks, most removed).
- Mirror symmetry was not enforced: MM9's own bind is an asymmetric stride.
- Sheets: `review/sheet_mm9_vs_ours.png`, `review/sheet_tiers.png`, `review/sheet_closeups.png`. Gate outputs: `review/gates/`.
- User artistic acceptance: not recorded.


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_lich_reduce_claude/`** (ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `level_generation/creatures/mm9_lich_reduce_claude/before/`.
