# MM6 Cannibal / Head Hunter / Witch Doctor, male (natm) — Claude rig-first project

Second attempt after `mm6_natm_codex/` (user, 2026-10-13: the attack and the blow delivery looked artificial; the
model "too artificial" overall). Free hand on clips; Meshy budget 200 credits. Installed as `mm6_natm.glb` with the
`mm6_natm_spear.glb` / `mm6_natm_buckler.glb` attachments (bindings `PeasantM4 A/B/C` in
`assets_dev/worlds/mm6/models/actors.yml`).

[Review viewer](review/viewer/index.html) · [attack key frames](review/glb_attack.png) ·
[arm close-ups at the blow](review/arm_attack.png) · [in-game](review/ingame/)

## The attack (what changed and why)

- **Grip analysis decided the move.** The humanoid set's one-handed grip holds a weapon like a hammer: the shaft runs
  across the palm with the tip out of the thumb side. With that grip a spear points along the forearm only with a
  60–90° wrist bend, and an overhand (javelin) thrust needs the reversed grip. The set's spear attacks therefore stab
  into the ground (SpearAttackR3: tip 2 cm above the floor 2 m ahead, then an 8-frame frozen hold) and the Codex clip
  inherited that look. The natural blow for this grip — and for the native's carry (spear low, level, tip forward) —
  is an **underhand lunge thrust**.
- **Body from mocap, blow authored** (`scripts/author_attack.py`, parameters in `scripts/attack_params.json`):
  Mixamo "Stabbing (2)" gives the trunk, head and the shield arm's counterbalance (time-remapped); everything that
  decides how the blow reads is authored on top:
  - anticipation 0–0.5 s: pelvis sinks and draws back, hips then chest coil 12°/19° to the spear side, the spear hand
    swings back past the hip (shoulder extension 30°, arm abducted 15°), the shield comes up in front (native frames b/c);
  - strike 0.52–0.64 s: the left foot steps 45 cm into the lunge (sine lift, toe-up), the right heel peels up 22° and
    drives, the pelvis travels 28 cm forward and drops 11 cm, the hips lead the chest by 50 ms (kinetic chain), the
    trunk leans 16° into the blow, the right clavicle reaches forward 14°, the arm swings forward to 55° flexion;
  - the spear points at a target at chest height (1.2 m, 2.1 m ahead, 30 cm toward his left: a right-hand underhand
    thrust crosses toward the centre line, and a dead-centre thrust foreshortened to a dot from the party's view);
  - follow-through: 4° overshoot, the tip dips 7°, a short settle, recovery and the left foot steps back home;
  - the arm is solved by `scripts/armik.py`: minimal-change IK plus a global (Viterbi) choice of elbow plane and hand
    roll over the whole clip (least wrist bend + forearm twist, continuity) — per-frame greedy solves flipped the hand.
- Blow at **0.626 s** (spear tip at 95 % of its 0.9 m forward travel; `scripts/clip_timing.py`), inside the native
  0.75 s action. Peak tip speed ~11 m/s.

## Other clips

| Role | Source | Notes |
|---|---|---|
| Standing | Mixamo Standard Idle | authored spear carry (`author_carry.py`, `carry.json`): wrist in the chest frame, spear fixed in the pelvis frame (tip 15° out, 4° down, like natmsta), 30 % of the idle's own wrist motion |
| Walking | Mixamo Walk | 1.69 m natural stride (tier A at 220 units/s plays it ~1.24x; the set's armed walk would have been 1.5x) + carry |
| Running | Mixamo Standard Run | `run_fit.py`: pelvis at 92 % of Standing + the source bob (bar1 review: not crouched), 1.5 m stride, 13° lean, gaze levelled; carry tip raised 6°/out 8° (clears the knees) |
| Hit | set Unarmed get-hit F1 | + carry (40 % own wrist motion); blends 0.12/0.20 s |
| Cast (Witch Doctor) | set Armed cast with the left hand | palm thrust, spear held upright; 0.3 s ready ease; Fire Bolt from `Socket_LeftPalm` at 0.55 s |
| Fidget | Mixamo Sword And Shield Power Up (planted) | spear swept overhead, chest out, head back |
| Death / Dead | Mixamo Standing React Death Backward | falls onto the back (native natmde), travel halved so the corpse lies near the actor |

`spear_clear.py` turns the spear hand minimally (wrist only, ≤ 36°, smoothed) wherever the 1.9 m shaft would enter the
body in clips that keep their source arms (fidget, death, cast, hit).

## Model and textures

- Geometry: Codex's Smart Topology of the Codex HD three-quarter master (reused; a fresh 5-credit job is kept in
  `meshy/body_geometry_v1/` as an alternative). 439 loose parts: skin, ~400 feather cards (mantle, hip trim, leg
  guards), arm rings, loincloth panels, tooth beads, eyes — labelled per garment (`garments.py`).
- Rig: source-frame rig (bar1/gob2 route), elbows from Meshy's auto-rig centred on the ring centreline (the ring
  line fit put them at 68–76 % of the arm), fingers by connectivity, twist bones (forearm 0.6, ramp 15–85 %).
- Weights by garment (`weights_fix.py`): mantle copies the skin (legs to the pelvis, arm share ≤ 0.25, smoothed
  per card); hip-trim and leg-guard cards rigid per card; loincloth strips pelvis→thighs; rings rigid; beads hang.
- 9,274 body triangles after weighting (head and hands protected) + spear 586 + buckler 624; LODs
  10,440 / 5,090 / 1,625 / 465.
