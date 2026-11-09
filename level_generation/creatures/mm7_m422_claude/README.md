# MM7 Vampire (m422) — Claude 3D model (batch F, 2026-10-20)

Minion Vampire / Vampire / Elder Vampire (monsters 415/416/417, descriptors `Vampire A/B/C`, sprite palettes 99/104/105),
unarmed (claw reach). Built with the batch-B robed-caster chain of [the Mage](../mm7_m274_claude/README.md) (settings in
`creature.json`): coat skirt chains + a simulated cape sheet. **Not installed** (batch rule,
[BATCH_F.md](../mm7_batches/BATCH_F.md)). Status: technically complete, agent-reviewed in the viewer; user artistic
acceptance pending. [Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m422_claude/review/viewer/).

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m422.glb` | runtime body: LODs 10,329 / 5,163 / 1,844 / 606 triangles, 126 bones, tiers `m422_a/b/c`, head set merged (sha256 `a9b85be7…`) |
| `mm7_m422_lod0.glb`, `mm7_m422.blend` | portable LOD0, editable master (textures packed) |
| [`../actors_m422_binding.yml`](actors_m422_binding.yml) | proposed `actors.yml` entries: scale 119.3 (201 px / 1.685 m Standing), run → Walking, stride 1.415 m, impact 0.975 s, no cast |

Install later (not run):

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m422_claude/export/mm7_m422.glb --world mm7
```

then add `actors_m422_binding.yml` to `assets_dev/worlds/mm7/models/actors.yml` and a tier/height regression.

## HD masters (and the refusals)

- `references_hd/`: 00 = `m422_three_quarter_r2b`, 01 = `m422_front_r3`, 02 = `m422_back_r1b`, 03 = `m422_left_v1b`,
  04 = `m422_right_r1b` (hashes in `creature_3d_progress.json`). `references_head/`: all four views in one run.
- The image service refused several requests at the **output** stage (`moderation_blocked`, category `other`):
  the corrective primary (`v3`, `r1`), the first front/back/right views and two more front attempts (`r1`, `r2`;
  `r3b`). The batch coordinator relayed a user decision (2026-10-20) overriding BATCH_F's no-rewording rule: reword
  to a clearly benign depiction (neutral, dignified, calm, no gore or bite emphasis, fangs only subtle), at most three
  variants per request, then mark the model blocked. Every prompt and refusal is in `references_hd/generation_runs.json`
  (note `note_refusal_override_20261020`) and the briefs `CODEX_BRIEF_*`. The reworded briefs asked for a "stylised
  game-art" court nobleman with an original face; all five views and the head turnaround were obtained (the front on
  the third reworded variant), so the restored-art fallback the coordinator also authorised was **not** used.
- **Deviation:** the HD masters have a closed, calm mouth (the native's open mouth with small fangs was dropped by the
  benign wording); the head turnaround shows the fang tips just over the lower lip, so the head texture has subtle
  fangs. The primary's camera is ~30° (not 40–45°) and the masters have faint coloured edge halos.

## Model

- **Geometry**: Smart Topology (15k, `pose_mode` empty) of the primary: coat + cape + collar as one shell, head, legs,
  hair, hands, eyes, belt buckle, neck ornament, 13 clasps. `clean_parts.py`: two thin sticks that hung from the
  mouth and the ornament down to the chest removed (sliver/long-edge triangles), a stray triangle deleted, the cape's
  open inner face filled (42-vertex hole, refined and relaxed), the shell split by vertex into coat top + sleeves,
  skirt (below 0.95 m), cape (the component behind the body below the shoulders) and the stand-up collar.
