# Xeen Sorceress (Sorceress / Enchantress / Grand Sorceress, Apprentice, Head Sorceress, Morgana), lane S, 2026-11-20

Clouds of Xeen image 31 (`reference/mm4_5_world_of_xeen/unpacked/sprites/xeen/031.mon`, `031.att`): a strong
brown-skinned woman, purple-black curly mane, gold circlet with a green gem, green eyes, white halter top with white
shoulder caps, jewelled silver girdle with a big green gem, long white front panel, black flared elbow gloves, black
thigh-high boots; green spell swirls round her hands. Built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md)
default route, the witch's way (`../xeen_witch_claude/`): Codex HD masters -> Meshy Smart Topology -> source-frame rig
with gates -> library clips -> our UVs (`claude_shared/uv_atlas.py`) + one Meshy 4K paint giving a body set AND a 1K
head set -> region tiers -> LODs (ladder) -> install -> bind. Lane S sub-agent; technical completion, no user artistic
review yet.

Darkside image 50 (Enchantress / Sorceress / Morgana in Dark Side: blue skin, red spiky hair, red claw-like shoulder
blades, armoured legs) is a different design, not covered by this model (see the lane report's DECIDE).

## Deliverables

| Item | Value |
|---|---|
| Body | `assets_source/worlds/xeen/models/xeen_sorc.glb` (= `export/xeen_sorc.glb`, sha256 `3360eefc...`); runtime copy `assets_dev/worlds/xeen/models/xeen_sorc.glb` (cooked by `install_model.py`) |
| Binding | `integration/actors.yml`, merged into `assets_dev/worlds/xeen/models/actors.yml` with `../xeen_tiers_claude/bind.py`; `--headless-validate-actor-models`: 275 descriptors, 0 refused |
| Triangles | LOD0/1/2/3 **9,949 / 4,973 / 2,480 / 1,234** (+ shadow LODs); Smart Topology 14.8k -> 9.9k after weighting (head and hands protected) |
| Skeleton | 52 `B_*` bones cloned from the humanoid set + forearm/upper-arm twist bones + `B_PanelFront` / `B_PanelBack` (cloth panels) + sockets `Socket_RightPalm`, `Socket_LeftPalm` (3 cm off each palm) |
| Height / scale | 1.75 m to the top of the mane; scale **99** units/m -> 173 units (the witch: 182) |
| Textures | body 1K + head 1K sets (colour, normal, ORM: R baked AO, G roughness, B 0), merged at runtime into 2080x1024 atlases by `merge_head_material.py` (one draw); 1K RGBA region mask (R = white cloth) |
| Meshy credits | **20 of 30**: Smart Topology 5 (`smart_topology_v1`), auto-rig 5 (`rig_v1`, joints + base weights), retexture 10 (`retexture_v1`, 4K on our UVs, body and head in one paint) |

## Head set from one paint

A separate head retexture (10 more credits and a Codex head turnaround) was avoided: `scripts/uv_sorc.py` splits the
welded master by face into HEAD (skin with B_Head weight > 0.5 plus eyes, lips, circlet and earrings: 3,020 faces) and
BODY (6,929), unwraps each with the uv_atlas defaults (PartUV, seam pass, sparrow, the other part as occluder) into its
own square and places them side by side in the lower half of one upload square (body u 0..0.5, head u 0.5..1). Meshy
paints that at 4K, so each set gets a 2048 quadrant, cut out and downsampled once to 1K (`compose_sorc.py`). The export
rescales each primitive's UVs to its own square (materials `Sorc_A`, `SorcHead_A`). The top half of the paint is unused.

## Tiers (one shared set, region R = the white cloth)

Xeen has one sprite (neutral palette whites 140..252) for all of them, so only A is native; B, C and M are design
choices (`scripts/tier_ramps_sorc.py`, `textures/sorc_ramps.json`). A is the ramp fitted to the paint (mean error 1.2
of 255); the others keep the paint's shading (stop = mid colour x (A stop luminance / region mean) ^ contrast).

| Skin | Rows | Cloth |
|---|---|---|
| `sorc_a` | Sorceress A, Apprentice Sorceress D (scale_reference A), Head Sorceress | native white |
| `sorc_b` | Enchantress B | pale violet #b8a0dc |
| `sorc_c` | Grand Sorceress C | deep emerald #106e40 (contrast 1.1) |
| `sorc_m` | Morgana (D-32) | deep crimson #8c0e1e, contrast 1.9 so folds and edges go near-black |

The mask (`compose_sorc.py`): light texels (saturation < 0.22, value > 0.42) of the panels (garments 3, 7), the
shoulder caps (4), the halter's strap ties (P44/P51, garment 5) and, on the skin shell, the halter between 1.15 and
1.52 m (the skin under the girdle carries a silver projection of it) or bright white elsewhere (the skin under the
panels); two texels of pale edge mix more on the skin shell so B/C/M show no white outline. Skin, mane, gloves, boots,
girdle, gems, choker and the head set keep their paint. D-32 asked for a separate black trim if the paint has hems
that mask cleanly: it has none (a trim channel found 0.01 % of the islands), so Morgana's black trim is the ramp's
near-black dark stops. Specular off (`openyamm_specular=0`, metallic 0) on both materials. Material classes:
`textures/sorc_material_classes.png`, `sorc_head_material_classes.png` (`compose_sorc.py`).

## Clips (30 fps keys; `work/clip_timing.json`)

Chosen at G1 from the local library (`review/g1_front_a.png`, `g1_front_b.png`, `g1_q.png`: candidates on her body):

| Role | Source | Notes |
|---|---|---|
| Standing (3.0 s) | Mixamo Standard Idle | arms moved clear of her wide hips (`elbow_clear.py`, wrists up to 11 cm out); the Pro Magic Pack idle is a crouched stance |
| Walking (1.0 s) | Mixamo Walk | stride **1.70 m** (`stride.py`) |
| Running (0.73 s) | Mixamo Standard Run | `run_fit.py` (92 % pelvis, bob, 13 deg lean); stride **2.05 m** |
| Attack (1.67 s) | Mixamo Zombie Attack (1), first right open-hand swipe (planted) | a slap; `arm_push.py` (the witch's offsets) keeps the follow-through clear of the hips; **impact 1.055 s** (hand at 95 % of its 0.91 m forward reach) |
| Cast (2.7 s) | Mixamo Standing 2H Magic Attack 01 (planted) | both palms raised overhead (the native attack frame), then thrust forward together; **release 1.23 s** from `Socket_RightPalm`, glow on both palms; eased from/to Standing over 0.30/0.35 s |
| Hit (0.5 s) | set Unarmed get-hit F1 | blends 0.12 / 0.20 s |
| Death (3.6 s) / Dead | Mixamo Standing React Death Backward | travel halved; `floor_fix.py --raise Death` on the export (the fall dipped 6.9 cm at 18 keys) |
| Fidget (5.0 s) | Mixamo Standing Idle 03 "playing with magic" (planted, first 5 s) | |

`attack_ranged` uses Cast. Cast differs from Attack (two palms raised and thrust vs a sideways one-hand swipe).

## Cloth panels

Skinned as the witch's apron (pelvis -> even thigh mixture), the forward thigh came 16 cm through the front panel in
Walking and 20 cm in Running, the backward thigh 13 cm through the back panel (`scripts/panel_poke.py`). `panel_bones.py`
adds `B_PanelFront` / `B_PanelBack` (children of the pelvis, at each panel's top) and bakes their swing per frame: the
front panel follows the more flexed thigh (x1.05), the back panel the more extended one; the panel vertices ramp from
the pelvis onto the panel bone 5-13 cm below the girdle (`weights_fix.py`). After: Walking 0.6 / 0.9 cm, Running 0 /
2.1 cm, Hit 0.9 cm; a constant 1.7 cm at the panel top under the girdle in every clip. Running swings the front panel up
to 74 deg with the knee (cloth flying); Standing tilts the back panel 11 deg against the idle's pelvis tilt so it hangs
plumb.

## Gates (final `work/rig_v5.blend` / export)

- G3 joints: Meshy axial joints, clavicles, shoulders, hips, knees; elbows at Meshy's t centred on the arm ring
  centreline; wrists = narrowest ring of the skin shell within 7 cm before / 4 cm past Meshy's wrist (16.7 / 17.3 cm);
  ankles = narrowest boot ring (`fit_sorc_joints.py`). Fingers by connectivity on the one skin shell (`fit_fingers.py`
  keeps the wrist-connected piece: the 0.3 m ball caught the outer thigh). Frame error 0; finger direction 18-43 deg
  off the carried source (splayed A-pose hands), chains inside the fingers (`review/g3_sheet.png`, `g3_hands_sheet.png`).
- Wrist swing <= 56 deg in every clip (`gate_wrist.py`; `wrist_ease.py` eased the cast and attack peaks).
- G5 hand stretch max 2.32x (Death L), <= 2.24x elsewhere (limit ~4.5x); fingers kept at 25 % of the source curl
  (`fingers_relax.py`, both hands open).
- G6 arms (`g6_contacts.py`, closed skin): <= 0.6 cm in every clip (before `elbow_clear.py`: hands 13 cm into the thigh
  in Walking, 2-3 cm into the hips in Standing and every clip that starts from it). Panels: above.
- Feet (`sole_probe.py`): Standing/Attack/Cast/Fidget soles at 0; Walking -0.8..+1.0 cm; Hit hops 1.8 cm for 2 frames.
  Installed floor audit (scale 99): stand 0, walk -0.8..+1.0, corpse +0.07 units, ok for all bound descriptors
  (`floor_audit.py --match 'Xeen Sorceress D'` stops on a missing Xeen sprite scale for `scale_reference`; D shares A's
  clips and skin).
- Jerk (`jerk_probe.py`): no step far above the source clips' own.
- Texture quality (`texture_quality.py`, pre-merge export): body atlas **74.7 %**, spread **1.16**, fragments
  **0.3 %**, stretch p90 **1.21**; head atlas **78.2 %**, spread 1.13, fragments 0.4 %, stretch p90 1.20.
- LODs: LOD1 `build_actor_lods.py`; LOD2/3 the playbook ladder (`lodrepair/`, Blender through the lane wrapper,
  `lod_repair_claude/venv`), **r25_12 accepted** (LOD2 outline 2.7 % / colour 8.8, LOD3 5.3 % / 12.0);
  `verify_far_only.py` OK; shadow LODs tucked (`shrink_shadow_lods.py`).
- Winding: 0 inverted closed parts. Viewer check: 36/36 tier/clip switches, no console errors.

## Review

- Viewer: `review/viewer/` (serve the repo with `claude_shared/serve_review.py 8912`, then
  `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_sorc_claude check`); tiers baked by
  `scripts/viewer_tiers.py`. Shots: `review/shots/`, `review/shots_sheet_v1.png`, close-ups `review/shots_close_v1.png`.
- Tier renders: `review/tiers_v3.png` (A/B/C/M from four sides), `review/crop_tiers.png`.
- In game (XD-21, `build-xeen`, tours `review/tour_xd21.yml`, `tour_xd21_v2.yml`): `review/ingame_v1/` (A/B/C/M
  spawned friendly side by side, dying, Head Sorceress + Apprentice), `review/ingame_v2/` (hostile Sorceress and
  Morgana: run, palm glow and release of the cast), sheets `review/ingame_sheet_v1.png`, `ingame_sheet_v2.png`,
  `ingame_cast_crop.png`. Killed actors leave loot bags in XD-21 and their corpses are gone 3.5 s later, so no corpse
  capture in game (the viewer shows Dead).

## Replay

```sh
TOK=<lease>; P=level_generation/creatures/xeen_sorc_claude
# one-off: examine_parts.py (HEIGHT=1.75, st_v1), export_clean.py -> requests/rig_v1.json, meshy_joints.py,
#          source_rest.py (Unarmed.glb)
TOK=$TOK STAGE=rig $P/scripts/rebuild.sh
TOK=$TOK STAGE=anim CLEAR="Standing:L:forearm:loop Standing:R:forearm:loop Walking:L:forearm:loop Walking:R:forearm:loop \
  Attack:L:forearm Attack:R:forearm Cast:L:forearm Cast:R:forearm Hit:L:forearm Hit:R:forearm Death:L:forearm \
  Death:R:forearm Fidget:L:forearm Fidget:R:forearm" $P/scripts/rebuild.sh   # needs work/measure_ref.blend (a rig_v5 copy)
TOK=$TOK $P/scripts/gates.sh; scripts/step.sh panel_poke.py $P/work/rig_v5.blend <clips>
# textures (once, layout locked): uv_sorc.py -> requests/retexture_v1.json; dump_uv_sets.py, bake_ao_sorc.py,
#          compose_sorc.py; cp work/uv_v1.blend work/rig_v6.blend (first time only; clips are synced into it)
TOK=$TOK $P/scripts/build_runtime.sh   # grade, ramps, gutter fill, sync, export, LODs, skins, head merge, winding
LOD_REPAIR_PYTHON=<lod_repair_claude/venv/bin/python> lodrepair/scripts/repair.py --source ../export/xeen_sorc.glb xeen_sorc
# -> lodrepair/export/xeen_sorc.glb -> export/xeen_sorc.glb; floor_fix.py --raise Death; check_winding.py;
#    tools/install_model.py export/xeen_sorc.glb --world xeen; python3 scripts/viewer_tiers.py; update_viewer_manifest.py
```

## Known limits

- B, C and M colours are design choices (one native sprite and palette). Morgana's trim is ramp darkening, not a
  separate hem colour (the paint has no hems to mask).
- The mane is rigid on the head blending to the chest by height (no secondary motion); the panels are rigid plates on
  their swing bones (no cloth bend); in Running the front panel flips up to 74 deg with the knee.
- The eyes are painted bright green, not emissive (an emission mask in the merged atlas would not match the far LODs'
  own re-baked UVs).
- Hit lifts both feet 1.8 cm for two frames (source clip).
