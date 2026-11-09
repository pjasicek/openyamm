# MM7 Elven Warrior / Elven Defender / Elven Lancer (`m218`) — Claude humanoid route (batch C, 2026-10-20)

MM7 batch C model 2 ([BATCH_C.md](../mm7_batches/BATCH_C.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights, solved fists); scripts start from `../mm7_m214_claude/` (itself from natm).
**Not installed**: install commands and the `actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart
Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10). User artistic acceptance is not
recorded.

[Review viewer](review/viewer/index.html) (serve the repository root, e.g. port 8912) ·
[tier shots](review/shots/tiers_sheet.png) · [tier close-up](review/shots/tier_check.png) ·
[actions](review/shots/actions_sheet.png) · [gates](review/gates_final.txt)

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m218.glb` | body: one skinned mesh `Elf`, 3 tier variants (`m218_a/b/c`) on one merged body+head material (2080×1024 atlases), colour LODs 9,586 / 4,775 / 1,692 / 541 tris + shadow LODs, 8 clips |
| `mm7_m218_spear.glb` | rigid spear attachment on node `Spear` (486 / 242 / 86 / 27 tris) |
| `mm7_m218.blend` | editable master (rig, textured mesh with the spear, clips), images packed |
| `mm7_m218_lod0.glb` | full-detail portable export before LODs/split (review viewer source) |

## Native identity and tiers

Native MM7 bitmaps `m218*` (119 frames) with the tier palettes from the sprite frame tables (`m219-221.yml`):
**A Elven Warrior = 50** (green loincloth), **B Elven Defender = 220** (blue-violet, the HD masters' colours),
**C Elven Lancer = 221** (crimson). Male woodland elf: pale skin, dark hair with a ponytail, two leaf sprigs as a crown,
green vines around chest, arms and legs, tabbed loincloth on a brown belt, leather bracers, bare feet, a spear in the
left hand and a second shaft slung across the back. HD masters/head views in `references_hd/`, `references_head/`
(Codex added a small hip pouch; kept).

## Model, rig and weights

- Smart Topology of `00_three_quarter.png`: 14,497 tris in 115 shells (one skin shell head-to-feet with the hair, separate
  hands, bracers, belt, front/back loincloth panels, back shaft, ~100 crown leaves). Props use piece ids 1000+ (this
  return has more than 100 shells).
- Joints (`joints_m218.py`): Meshy for the axial joints, shoulders, hips, knees and elbows (t ≈ 0.54, centred on the
  arm section); wrists at the hand shells' openings; ankles at the narrowest shin ring. Fingers fitted by connectivity.
- Weights (`weights_fix.py`): skin = Meshy (+ shoulder fade, neck free of the shoulders); every head piece (crown
  leaves, eyes, mouth) rigid on the head; back shaft rigid `B_Spine2`; belt copies the skin; bracers rigid on the skin
  mean (arm and twist kept); loincloth panels and tabs pelvis → thighs (natm rule); pouches/necklace rigid, no arm.
  Reduced after weighting (head, hands and crown leaves protected) to 9,586 body triangles.
- Spear (`make_spear.py`): 2.0 m, leaf blade traced from the HD reference, r 1.4 cm shaft; `Spear` is a world-keyed bone
  (child of `B_Pelvis`) so it can ride in the left fist (carry) and be gripped two-handed (attack).

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 3.00 | Mixamo Standard Idle; left-hand spear carry (`author_carry.py` SIDE=L), tip forward-down (native m218sa) |
| Walking | 1.00 | Mixamo Walk (1.78 m stride); the spear arm holds the idle's arm beside the body (`arm_hold.py`: world orientation of the idle's arm, ±6° swing against the right arm); floor pass |
| Running | 0.73 | Mixamo Standard Run fitted (2.12 m stride) + carry held out and forward |
| Attack | 1.40 | Humanoid set 2Hand-Spear Attack9 (`author_spear.py`): both fists on the shaft, lifted to the shoulder, horizontal two-handed thrust (native m218ab..ag); the set's lunge narrowed to 50 % and raised; wind-up retimed (source blow frame 17.9 → 23.5) so the **blow lands at 0.862 s** (native action 0.875 s, the game acts at its end). The spear stays in the left fist; the shaft line moves 12 cm forward, 14 cm down and 16 cm to the right in the chest's frame (`LSHIFT`, left wrist re-solved), the right fist is solved onto the shaft 0.42 m behind it (global elbow/roll solver) and eased in; the return to the idle takes 16 frames from full reach (second review: 10 frames swung the right elbow abruptly at frames 33-39), the right wrist and elbow on an IK arc bowed 12 cm out of the chest in the eased frames and the right arm smoothed over frames 26-42 (`smooth_arm.py`); both elbows then turned about the shoulder → wrist line out of the torso on the final weights (`elbow_clear.py`: right up to 70° over frames 16-33, left up to 60° in the wind-up; a one-shot clip's ends stay at the idle's arm) and the twist bones rebaked |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1 + carry; blends 0.12 / 0.20 s; floor pass |
| Death | 3.63 | Mixamo Standing React Death Backward (travel halved): falls onto the back; the fist opens at 0.5 s and the spear drops to lie flat beside the body (native m218da..dd) |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.47 | authored over Standing: the spear lifted upright beside the body, held, lowered (native m218fa..fd) |

User review 2026-10-20: the walk tucked the spear arm against the body (now held as in the idle); the thrust put the
right arm into the chest (shaft line moved, elbows cleared); the feet stood on their outer edges (`foot_level.py` now
also levels the sole roll while planted: batch A's rule, the run roll only).

Tried and rejected for the attack: natm's authored hip-level lunge over Mixamo "Stabbing (2)" with the left hand
solved onto the shaft (the left hand could not reach it: 8-19 cm gaps).

## Textures

Meshy body retexture (own UVs, copied back exactly) + head retexture (1K head set: head skin above a level neck cut, the
crown leaves, eyes). `compose_m218.py`: one skin albedo × Meshy's fine shading under the painted vines, AO grade,
specular classes, class maps. One recolour region (R): the loincloth panels and blue-violet tabs. Ramps: each tier
palette's saturated loincloth entries (indices 189-246 that differ between the tiers, saturation > 0.4, the darkest
fifth dropped), sorted by luminance, × 1.35. (A rank match through tier B's luminance mixed grey highlights into the
ramps; the darkest entries are purple/teal shade that turned C purple.)

## Gates (final rig, `review/gates_final.txt`)

- G5 hand stretch: right fist ≤ 3.01x, left ≤ 2.40x (limit ~4.5). G4 arm stretch p99 ≤ 1.86.
- Arms into the torso (`arm_torso_probe.py`, upper arms and forearms; the G6 test samples only forearms and hands): none
  above 1 cm except one lying frame of the death (left upper arm, frame 24). Before the review fix the thrust put the
  right upper arm and forearm up to 11.6 cm into the chest (frames 22-40).
- G6 (`g6_prop.py`, half frames, skin inside test, hit bone reported): Standing, Walking, Running, Hit, Fidget and Death
  clear of spear/arm penetration beyond the idle's own right-hand/thigh touch (≤ 1.4 cm). Known in the Attack: the fists
  graze the thighs during the first and last ~3 frames of the eased transitions (frames 1-4, up to 3.4 cm), the spear in
  the left fist touches the left thigh 5.0 cm at frame 34 of the return; the engine's 0.06-0.12 s crossfade covers the
  start). The dropped spear stays above the floor (-0.7 cm at worst).
