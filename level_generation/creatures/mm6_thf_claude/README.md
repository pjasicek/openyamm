# MM6 Thief (thf) — 3D model, 2026-10-09

Thief / Burglar / Rogue (descriptors BThief A/B/C, 637–639; palettes 825 grey-green / 826 purple / 827 brown), built
with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md): Codex HD masters → Meshy Smart Topology → own cleanup
and UVs → Meshy API auto-rig + cloak chains, finger rig and daggers → clips (Meshy rig/library + authored from the
native keys) → body retexture + head set → cloth region tiers. Runtime: `assets_dev/worlds/mm6/models/mm6_thf.glb`,
bound in `assets_dev/worlds/mm6/models/actors.yml` (opt-in via `debug.actor_models=true`).
Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_thf_claude/review/viewer/> (checked with
`claude_shared/check_viewer.mjs`: 3 tiers × 8 clips, no errors).

| Item | Value |
|---|---|
| LOD0/1/2/3 | 9,506 / 4,751 / 1,704 / 563 (Smart Topology 15k; eyeballs, a chest clasp and specks removed; face and hood kept) |
| Textures | body set 1K (from Meshy 2K), head set 1K (face + hood), normal and ORM (R baked AO) 1K; 9.2 MB GLB |
| Tiers | one region (cloth: hood, mantle, cloak, undershirt cuffs/hem), ramps from the native cloth pixels; everything else unchanged |
| Rig | Meshy auto-rig (wrist joints moved onto the hand shells) + 17 cloak chains × 4 bones (baked verlet), mitten finger rig (3 finger + 2 thumb bones per hand), DaggerL/DaggerR |
| Clips (24 fps) | Standing 2.0 s, Walking 1.04 s, Running 0.625 s (Meshy rig, jog), Attack 0.75 s (authored: two alternating thrusts with a lunge step since 2026-10-14; melee and thrown dagger), Hit 0.75 s (Mixamo Medium Hit To Head, `retarget_hit.py`, 2026-10-14), Death 1.125 s (Meshy 189 at twice the source speed, 2026-10-14), Dead, Fidget 0.75 s |
| Scale | 108.68 (native stand frame 245 px × frame scale 0.7 = 171.5 units against the 1.578 m model; all tiers) |
| Meshy credits | 36 of 60: Smart Topology 5, rig 5, two library clips 6, body retexture 10, head retexture 10 |

## Pipeline (scripts/)

1. `references_hd/` (Codex; `CODEX_BRIEF_v1_primary.md` for the primary, `CODEX_BRIEF.md` for views 01–04),
   `references_head/` (head turnaround). Gate: `review/hd_gate.png`, `review/head_gate.png`.
2. `examine_parts.py` → `analyse_parts.py` (visibility) → `step1_thf.py` (`work/step1_v1.blend`) → `uv_thf.py`
   (`work/step1_uv.blend`; gate `uv_check.py`, `draw_uv_layout.py`).
3. `export_clean.py` → Meshy rig (`requests/rig_v1.json`) and library clips (`requests/anim_*_v1.json`) →
   `rebuild_anim.sh`: `build_rig_thf.py` → `cloak_rig.py` → `finger_rig.py` → `fist_solve.py` → `seat_daggers.py`
   (`work/rig_v1.blend`) → `build_clips_thf.py` → `attack_thf.py` → `cloak_sim.py` (`work/rig_v2.blend`) →
   `apply_head_split.py` (`work/rig_v3.blend`: the head faces and UVs of the head retexture upload, restored exactly).
   Gates: `pose_audit.py -- rig_v2.blend`, `cloak_poke.py`, `cloak_stretch.py`, and the viewer-timing trace below.
7. **Trace loop** (after `export_runtime.py`): `trace_clip.py -- <clip> 48` imports the exported GLB, plays it with
   linear keys at 48 fps like the viewer, and records shoulder/elbow/wrist/hand/dagger grip and tip per half-frame with
   the wrist seam gap, hand-ring drift in the forearm frame, wrist swing/twist, forearm twist, hand turn per
   half-frame and the widest cloak opening; `trace_gate.py <clips>` checks them; `plot_trace.py <clip>` (matplotlib,
   e.g. a venv with system site packages) draws the paths and metrics (`review/trace_Attack.png`).
