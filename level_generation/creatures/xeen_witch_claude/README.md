# Xeen Witch (Wicked Witch / Witch / Head Witch), 2026-11-20

World of Xeen's witch (Clouds of Xeen image 76, Witch Tower), built with the
[humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) default route: Codex HD masters -> Meshy Smart Topology ->
source-frame rig with gates (`mm6_natm_claude/` scripts adapted) -> library clips + authored staff carry -> our UVs
(`claude_shared/uv_atlas.py`) + Meshy 4K paint -> region tiers -> LODs (ladder) -> install. Lane S sub-agent
(owner `xeen-s-witch-sub`). Technical completion; no user artistic review yet; **no in-game run** (the Xeen world has
no witch monster rows yet, so nothing places her; the parent/A2 own the bindings).

## Deliverables

| Item | Value |
|---|---|
| Body | `assets_source/worlds/xeen/models/xeen_witch.glb` (sha256 `bfbcb440...41f4`, = `export/xeen_witch.glb`); runtime copy `assets_dev/worlds/xeen/models/xeen_witch.glb` (cooked by `install_model.py`) |
| Staff attachment | `assets_source/worlds/xeen/models/xeen_witch_staff.glb` (sha256 `adb3741d...2534`), node `Staff` |
| Binding block | `integration/actors.yml` (ready to paste; placeholder descriptors `Xeen Wicked Witch`, `Xeen Witch`, `Xeen Head Witch`) |
| Triangles | body LOD0/1/2/3 9,644 / 4,815 / 2,403 / 1,202 (+ staff 368 / 184 / 74 / 74); Smart Topology 13.0k -> 9.6k after weighting (head and hands protected) |
| Skeleton | 52 `B_*` bones cloned from the humanoid set + forearm/upper-arm twist bones + `Staff` + sockets `Socket_RightPalm` (cast launch), `Socket_StaffCrystal` |
| Height / scale | 1.84 m to the horn tips (1.76 m head top); scale **99** units/m -> 182 units (brief: ~1.8 m; barbarian 1.9 m at 99) |
| Textures | one 2K body set (Meshy 4K paint downsampled once), 1K normal, 1K ORM (R baked AO, G roughness, B 0), 1K RGBA region mask; staff 1024x256 colour + crystal emission mask. No separate head set: the face is the gold hard-surface mask, given 2x texel density in the body atlas |
| Meshy credits | **20 of 60**: Smart Topology 5 (`smart_topology_v1`), auto-rig 5 (`rig_v1`, joints + base weights), body retexture 10 (`retexture_v1`, 4K on our UVs) |

## Tiers (one shared set, region R = the robe)

Xeen has one sprite and one palette for all three, so only A is native; B and C are design choices
(`scripts/tier_ramps.py`, `textures/witch_ramps.json`; albedo x1.35 the palette colour, range = robe texel luminance
2-98 %):

| Skin | Monster | Robe colours |
|---|---|---|
| `witch_a` | Wicked Witch | native blood red: (88,0,0) (108,0,0) (128,0,0) (148,0,0) (168,0,0) (212,68,68) |
| `witch_b` | Witch | deep violet-purple: the A shades turned to hue 282, saturation x0.85, value x0.95 ((62,13,84) .. (167,85,201)) |
| `witch_c` | Head Witch | black robe with a faint wine undertone (14,10,12) .. (78,64,72); the gold mask stays gold, so C reads as the leader |

The robe mask is the paint's red (hue within 22 deg of 0, saturation >= 0.45) on the body/robe shells: coat-robe,
tatters and the red right wrist wrap. Mask, skin, mane, black panel, brown cord, beads, gems and boots keep their paint.
Specular off (`openyamm_specular=0`, metallic 0) on the body; the staff has specular 0.4.

## Clips (30 fps keys; `work/clip_timing.json`)

Chosen at G1 from the local library (`review/g1_*.png`: candidates rendered on her body), before any animation work:

| Role | Source | Notes |
|---|---|---|
| Standing (3.0 s) | Mixamo Standard Idle | staff carried upright in the gloved left hand (`author_carry.py`, `carry.json`); the bare right palm raised beside the head like the sprite (right arm from the cast's stance, `right_stance.py`) |
| Walking (1.0 s) | Mixamo Walk | stride **1.90 m** per cycle (`stride.py`); floor pass |
| Running (0.73 s) | Mixamo Standard Run | `run_fit.py` (92 % pelvis, bob, 13 deg lean); stride **2.07 m** |
| Attack (1.67 s) | Mixamo Zombie Attack (1), first right-claw swipe (planted) | hand raised to chest height for the blow and pushed clear of the hips in the follow-through (`arm_push.py`); **impact 1.055 s** (the claw at 95 % of its 0.97 m forward reach) |
| Cast (2.2 s) | Mixamo Standing 1H Magic Attack 02 (planted) | wind-up beside the head, open right palm thrust forward; **release 0.719 s** from `Socket_RightPalm` (glow there) |
| Hit (0.5 s) | set Unarmed get-hit F1 | blends 0.12 / 0.20 s |
| Death (3.6 s) / Dead | Mixamo Standing React Death Backward | travel halved; staff kept in hand; `floor_fix.py --raise Death` on the export (fall dipped 2.7 cm) |
| Fidget (5.0 s) | Mixamo Laughing (first 5 s, planted) | a cackle |

Cast differs from Attack (path from beside the head vs a sideways swipe). `attack_ranged` uses Cast (her spell).

## Gates (final rig_v5 / export)

- G3 joints: Meshy axial joints, shoulders, hips, knees; wrists = narrowest ring of the hand shells past the wrist band
  (`fit_witch_joints.py`), ankles from the boot rings, elbows at Meshy's t on the arm-shell centreline; fingers by
  connectivity on the hand shells. Frame error 0. Hand-frame check: finger direction 18-66 deg off the carried source
  (the A-pose hands are splayed wide; the fitted finger chains are inside the fingers, `review/g3_hands_sheet.png`).
- G4 arm stretch p99 <= 1.9 everywhere except the attack's raised swipe arm (p99 2.4-2.8, max 3.6 at 1.0 s) and the
  cast's fully extended arm (2.4).
- G5 hand stretch: left (staff fist, `grip_solve.py` SIDE=L) 2.42x, right <= 3.75x (fingers kept at 25 % of the source
  curl, `fingers_relax.py`); limit ~4.5x.
- Wrist swing <= 56 deg in every clip (`gate_wrist.py`; `wrist_ease.py` eased the cast/attack/death peaks), forearm roll
  moved to the hand (`forearm_hinge.py`) and spread by the twist bones.
- G6 contacts (`g6_contacts.py`, closed shells inside test, robe skirt as a sheet): Standing, Walking, Running, Hit 0;
  Cast 0.2 cm, Fidget 0.5 cm (left elbow fold), Attack 0.1 cm; Death: the corpse's forearm clear, staff fork 0.7 cm at
  0.15 s. Session 2 (2026-11-20) put `elbow_clear.py` into the chain: after `arm_push.py` it moves the wrist out
  along the outward normal where the forearm or the staff enters the closed skin (measured on the previous build's
  final body, `work/measure_ref.blend`), eased over +-8 frames, joints rebuilt as pure swings; a second pass after
  `clip_timing.py` clears the staff from the boot in the death's blend-in. Before: the left inner elbow 1.4-4.1 cm into
  the waist in Running, Cast and Fidget, the right forearm 1.8 cm in Fidget, the lying forearm 6.4 cm in the torso and
  the fork 4 cm in the boot. Wrist swing <= 56 deg and jerk unchanged from before the pass.
- Feet (`sole_probe.py`): Standing/Attack/Cast/Fidget soles at 0; Walking -1.3..+0.9 cm; floor audit (world units, scale
  99): standing 0, walking -1.32..+0.86, corpse +0.02, no problems.
- Texture quality (`texture_quality.py`): atlas **74.0 %**, density spread **1.1**, fragments **2.9 %**, stretch p90
  **1.16** (uv_atlas defaults: PartUV charts, seam pass, sparrow; no fallback; head 2x).
- LODs: LOD1 `build_actor_lods.py`; LOD2/3 the playbook ladder (project copy in `lodrepair/`), step **r25_12 accepted**:
  LOD2 outline 5.5 % / colour 13.1, LOD3 8.3 % / 12.5; `verify_far_only.py` OK; shadow LODs tucked.
- Winding: 0 inverted closed parts (body and staff). Viewer check: 27/27 tier/clip switches, no console errors.

## Review

- Viewer: `review/viewer/` (`python3 tools/run_creature_review.py --project level_generation/creatures/xeen_witch_claude
  --port <port> check`; tiers baked by `scripts/viewer_tiers.py`, crystal emission applied).
- Textured renders from the party's eye height: `review/r_tiers.png` (A/B/C front, A three-quarter/side),
  `review/r_blow.png` (attack and cast around the blow), `review/r_front_keys.png`, `review/r_attack2_close.png`
  (close-ups: mask, staff hand, right claw). Blender's glTF import plays the clips at 24 fps: render frame f = f/24 s.

## Replay

```sh
TOK=<lease>; P=level_generation/creatures/xeen_witch_claude
# one-off: examine_parts.py (HEIGHT=1.84, st_v1_parts), export_clean.py -> requests/rig_v1.json, meshy_joints.py,
#          source_rest.py, proportions.py source
TOK=$TOK $P/scripts/rebuild.sh        # STAGE=rig | anim | all
# (anim needs work/measure_ref.blend, the final body for elbow_clear.py: a copy of a previous build's work/rig_v5.blend)
# textures (once, layout locked): uv_witch.py -> requests/retexture_v1.json -> uv_garment.py, bake_ao_witch.py,
#          make_staff.py, compose_witch.py
cp $P/work/uv_v1.blend $P/work/rig_v6.blend   # first time only (UV master; clips are synced into it)
TOK=$TOK $P/scripts/build_runtime.sh  # grade, ramps, gutter fill, sync, export, LODs, tiers, staff split, emission
# far LODs: lodrepair/scripts/repair.py --source export/xeen_witch.glb xeen_witch (r25_12) -> export/xeen_witch.glb,
# floor_fix.py --raise Death, check_winding.py, tools/install_model.py export/<name>.glb --world xeen (body, staff)
python3 $P/scripts/viewer_tiers.py && python3 $P/scripts/update_viewer_manifest.py
```

## Known limits

- Seen in game in XD-21 (Xeen Witch A/B/C, Head Witch), bound in `assets_dev/worlds/xeen/models/actors.yml`.
- The attack's raised arm stretches the shoulder to p99 2.8 for a few frames of the 7 m/s swipe.
- The mane is rigid on the head blending to the chest by height (no secondary motion); the robe is skinned, not
  simulated (the legs show through the front slit as designed).
- The staff thumb stands up along the shaft rather than wrapping it (gauntleted fist; G5 clearances 1.6-2.1 cm).
- B and C colours are design choices (one native palette).