- Feet flat (`foot_flat.py`): planted roll within 2.6° in Standing and Fidget, 5.4° at
  the attack wind-up (was 7-9° onto the outer edges); the walk's planted frames level, larger rolls only at toe-off.
  The roll correction is weighted to the flat-planted frames, capped at 20° and smoothed over the clip (second
  review: a frame-by-frame roll at heel strike and toe-off twitched the walking ankles up to 44° per 1/48 s); foot
  turn in Walking and Running ≤ 16.9° per 1/48 s, the source clips' own rate.
- Walk bob (`bob_smooth.py`, third review: the head went down, up, down around each heel strike, a 1-3 cm pelvis hitch
  already in the source walk): pelvis height low-passed over the cycle (harmonics ≤ 4), legs re-solved to the same feet
  (ankles within 4 mm); bob 7.0 → 6.4 cm, one smooth dip per step (`head_bob.py`).
- Soles: the lowest foot stays within -1.5..+1.7 cm in Standing, Walking, Attack (after its floor pass -0.3..+0.9),
  Hit and Fidget; Hit leaves both feet off the floor for two frames (8-9, a small hop from the source get-hit).
  Running and Death are airborne by design (run flight phase, the fall).
- Jerk: the right upper arm turns up to 36° per 1/48 s at the thrust itself (fast push; left arm 31°);
  no hand-roll flips (≤ 22°).
- Viewer: 24/24 tier/clip switches, no console errors; textured shots of every tier and clip inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m218_claude/export/mm7_m218.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m218_claude/export/mm7_m218_spear.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `Elf Spearman B` / `m218_b` and `Elf Spearman C` /
`m218_c`). Scale = native standing silhouette 184 px (SFT scale 1, leaf crown included) / 1.813 m:

```yaml
# MM7 Elf Spearman m218 (250-252): two-handed spear thrust, spear attachment on the world-keyed Spear node.
- descriptor: Elf Spearman A
  model: worlds/mm7/models/mm7_m218.glb
  scale: 101.49
  yaw_offset: -1.570796327
  skin: m218_a
  animation:
    run: Running
    stride_length: 1.779
    run_stride_length: 2.121
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 0.862}
      attack_ranged: {impact: 0.862}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  attachments:
  - model: worlds/mm7/models/mm7_m218_spear.glb
    node: Spear
```

Speeds: tier A walks at 240 units/s (the walk's natural 180 units/s: played 1.33x); B (260) and C (280) are above the
run threshold (2.4 × 101.49 = 244) and run at 0.89x / 0.96x. No in-game check was run.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; fists solved on the
unanimated weights inside the chain; `spear_clear.py` and a tracks-only `author_spear.py` pass follow the attack
assembly). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap, then HeadUV),
`uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m218.py`; then `scripts/build_runtime.sh`, `viewer_tiers.py`,
`update_viewer_manifest.py`. Gates: `g6_prop.py`, `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`,
`jerk_probe.py`, `probe_grips.py`, `probe_prop.py`, `probe_arm.py`, `stride.py`, `stand_height.py`.