- **Rig**: source-frame rig (Meshy auto-rig joints + arm rings, `joints_fix.py`). `legs_fix.py`: Meshy put both knees
  on the coat front, 7.7–8.7 cm in front of the leg mesh; knees and ankles moved onto the leg cross-section centres
  (the calf had swung about the knee's front and swept through the back of the coat in the walk).
- **Weights**: `weights_robe.py` (sleeves split from the torso at 1.15 m, collar without arm weight, rigid buckle and
  upper clasps, skirt 12 chains × 4 from the waist (0.93 m) to the hem (0.30 m), skirt clasps follow the chains);
  `shrink_legs.py` thins the trousers hidden in the skirt above 0.45 m to 85 % (they touched the skirt at rest);
  `sheet_rig.py`: the cape 5 columns × 4 from `B_Spine2`. Hands rigid (open claws, no finger weights).
- **Cloth** (`robe_sim.py`): coat with leg capsules (calf 8 cm), neighbour-midpoint collisions and a hard collision
  pass after the temporal smoothing (`MID_COLLIDE`), cape with a final neighbour-spacing pass (`NB_FINAL`); both
  `DROP_FLAT` for the corpse.

## Clips (30 fps; G1 sheets in `review/g1_*`)

| Clip | Source |
|---|---|
| Standing 2.0 s / Walking 0.8 s | set Relax Idle / Relax Walk Forward (arms abducted 6°); Walking and Hit get a ground pass (the lower ankle's float taken off the pelvis) |
| Attack 1.567 s | Mixamo "Standing Melee Attack Downward" (user review 1, see below): claw raised over the head, raked down across the body, faced front, authored lunge step (`attack_legs.py`); impact 0.975 s |
| Hit 0.5 s | set Unarmed Get Hit F1, planted |
| Death 4.6 s / Dead | Mixamo "Dying Backwards": staggers, sits, falls onto the back with a leg kick (native da–dc), travel halved, floor pass. "Standing React Death Backward" strode wide and the knee came through the closed coat front; "Dying" lay face down; the set's Death1 left the coat behind the bent knees |
| Fidget 2.0 s | authored (`author_fidget.py FIDGET=cape`): the right forearm rises across the lower face and lowers again (native fa–fd), smoothed |

## Gates (final rig `work/rig_v5.blend`; `review/gates_v5.json`, `review/cloth_v5.json`, `work/gates_run.log`)

- G4 arm stretch p99 ≤ 1.82 (max 3.28 on a few edges: Fidget right armpit); Death 2.00/1.75. Wrist swing ≤ 56.6°.
  G5 hand stretch ≤ 1.05 (rigid hands). G6 hand inside body: 0 in every clip.
- Cloth (`cloth_gates.py`): skirt p99 ≤ 1.35, cape p99 ≤ 1.24 upright; skirt poke 0 except Walking (4 vertices,
  5.2 cm at one frame) and Hit (1 vertex, 0.02 cm); cape poke ≤ 1. Death (lying): skirt p99 2.22, cape p99 6.1 with a
  66 cm opening at 2.2 s (the cape crumples under the body while the legs kick up; brief).
- Soles (`sole_probe.py`): standing clips within −0.5…+1.1 cm; Walking one half-frame with both feet > 1 cm.
- Jerk (`jerk_probe.py`, 1/48 s): Standing/Walking/Fidget smooth (≤ 17° hand step); Attack hand 50°/step at the
  release, the source clip's own snap (source upper arm 61°/step); Hit and Death similar to the source.
- Viewer: `check_viewer.mjs` and `run_creature_review.py check`: 3 tiers × 7 clips, 21 switches, no console errors;
  shots in `review/shots/`, playback (normal and half speed) in `review/playback/`. Winding: 0 inverted parts.
  **Not checked in game** (optional; the batch ran in parallel).

## Textures (`scripts/compose_m422.py`)

Body 1K + head 1K (Meshy retexture of the body with `enable_original_uv: false`, UVs transferred back; head-only
retexture on our HeadUV). UV layouts carried to the rebuilt mesh by `carry_uv.py` (the stick removal came after the
uploads). Regions from `../mm7_m422/variants.json`, ramps from the indexed bitmaps per palette: R coat (indices
137–169: green / royal blue / red), G cape + collar (202–239: green / burgundy / black), B hair (85–101, head set).
Tier C's cape is pure black in palette 105: a neutral near-black ramp (linear 0.004–0.035, rendered median about
sRGB 34) keeps the folds visible (deviation).

**Tier colour review (2026-10-20).** The guide's 1.35× ramp gain rendered the coats and tier A's cape flat bright
green/red and the hair light brown/mauve. `scripts/tier_match.py` (after the Necromancer's) compares viewer shots
with each tier's native pixels (median sRGB luminance and chroma, same pixels in every tier); the per-tier, per-region
gains in `textures/m422_ramp_gains.json` were fitted in three passes (`scripts/tier_iter.sh`): coat 1.14 / 0.84 /
0.69, cape 1.05 / 1.10 / –, hair 0.79 / 0.81 / 0.63 (A / B / C). Rendered vs native median luminance now: coat
0.253/0.252, 0.129/0.129, 0.110/0.101; cape 0.281/0.271, 0.123/0.122; hair 0.192/0.189, 0.212/0.208, 0.153/0.146
(`review/tier_match.json`). The hair keeps a per-tier colour because the palettes do differ there: indices 85–101 are
dark brown in 99 (median sRGB 65/45/31), neutral grey in 104 (53/53/53) and dark mauve-grey in 105 (45/35/38); it now
renders as dark as the native in every tier. The gold was also graded down (rendered median sRGB 225/185/72 against the
native 134/92/44, now 166/119/45). Side by side at the same scale: `review/tiers_vs_native.png`. Tier C's red coat
keeps a little less chroma than the native (0.30 vs 0.45). Skin repainted pale (native face pixels ×1.1). Material classes in `textures/m422_material_classes.png`
and `m422_head_material_classes.png`; ORM red = per-class specular mask.

Meshy: **40 credits** — Smart Topology 5, auto-rig 5, body retexture 10 (v1, superseded) + 10 (v2 on the final mesh), head retexture 10.

## Known limits / for review

- Mouth closed in the masters (refusal rewording); fangs only as painted tips.
- The A tier cape is the palette's mid green (native palette 99 draws it at median sRGB 14/91/14), lighter than the
  restored identity sheet suggests; tier C's coat red is slightly less saturated than the native.
- Death: the cape crumples under the body for ~0.3 s while the legs kick; the trousers show from the hip while sitting.
- Fidget: the forearm covers the eyes/nose with the elbow raised in front (native: level across the mouth, elbow out).
- Walk: the calf touches the back hem at one frame (≤ 5 cm, under the cape).

## Reproduce

`TOK=<lease> scripts/rebuild_and_gates.sh all` (chain `scripts/rebuild.sh` + cloth, sole and jerk gates); textures:
`export_uploads.py`, `requests/*.json`, `transfer_uv.py` (on the upload master), `carry_uv.py`, `uv_raster.py` ×2,
`bake_ao_natm.py`, `compose_m422.py` (tier gains: `tier_iter.sh`, `tier_match.py`, `tier_compare_sheet.py`); `TOK=<lease> scripts/build_runtime.sh`; `viewer_tiers.py`,
`update_viewer_manifest.py`. Probes used in review: `probe_*.py`, `dump_*.py`, `hide_shots.py`, `worst_edges.py`,
`long_edges.py`.

## Revision 2026-10-20 (user review 1)

Rebuilt and exported again; still **not installed**. Gate logs: `work/gates_run.log`, `review/gates_v5.json`,
`review/cloth_v5.json`, `review/armpit_v5.json`.

1. **Attack: melee hand attack chosen by G1.** The native attack (aa–ah) raises the right claw and lunges/rakes
   forward. I retargeted four library candidates onto this body, planted, and rendered them front/side/three-quarter
   (`review/g1_attack_candidates.png`, last row the old clip): Mixamo "Cross Punch" (a boxer's guard and jab, not
   aristocratic), "Standing Melee Attack Downward" (claw raised over the head, raked down and forward across the
   body), "Zombie Attack" (a two-handed grab that bends double over 4.6 s) and "Standing Melee Attack Backhand" (a wide
   swing that turns the back on the target). **Picked the downward claw rake**: it is the native's raise-and-rake,
   reads as a predatory but upright noble strike, and keeps the feet planted. Cut at 1.47 s of the source, eased from/
   to Standing frame 0 (lead 0.1 s), feet planted, faced front. Blow measured at the claw's peak speed: **0.917 s**
   (`actors_m422_binding.yml` updated; the native has no spells or missile, so the `cast` mapping was removed).
   `arm_cap.py` softly limits the arm's elevation above 80° (×0.4 beyond, wrist peak 1.76 → 1.57 m) and clamps the
   clavicle to ≤ 8° above Standing (also used on the fidget). The cape follows the chest frame when he bows into the
   rake (`TILT_CLIPS=Death,Attack`, 10–40°): the plumb cape had folded onto itself (36 inverted faces → ≤ 5).
2. **Light patches through the walking coat.** Cause: the coat shell carries a hidden *inner layer* in front (faces
   turned toward the body behind the outer surface, painted flat by Meshy). With the chain skirt bending, those faces
   came through the outer coat, and the double-sided viewer drew their flat paint (the engine would cull them into
   holes). Measured with `visible_backfaces.py`: 50–125 cm² of visible back faces per walk frame. Fixed at the source:
   `clean_parts.py` deletes the hidden inner coat faces in front (374 faces whose radial ray meets the outer coat
   within 5 cm); the remaining inner vertices copy the outer surface's weights (`weights_robe.py inner_layer_reach`);
   the skirt near the button strip takes the centre chain (`front_seam_deg`); the robe sim got bending stiffness across
   and along the chains plus a 15° bend limit after the collisions (`BEND_SMOOTH`, `BEND_MAX`: the knee had tented the
   front chains 35–50°, now ≤ 17°). Also removed: a fan of 36 internal stick triangles in the chest (holes it left are
   filled). Result: 7–15 cm² of visible back faces per walk frame (front and three-quarter), the light patches are gone
   in all tiers (`review/review1_walk_coat.png`, `review/review1_tiers_closeups.png`). Texture layout carried to the
   new mesh by island (`carry_uv.py`), no new retexture.
3. **Coat stretch under the raised arm.** Meshy had left upper-arm weight on the chest beside the strip and on the side
   panel. `weights_robe.py armpit_fade`: on the coat top the arm share fades out medially (none within |x| 0.06 m, full
   at 0.12 m) and goes to the chest bones; the torso below the armpit split loses its arm weight over 15 cm into the
   chest bones (`split_ramp`, `split_to_chest`); the armpit band is protected from reduction
   (`reduce_protect_box`). Sleeves stay arm-only below the split; the forearm twist ramp and upper-arm counter-twist were
   already in (`twist_bones.py`). Armpit/side/chest edge stretch (`armpit_stretch.py`, right side, p99 / max):
   Attack 3.56 / 4.70 → **2.46 / 3.53** at its highest-arm frame, Fidget 2.91 / 3.89 → 2.34 / 3.19, Death 3.37 / 4.11
   (left) → 2.41 / 3.11; Standing/Walking ≤ 1.23 / 1.42; Hit 2.12 / 2.89. Arm-gate p99 ≤ 2.39 on every clip (target ≲ 2
   is met except the attack's wind-up 2.39 and Death 2.38). Close-ups of the raised-arm frame, front, back and side:
   `review/review1_raised_arm_clay.png`; textured: `review/review1_tiers_closeups.png` (columns 4–5).
4. **Buttons and belt.** The clasps (rigid on spine bones / per-cord chain mixes) and the buckle (rigid on B_Spine) now
   each copy ONE weight set: that of the coat vertex under the piece (`accessory_pieces`), so they ride the placket
   and the skirt chains rigidly. Distance change between each piece and its seat on the coat (`accessory_gap.py`):
   Standing/Fidget 0.8 mm, Walking 6.1 mm, Hit 4.5 mm, Attack 8.0 mm (bow), Death 6.4 mm. Close-ups:
   `review/review1_placket_clay.png`. **Belt ends:** the ragged edges are geometry — Smart Topology modelled the
   native's winglike side scrolls as thin folded flaps of the coat shell standing above both belt ends (visible at rest,
   not a texture seam and not an intersection; the belt band is part of the coat shell and moves with it). A Laplacian
   relax of that area did not remove them and was dropped; fixing them needs the belt ends remodelled (open item).

Gates after the revision: G5 hand stretch ≤ 1.05, hands in body 0 on every clip; wrist swing ≤ 57°; skirt poke 0
(Standing, Attack, Hit, Fidget), Walking 15 vertices at the back vent (inward ray ≤ 10 cm, under the cape); cape poke
≤ 7; soles within −0.5…+1.1 cm (Walking one half-frame both feet > 1 cm); jerk: Attack hand 35°/step at the blow
(source clip), others unchanged. Viewer: 21 switches, no console errors; winding 0 inverted. Meshy: no new credits
(30 total).

Remaining for review: the belt-end flaps; the attack's armpit p99 2.46 at the wind-up peak. (The UV carry-over specks
were removed by the body retexture v2, below.)

## Attack feet (user review 2026-10-20)

User: "please use legs during his attack — he is completely inert from the bottom down". Cause: the attack was retargeted
`:plant` (legs held at Standing frame 0); the source (Mixamo "Standing Melee Attack Downward", the same clip as the
Devil's) only pivots its feet in a wide fencing stance. `scripts/attack_legs.py` (copied from
`mm7_m178_claude/scripts/attack_legs.py`; numbers in `scripts/attack_legs.json`) authors the lower body on the timed
clip, after `flatten_feet.py` and before the coat/cape simulation:
- wind-up: the pelvis draws back 4 cm and sinks 1.5 cm as the claw rises, hips yaw −8°; rake: the pelvis drives 10 cm
  forward and sinks 8 cm, hips +10°, the chest follows 50 ms later; lean −3° then +2° only (the source already bends
  forward into the rake);
- feet: the left foot steps 28 cm forward with an 8 cm sine lift (frames 16–26, landing just before the blow) and steps
  back in the recovery (36–45); the right heel peels 14° about the ball joint at floor level with the toes counter-
  rotated flat; the planted foot never slides; legs by two-bone IK with the knees bending toward the pelvis forward
  (the inherited knee plane bowed the stepping knee 17 cm out through the coat side); worst ankle IK miss 0.0 mm;
- the coat's leg capsules got a 0.08 m floor (thigh 0.06 → 0.08) so the skirt clears the lunging knee.

Gates (Attack, before → after): leg-through-coat poke 0 → 2 vertices / 0.6 cm (first try with the inherited knee
plane: 46 vertices / 6.3 cm); visible back faces mid-lunge 14–36 cm²; skirt stretch p99 1.10 → 1.26 (max 2.47);
armpit p99 at the highest-arm frame 2.464 → 2.467 (max 3.54 → 3.54); hands in body 0, hand stretch ≤ 1.05; soles:
planted foot −0.8…−0.1 cm, stepping foot lifts to 7.9 cm; jerk per 1/48 s: pelvis 1.4°, feet 0.4 / 1.5°, head 7.8°
(was 7.4°); button/placket seat drift ≤ 8.4 mm (Attack), 12.3 mm worst in Death (the thicker leg capsules changed
the fall). Blow re-measured at peak claw speed: 0.917 → **0.975 s** (binding updated). The thicker capsules raised the
standing skirt stretch p99 1.10 → 1.15. Sheets: `review/attack_feet_sheet.png` (front, side, three-quarter),
`review/attack_feet_closeups.png` (feet), `review/attack_lunge_coat_clay.png` and `review/attack_lunge_coat_tex.png`
(coat mid-lunge). Previous masters: `work/rig_v5_preattackfeet.blend`, `work/rig_v6_preattackfeet.blend`,
`work/mm7_m422_preattackfeet.glb`. Viewer: 21 switches, no console errors. No credits.

## Body retexture v2 (user approval 2026-10-20)

The light specks left by carrying the v1 layout onto the reworked coat mesh are gone: a fresh Meshy body retexture of
the FINAL mesh (`retexture_v2`, 10 credits, project total 40/100; the four HD masters, `enable_original_uv: false`).
- Upload `texturing/m422_body_upload_v2.glb` from `work/rig_v6.blend` (rest pose, 10,329 faces;
  `scripts/export_body_upload_v2.py`); Meshy's layout copied back face by face (`transfer_uv.py`: centroid mismatch p99
  0.0 mm) into the new texture master `work/rig_v6_upload2.blend` (`creature.json texture_upload_master`).