- Textures: Meshy retexture (own UVs, copied back) + head retexture (1K head set). Skin repainted to one warm albedo
  times Meshy's fine shading (Meshy painted salmon-to-dark patches; the Codex model read dark and plastic), AO baked,
  per-class specular/roughness. One recolour region as the native mask: loincloth, belt, arm bands, leg-guard
  bindings, spear bindings, buckler paint; ramps per tier from the native frames. Tier palettes from dsft.bin:
  **A Cannibal 795 (grey), B Head Hunter 796 (olive), C Witch Doctor 797 (red)** (the restoration README's "base
  796" is the art's base, not tier A).
- Props modelled from the HD prop references and textured by projection (`make_props.py`, `prop_textures.py`).

## Gates (2026-10-14, final export)

- G6 contacts (`g6_contacts.py`, half frames; skin = inside test, feather cards/panels = proximity): no spear,
  forearm, hand or buckler point inside the skin in any clip, except the cast's left palm (1.0 cm, one frame). The
  spear brushes feather cards in the fidget (8 samples) and death (3). Spear clearance turned the hand ≤ 15° (fidget,
  death, attack 3°); the hit needed 36° on 3 frames.
- G5 hand stretch: right 2.10x every clip (the solved fist), left ≤ 3.09x (source fist curl); limit ~4.5x.
- G4 arm stretch p99 ≤ 1.98 (attack, clavicle reach 14°), max 2.68 (clavicle), cast left clavicle max 3.26.
- Wrist swing: attack ≤ 35°, carry ≤ 50°; the hit reaches 74° for a few frames of its 0.5 s recoil (above the 60°
  guideline; left as is).
- Viewer check 27/27 tier/clip switches, no console errors. Regression `mm6_peasant_m4_actor_model_tiers_share_the_
  native_height` passes (all four peasant cases pass; the full mm6 actors run had 3 unrelated failures: mage, guard
  and ooze bindings).
- In game: outdoor (oute3) and indoor (6d19) captures, 3D vs native sprites at the same camera:
  `review/ingame/final_ingame.jpg`, `out_cmp.jpg`, `crop_cmp2.png`.

## Reduction (2026-10-14)

The installed body is now the head-protected reduction from `../mm6_natm_reduce_claude/` (9,230 -> 6,003 triangles,
installed head and head texture kept, body retextured, the chest hole of the Smart Topology mesh closed, pendants
ivory). The model, LOD and texture numbers above describe the unreduced version; its source is kept in
`../mm6_natm_reduce_claude/work/mm6_natm_source_pre_reduce.glb`. The installed Attack plays 1.5x faster (1.0 s, blow
0.419 s in `actors.yml`) and Death 2x faster (1.8 s), retimed in the reduce project (user, 2026-10-14).
`scripts/build_runtime.sh --install` here would reinstall the unreduced body at the old speeds: after a clip change,
rerun the chain in `../mm6_natm_reduce_claude/` (`swap_body.py`, `retime_clips.py -- work/rig_v5.blend Attack:1.5
Death:2`, `export_uploads.py`, `copy_head_uv.py`, `h65_texture_chain.sh`; the stored Meshy body job stays valid while
the geometry is unchanged) and install from there.

## Replay

`scripts/rebuild.sh` (STAGE=rig, then STAGE=anim), texture chain once (`export_uploads.py`, Meshy jobs,
`transfer_uv.py`, `uv_raster.py`, `bake_ao_natm.py`, `compose_natm.py`), then `scripts/build_runtime.sh --install`.
Meshy: **30 of 200 credits** (unused alternative Smart Topology 5, auto-rig 5, body retexture 10, head retexture 10).

## Known limits

- The feather mantle and loincloth panels are skinned, not simulated (no secondary swing).
- Skin is a little lighter and flatter than the sprites' baked shading; the props are projected from the HD
  references (the buckler straps' inner faces shade softly).
- Tier A walks at 220 units/s against the walk's natural 1.69 m/s (played ~1.24x).

## Review round 1 (user, 2026-10-14)

| Feedback | Cause (measured) | Fix |
|---|---|---|
| Attack frames 32-33+ (48 fps) anatomy: armpit, forearm, wrist | clavicle reach 14°, arm flex 55°, hand twist 85-105° at the blow | clavicle 8°, flex 50°, twist cost 0.6 in the arm solver: twist 41-59°, arm stretch p99 1.85 |
| Feet warped, not planted | the Mixamo/set toe channels curled the toes up 4-7 cm; the idle (and walk) pitched both feet ~20° toe-up; the heel peel pivoted 5 cm above the floor (ball 3 cm under); the hit floated 17 cm, the cast sank 6 cm, the dead body lay 28 cm under the floor | `foot_level.py` (grounded feet levelled; the walk only its constant 20° tilt); toes back to rest; heel peel about a floor-level pivot + mesh floor clamp; floor pass in `clip_timing.py` |
| Head turn/jerk right at frames 29-34 | chest/neck counter-yaw with a 50 ms lag | head stabiliser (smoothed gaze, yaw held 50 % toward the target) |
| Running like fast walking | the first fit replaced the legs with sine-lift foot paths (no heel kick or knee drive) | the source's own ankle paths relative to the pelvis, 1.8 m stride, 5 cm bob; feet levelled by a constant yaw (per-frame yaw flipped 60-100°) |
| Running right elbow jerk frames 11-13 | per-frame IK flipped the elbow plane where the source arm straightened | the carry uses the global elbow/roll solver, smoothed; 35 % of the run's own hand motion |

Sole probe (`sole_probe.py`): every grounded foot within -1.8..+1.8 cm of the floor in every clip; jerk probe
(`jerk_probe.py`, 48 fps): running feet ≤ 17° per step (was 101°), right forearm ≤ 13° (was 19.5° with 2x the
acceleration). Bindings: run stride 1.8, attack impact 0.628 s.
