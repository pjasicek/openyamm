# MM9 Trellborg body (mm9_trellborg) — 3D actor, 2026-10-31

Rows 165 Trellborg L22 (`MM9 Trellborg A`, TRELLBORG1), 166 Kin Trellborg L35 (`B`, TRELLBORG2), 167 Ancient Trellborg L50 (`C`, TRELLBORG3), `TRELLBORG.abc`, 32 joints, 18 clips, no child model (all clips in the file). **Humanoid route**: `Bip01` biped, MM9 skeleton and clips, posed fists, wrapped Meshy body and head. Progress and receipts: `creature_3d_progress.json`.

| Item | Value |
|---|---|
| Runtime GLB | `assets_source/worlds/mm9/models/mm9_trellborg.glb` (`tools/install_model.py --world mm9`), variants `trell_a/b/c` |
| Binding | `assets_dev/worlds/mm9/models/actors.yml`, `MM9 Trellborg A/B/C`, scale 100, `yaw_offset` -1.570796327, stride 1.45 / 2.97 (`stride.py`), melee impact 0.333 s (`Rattack` in Hattack1), ranged impact 0.686 s released at `cast_hand` = `Bip01 R Hand` (MM9's RangeAttack node), look `Bip01 Neck, Head`, upper body `Bip01 Spine2` |
| Triangles LOD0/1/2/3 | r1 11,633 / 5,815 / 2,087 / 694, r10 adds 672 at LOD0; LOD0 body about 4,300, face 3,000, hair 2,600, fists 1,700, tusks 160, club 576 |
| Skeleton | MM9's 32 joints, names and rest rotations, knees half way to our mesh + 14 half-rotation helpers (`*_h`). Pivots `scripts/pivots.json`: knee and elbow back, hip forward. `Ponytail*` drive nothing (below) |
| Clips (30 fps) | Standing, Walking, Running, Fidget, AttackMelee `Hattack1`, AttackRanged `Rattack1`, Hit, Death, Dead; script clips AttackMelee2, Fidget2, Fidget3, Taunt, Aware, Hit2, Death2; Backpedal and BackpedalRun built, not bound |
| Textures | **Per tier (deviation):** body 2K colour + 1K normal + 1K ORM, head 1536 colour; shared head normal 1K and flat ORM; club 1K + 512 maps. 17 images, 43.6 MB as PNG in the export GLB. Cooked size not measured |
| Meshy credits | **40 / 40**: body Smart Topology 5, head Smart Topology 5, three 4K body paints 10 each (backup account, no retries) |

## Deviation: per-tier images
MM9's three skins are three outfits on one mesh: A leather harness over bare skin with steel bracers and greaves; B fur vest, claw necklace, fur and lace wraps; C mail shirt, lamellar shoulders and waist, steel boots. No ramp makes those, so this body follows `mm9_clansoldier_claude/`: one layout, three Meshy paints, `tier_materials.py`. All variant images upload for one tier. Head design is shared: one Codex paint, `tier_head.py` recolours hair and beard by MM9's luminance quantiles, and fills the band over the seam with the tier body's own pattern by reflection across the seam plane.

## Route (`scripts/`)
0. **Sources**: `convert_abc_model.py --scale 0.0256`, `mirror_glb.py` to `source/true/`, `bone_length_audit.py` 0 stretching on raw and true. Symmetric bind. `make_refs.sh`.
1. **Masters** (Codex): `references_hd/` five views of A (run 1b swapped Codex's fur skirt for MM9's tight shorts), `references_tiers/` four views of B and C, `references_head/00_geometry.png` clay sculpt, `references_club/` wood and iron.
2. **Meshy**: body and head-only Smart Topology. Both clean; the head's locks are separate pieces.
3. **`step_a.sh`**: `head_prep_trell.py`, `fit_trell.py` (limbs on MM9 bones, arms thinned 0.84 / 0.8), `graft_trell.py` (shell holes filled, strap ridges smoothed: the harness is tier A's paint only; lock tips lifted off the shoulders), `wrap_voxel.py` + `wrap_finish.py` (one closed skin at 4 mm).
4. **`rig_trell.py`** bone heat on a 6k copy, transferred; **`step_b.sh`** posed MPFB fists; **`quick.sh`** weights, helpers, `reduce_trell.py` (body 4.3k, hair 2.6k, face 3k, fists 1.7k), `make_club.py`, `add_club.py`, clips, `club_keys.py`, `half_keys.py`.
5. **UVs** `uv_trell.py`. **Never re-run**: the paints belong to `work/uv_v1.blend`.
6. **Paint** `textures.sh` (`compose_trell.py`, grade, `tone_trell.py`, `project_head.py`, `tier_head.py`).
7. **Runtime** `REV=<rev> scripts/rebuild.sh --install` (claim a lease, token in `work/token`); `retier.sh` when only images change; `bind_actors.py` under the flock. `final.sh` gates, `final2.sh` strips.

## Club and hands (user feedback fix, r5, 0 credits)
User: "hands not grafted properly, club outside of his palm/hand". Both true: the wrist band had folded inward to a groove, and my earlier "hole" was a gap outside the fist, so the handle ran beside it. My 2.55 in 2.79 cm check never tested the handle against the palm.
- **Wrists** (`fist.py`, `wrist_paint.py`): band vertices on the tube between the bracer's end ring and the hand's ring, polar per angle; band texels take the hand's own skin per tier, colour and normal (originals `textures/*_prewrist.png`). Hand scaled 1.08 from the wrist.
- **Grip** (`fist.py`, vertices only, UVs and paint frozen): fingers re-embedded on arcs round the handle (206 deg of arc at most), thumb swung rigidly over them, left a closed fist round 1.6 cm. The fists have no finger bones, so the Highwayman's per-joint solver could not run as it stands: MPFB's joint chain zigzags and joint FK mangled the low mesh. Its gate was adapted: `grip_gate.py`.
- **Club** is rigid in the fist; `club_keys.py` still moves MM9's up to 109 deg turn in the mitten to the wrist, with a constant 21.7 deg turn lining the fist up with MM9's axis. Direction matches MM9; position drifts as it pivots at the wrist (estimated up to 20 cm, not measured). Built from MM9's stations, 1.35 m, five nails and a hook, grip radius 2.55 cm.

## Wrist cuffs (r10, installed)
Orchestrator decision after the failed blends: a rigid flared cuff per arm hides the join, no credits, no new paint. `scripts/add_cuffs.py`, shape in `scripts/cuff_config.json`: closed double wall, 14 sides, 12 rings, from 3.6 cm over the bracer to 6.6 cm past the wrist joint, radius 8.1 to 11.6 cm (forearm about 7 cm), 100 % on `Bip01 {R,L} Forearm`. 336 quads, 672 triangles, on the Trellborg body material. UVs per quad from the last 12.4 cm of the bracer on the shared layout, so each tier's paint carries on and the bracer's rim falls on the cuff's edge. The r5 skin join stays under it, untouched; no band faces were removed. **The cuff is a design addition: MM9 has none.**

`wrist_gate.py`, all clips at 48 fps, runtime GLB, how far hand and band stick out past the cuff's outer wall in the forearm's frame. **Target 0 not met:**
| Arm | Worst | Walking | Running | AttackMelee | Others over 5 cm | Standing |
|---|---|---|---|---|---|---|
| R | 12.64 cm, AttackMelee2 0.65 s | 0.1 | 0.1 | 6.9 | Fidget2 9.4, Death 5.7, Death2 9.0 | 0 |
| L | 10.39 cm, Fidget 1.23 s | 2.4 | 5.2 | 2.9 | Fidget2 6.8, AttackMelee2 7.6, Death2 5.0, Fidget3 5.0 | 2.3 |
Club into the cuff: 0.00 cm on both arms. The rigid cuff cannot hold the wrist bends: `club_keys.py` puts up to 138 deg on the right wrist. The flare was not widened: the rim is already 1.6 x the forearm, and clearing L Standing and Running alone needs about 2.5-5 cm more. By eye these read as the hand leaving the cuff at an angle; worst seen, a wedge of hand over the lip in AttackMelee R, side view, tier A. Clips over 5 cm other than Running L and AttackMelee R were not looked at.
Paint seams: the source runs over bracer chart seams, so 106 of 336 quads are held inside one source triangle, and hard steps show on the cuff (white plate against leather on A and C, side view, near the free edge). Density about 1.5 x coarser round the rim. Under the cuff the join still has 13 and 9 open edges, hidden.

## Wrist blends tried before the cuff (r6-r9, not installed)
User verdict on r5: hands look cut off and glued on at the bracer. Later builds, none accepted:
- r6 (taper with smoothing, wider weight blend): the Laplacian shrank the sparse wrist ring to a thread, 3.8 cm radius at al 0.02, and the band paint streaked like wood. It reached the viewer; the user reported the hand detached.
- r7: explicit tube closed the thread; `wrist_gate.py` found 13 and 9 open edges on the zip ring, R and L. r8: weld left 1 and 0, with 3 and 1 multi edges (gate on Walking only for both).
- r9 (`scripts/fist_mode.txt` = r9): 0 open edges, 0 multi edges on both arms in every clip at 48 fps, neck ratio 0.86 R, 0.97 L, extra edge length 4.72 cm R, 2.38 cm L (stretch, not a gap). **Failed by eye**: in `review/shots/wrista/RunningLb.png` a wedge opens between bracer end and hand top, the hand's top still reads as a rectangular block in Walking, and the band paint is speckled. Saved as `work/mm9_trellborg_r9_attempt.glb`, not installed.
The join's real fault is the mesh there: about ten vertices per ring and a flat hand block from the MPFB stub. Vertex and weight work did not make it one limb. A proper fix needs a new tube on the frozen UVs or a re-grafted hand with new paint on that chart.
r10 is built on r5 (`fist_mode.txt` = r5, `wrist_paint_r5.py`).

## Checks (r1 clips and mesh unless marked r5; r5 moved hand vertices only)
| Gate | Result |
|---|---|
| Cloth | **Not applicable**: breeches, apron, vest and mail are tight paint on the skin. No cloth geometry, nothing measured in Walking or Running |
| `arm_hand_gate.py --outer-only --exact`, 48 fps | 0 frames over 1 cm in every clip **except script clip Fidget2: L hand 6.0 cm (gate cap), 74 frames, R hand 2.0 cm, 6 frames, R forearm 4.0 cm**. Arms cross over the club there; `arm_bump.py` Fidget 7.4 to 0, Fidget3 4.3 to 0.1, Fidget2 12 to 8.8 cm before the cap |
| `club_gate.py` (club in skin, 24 fps) | 0.0 cm in every clip **except Fidget2 5.7 cm, 13 frames** |
| `jitter_gate.py` r5 | **0 fails** (against the clips with the wrist keys, before helpers and bumps) |
| `grip_gate.py` r5, every clip | club rigid to the hand 0.0 deg in all 18 clips, so the fist holds wherever the wrist turns. Wrap, Standing: index 240, middle 225, ring 150, pinky 135, thumb 105, palm 150 deg. Wrap reads lower in posed clips (Dead: 180, 180, 105, 75, 45, 165): the bins use a rest-frame plane, a metric fault, since the fist is rigid. **Inside the handle 1.9 cm, 305 samples per clip:** skin webbing between finger roots and palm runs through the handle; opaque club hides it. Not removed |
| `arm_hand_gate.py` r5 | L as below. **R hand reads 1.8 cm in all clips, from that hidden webbing against the club** (constant, so I read it as the club, not the body; not separated) |
| `bone_length_audit.py` | 12 checked, 0 stretching |
| Handedness | R bone and club on the anatomical right, raw ABC mirrored |
| `detached_parts_audit.py` r5 | 12 components, 0 detached |
| `flat_shading_check.py` | 0.00 |
| `check_winding.py` | 0 inverted |
| `texture_quality.py` | body atlas 59.8 %, spread 1.34; head 55.8 %, spread 1.79 (face denser by design); club spread 4.52 (nails on few texels) |
| `floor_audit.py --world mm9` | 3 ok, 0 problems. Corpse raised 17 cm by `floor_fix.py` (MM9's fall goes under the floor) |
| Regression `mm9_actor_models_build_every_binding` r5 | PASS. Run stopped by a 200 s limit after that case: the rest of the `actors` suite did not finish. `--headless-validate-actor-models` 140 descriptors, 0 refused at r1, not repeated |
| `run_creature_review.py check` r5 | 0 failed |
| In game (`bootcamp.odm`, review root, isolated) | `review/ingame_sheet.png`: all tiers, hostile, club raised and swung, health bars |
| Faces, front on, each tier (`review/sheet_heads_front.png`, camera riding the head) | one pair of eyes, one nose, one mouth, one beard. Tusks are mesh: their painted copy was removed from the lips (`tier_head.py`, 40k texels) |

**Collapse, worst frame** (`review/gates/collapse.txt`, all LOD0 primitives, club excluded by region; `seen` = worst exposed region). Not zero.

| Clip | face-frames | knee | elbow | shoulder | wrist R | torso | head | seen |
|---|---|---|---|---|---|---|---|---|
| Standing | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Walking | 6 | 2 | 0 | 0 | 0 | 0 | 0 | knee 2 |
| Running | 49 | 4 | 0 | 0 | 0 | 1 | 2 | knee 4 |
| Fidget | 320 | 0 | 6 | 6 | 0 | 1 | 1 | shoulder 6 |
| Fidget2 | 1336 | 0 | 2 | 25 | 7 | 0 | 2 | wrist 6, shoulder 5 |
| Fidget3 | 318 | 0 | 0 | 7 | 0 | 1 | 5 | head 4 |
| AttackMelee | 108 | 0 | 1 | 12 | 0 | 3 | 8 | shoulder 6 |
| AttackMelee2 | 193 | 0 | 4 | 0 | 11 | 2 | 3 | wrist 3 |
| AttackRanged, Taunt | 57 | 0 | 4 | 2 | 0 | 0 | 4 | shoulder 2 |
| Aware | 98 | 0 | 4 | 2 | 0 | 0 | 4 | shoulder 2 |
| Hit / Hit2 | 33 / 39 | 0 | 0 | 6 / 1 | 0 | 0 / 2 | 1 / 2 | shoulder 3 / torso 2 |
| Death | 116 | 0 | 1 | 3 | 0 | 1 | 12 | head 6 |
| Death2 | 338 | 0 | 1 | 5 | 6 | 11 | 6 | torso 11 |
| Dead | 465 | 0 | 1 | 1 | 0 | 1 | 12 | head 6 |

Finger-and-wrist stretch reaches 4.03 in AttackMelee2 (138 deg at the wrist, MM9's club swing), 3.33 in Fidget2, 2.77 in AttackMelee.

## Decisions and open points
- **Hands**: MM9 mitten, `Finger0` only. Posed five-finger fists, rigid; right curl 64-76 to hold the shaft, left 80-92.
- **Hair**: one closed voxel mass, rigid on the head. MM9's `Ponytail*` sway is not used; its roots carry a constant 16 deg offset. Deviation from MM9's secondary motion.
- **Mouth**: no jaw bone, closed. Tusks are separate mesh pieces, eyes are paint on the shell (not separate pieces).
- **Seam at the neck**: the head set reaches the shoulder tops. Reflection carries the outfit over it, but a smeared wedge shows on both shoulder tops by the neck (B fur, A broken strap ends) and fine facet lines show under the jaw from below. Open, by eye, seen in `sheet_heads_front.png`, `sheet_closeups_a.png`.
- **Beard**: B and C keep some of A's red at the top of the beard, pale slivers beside it on B and C. **C forehead**: dark smudge at the widow's peak.
- **Tone**: skin brighter and more orange than MM9 in the viewer; studs and strap edges near white on A. Tiers read correct in game.
- **Tier C feet**: steel paint over toe geometry, no sabaton shell; reads as segmented steel.
- **Muscle relief**: the wrap softened it; it is carried by the paint.
- **Rows at sprite height** 200 world units against a 233 cm figure: health bar sits low. Not corrected.
- **Velocity events** in die1 and die2 not carried over. `Rattack`, FX and sounds as on other bodies. Projectile RingOfFire's launch point not looked at.

## Sheets (viewer shots)
`review/sheet_mm9_vs_ours.png` (MM9 Blender render, ours front and back, every tier), `review/sheet_tiers.png`, `review/sheet_heads_front.png`, `review/sheet_closeups_a.png`, `_c.png` (knees, groin, armpits, elbows, neck, mouth in AttackMelee2 crouch, Death, Dead), `review/strips_{a,b,c}_{1,2}.png` (18 clips, five frames, each tier), `review/ingame_sheet.png`. Numbers `review/gates/`.

## Not checked
r10 shots read at 900 px per view (`review/cuff_{a,b,c}_{0,1,2}.png`, all together `review/sheet_wrist_cuff.png`): all 42 views, 3 tiers, both hands, Running, Walking, AttackMelee, back and side, plus the two front-quarter views of the user's images. Collapse, arm and hand, floor, in-game, strips and close-ups not repeated on r10. In game the cuffs are unseen. Cuff triangles in LOD1-3 not looked at. r9 wrist sheets `review/sheet_wrist_fix.png` (not installed): I read `review/wrist_{a,b,c}.png` at 480 px per view and two views at 900 px. Rebuilt r5: one view read (tier C, Running, left wrist, back). Hand acceptance: not the full set asked for. All tiers, both hands, front, palm, back, Standing, Walking, AttackMelee are shot at r5 (`review/shots/hand{a,b,c}/`, sheets `review/sheet_hands_{a,b,c}.png`). I read `sheet_hands_c` at 320 px per view (r5), `sheet_hands_a` at 320 px at r4 before the thumb fix, and two views at 900 px (`review/sheet_grip_full.png`, tier B, palm side Standing, front AttackMelee). Not read: `sheet_hands_b`, `sheet_hands_a` at r5, and the 54 views at full size. Collapse, floor, club gate, in-game, strips, close-ups not repeated on r5: strips and close-ups show the old fists. Fidget2's numbers are r1 for the club. Read of the other sheets as before: `strips_c_2` only; `sheet_closeups_c`, `sheet_mm9_vs_ours` made and not looked at. Normal-speed playback, LOD1-3 and shadow meshes by eye, real maps, indoor light, ranged release, sounds, rest of the `actors` suite, cooked size, Android.

User artistic acceptance: "trellborg - fine I guess" (2026-10-31, r10 with cuffs)


**LOD0 reduced post-install on 2026-11-04 by `level_generation/creatures/mm9_trellborg_reduce_claude/`** (user-approved; ledger: `level_generation/creatures/REDUCTION_LEDGER.md`, "MM9 reduction"). A rebuild from this project must re-run that reduction, or it silently restores the heavier mesh. Rollback source: `mm9_trellborg_reduce_claude/before/`.