4. `export_neutral.py` → body retexture; `claude_shared/head_texture_split.py` (parts 0 1 6, whole 6) → head retexture;
   `claude_shared/bake_creature_ao.py` on rig_v2 → `work/ao_body.png`.
5. `build_runtime.sh [--install]`: `native_pixels.py` → `dump_uv3d.py` → `prepare_textures.py` →
   `compose_head_set.py` → `dump_head_uv.py` → `head_tiers.py` → `export_runtime.py` → LODs → `shrink_shadow_lods.py`
   → region variants → `merge_head_material.py` → install → `viewer_tiers.py` → `update_viewer_manifest.py`.
6. Regression `mm6_thief_actor_model_tiers_share_the_native_height` (headless `actors` suite).

## Trace review (user review 2026-10-09: right wrist detached and deforming from viewer frame 7, a cloak sheet
## under the raised arm)

- **Right wrist detached**: Meshy's RightHand joint sat ~5 cm behind the wrist (left ~1.5 cm), so every wrist bend
  swung the rigid hand shell out of the bracer: 38 mm ring drift, 15 mm seam gap in the attack. `build_rig_thf.py`
  moves both Hand joints to the hand shells' wrist rings: drift ≤ 2 mm, gap ≤ 2.3 mm in every clip.
- **Hand flips**: per-key forearm rolls were chosen independently (+60 → −40 → +60) and the wrist re-solved per frame:
  ~100° hand turns within one 48 fps frame. The attack now solves roll (≤ 50°) and a swing-only wrist (≤ 40°) per key
  with a continuity cost, interpolates roll and wrist rotation between keys, and moves the hands on a Catmull-Rom path
  through in-between keys (the travelling hand passes in front of the body, blade forward; straight key-to-key
  interpolation swept the arms out sideways with the daggers pointing at his neck). Hand turn ≤ 39° per half-frame.
- **Cloak sheet**: the arm attach reached the side panel near the elbow (9× edge stretch); it now covers only the
  mantle over the shoulder (z 1.05–1.15 fade, 5–12 cm from the upper arm).
- **Cloak, all clips**: 17 chains (was 11), weights diffused over the cloak's edges (4 passes), constraints iterated
  with collisions last, foot capsules, arm capsules at least 4 cm, and lying targets flattened onto the floor (the
  death crumpled with 34× stretch). The run is a jog (knees and thighs at 65 %; the Rogue, speed 270 > 2.4 × scale,
  always runs). Remaining: stretched-cloth openings of 6–10 cm between chains (gate warning), and in the run the
  kicked calf shows at the hem in a few frames.
- The head split is restored from the head retexture upload (`apply_head_split.py`): the weight-derived split had
  changed by 6 faces after the cloak changes.

## Attack redesign (user review: "he only shows off his knives, he doesn't stab or slice")

The native keys' raise-and-lower with a crosswise dagger read as a flourish. Now two thrusts, alternating hands:
chamber beside the hip (elbow back, blade forward), a fast thrust at chest height with the arm extended and the chest
turning into it, recoil, the other hand, guard. The daggers sit in a diagonal hammer grip (55° to the forearm,
`seat_daggers.py` GRIP_DEG), so a thrust points the blade forward. `attack_thf.py` writes `work/attack_intent.json`
(wrist target and blade direction per key); `trace_gate.py` compares the played clip with it: wrists within 0.3 cm,
blades within 7° (right) and 4° (left) at the thrusts, ≤ 22° elsewhere. The comparison exposed two solver bugs that
had also spoiled the earlier attack: the wrist turn used `rotation_difference` (a local-frame difference) as a world
rotation, and the forearm roll turned about Meshy's guessed bone tail (the right hand landed 3.4 cm off target).
Viewer keys: `review/viewer_thrusts_v2.png`.

## Notes