- The head set is unchanged (the head faces did not change; HeadUV and the head retexture are kept).
- `carry_uv.py` now copies the layout loop by loop when the rig mesh is identical to the texture master (the island
  search had put corners up to 22 cm off on an identical mesh). UV outlier triangles (> 4x the median texel ratio) 125
  -> 95, all on the hands, none on the coat.
- Compose, AO, material classes and region masks re-derived on the new UVs (`texture_refresh.sh`); tier gains refitted
  twice with `tier_match.py` (`textures/m422_ramp_gains.json`: coat 1.10 / 0.84 / 0.59, cape 1.06 / 1.12 / -, hair 0.78 /
  0.79 / 0.61). Rendered vs native median luminance: coat 0.251/0.252, 0.129/0.129, 0.106/0.101; cape 0.272/0.271,
  0.123/0.122; hair 0.190/0.189, 0.208/0.208, 0.148/0.146 (`review/tier_match.json`). Tier C's coat red stays less
  saturated than the native (chroma 0.26 vs 0.45).
- Close-ups (coat front, sleeve, hem mid-walk, coat mid-walk, mid-lunge; all tiers): `review/retexture_v2_closeups.png`;
  tiers beside the native palettes: `review/tiers_vs_native.png`. No specks on the coat, sleeves or hem; a small light
  patch shows at the left of the collar under the raised arm in the lunge only (not investigated further).
- Viewer: 21 switches, no console errors; winding 0 inverted. The belt-end flaps are unchanged (not remodelled).