- **Cloak.** Smart Topology returned hood, mantle and cloak as one closed thick shell, open at the front, hanging
  outside the arms. Meshy's auto-rig weighted it to the legs and hands; `cloak_rig.py` replaces every cloak weight:
  hood on Head/neck, mantle front on the chest, the rest on 17 chains (every ~13.5° from −108° to +108°) whose points sit
  mid-thickness on the cloak (ray casts), blended by angle and height. The mantle over the shoulder follows the upper arm, so a raised
  arm lifts it as in native attack keys b/c.
  `cloak_sim.py` simulates 9 points per chain (joints and bone midpoints) against capsules on the legs, hips, torso and
  arms. Collisions are **one-sided** (a point inside moves outward along its chain's direction): a radial push let the
  back leg sweep the points to the inside, 1,802 leg vertices poked through over the walk; now the cloak stays behind
  the leg (only the heel shows below the hem). The target is the rest bell hung plumb (heading only), blending into the
  chest frame as the chest tilts past 25–70° (the death: the cloak falls with him and spreads on the floor).
- **Hands and daggers.** The Smart Topology hands came back relaxed and open (the brief asked for loosely closed
  hands), and Meshy's rig has no finger chains. `finger_rig.py` adds a mitten chain (four fingers together) and a
  two-bone thumb per hand; `fist_solve.py` fits the curl so the finger joints lie on a circle round the grip and lays
  the thumb over the top of the grip. Hands stay relaxed (native stand/walk) and close only in the attack. The daggers
  (from the Crude Dagger icon, 27 cm) are part of the skinned mesh, 100 % on DaggerL/DaggerR, keyed at scale 0.001 in
  every clip but Attack, textured from steel/iron/leather swatches in an empty atlas corner.
- **Weights fixed after Meshy:** hand weight on the right knee (up to 84 %; legs, boots, skirt and hip props lose all
  arm weight), the chest bleed ramp, the jerkin's side panels under the armpit (arm weight capped at 20 % in z
  1.02–1.17: they stretched toward the raised arm in attack key b, `review/atk_b_zoom.png` → `_v2`).
- **Clips.** Standing is authored (Meshy idles stoop). Walk keeps 35 % of Meshy's arm swing (native walk barely swings
  under the cloak), run 45 % plus 6° outward (full swing put the forearms 3 cm into the jerkin), its knees and thighs 65 %. Attack follows the
  native keys: right low (a), right raised (b), right stabs as the left rises (c), left stabs across (d), waist guard
  (e), with in-between keys; see the trace review above. The Mixamo "Dual Weapon
  Combo" was the closest catalogue clip but needs a manual download; not used. Hit: Meshy Hit Reaction 1 at its peak,
  upper-arm roll 70 %. Death: Meshy Dying Backwards, spine twist 50 %, upper-arm roll 60 %, wrists 60 % capped at 45°.
- **Gate** (`pose_audit.py`, all clips): arm penetration ≤ 0.1 cm, dagger penetration 0, wrist ≤ 44°, forearm twist
  ≤ 59°, upper-arm roll ≤ 37°, corpse at the floor (lowest vertex −1 cm, the cloak under the body).
- **Tiers.** The native B/C palettes are deterministic recolours of A, so `native_pixels.py` takes the cloth region as
  the pixels that differ between palettes. Cloth ramp gain 1.0 and a 50 % native shading transfer by height (gain 1.3
  without shading read 30–40 % brighter than the sprites in game, `review/ingame/crop_2.png` → `fight_v2_sheet.png`).
  The head set's hood takes the neck-seam gain (0.687) alone; the face keeps 1.0. Hands × 0.85 (near-white otherwise).
- In game: `review/ingame/fight_v2_sheet.png` (3D left, sprites right, same camera; A/B/C attacking an immortal
  party at the New Sorpigal test spot).
- Known limits: the raised arms in keys b/c are straighter and more vertical than the native (elbow out); the fist
  leaves a ~1 cm gap between thumb and grip; the hands are mittens (the four fingers curl together); the 3D trousers
  are matte where the sprite's are glossy; the run is Meshy's with damped arms (MM6 shows no run of its own).

## Death at source speed (2026-10-10)

`build_clips_thf.py` plays the whole Dying Backwards clip at source speed (2.21 s; was 1.5x in 1.5 s), see the
[clip timing audit](../CLIP_TIMING_AUDIT_20261010.md). Replayed `attack_thf.py`, `cloak_sim.py`, rig_v3 head
restore, build. Gates: pose audit as before, cloak poke 0, worst cloak tear 9.6 cm (was 10.3). Backups
`work/rig_v{2,3}_pre_death_timing.blend`.
