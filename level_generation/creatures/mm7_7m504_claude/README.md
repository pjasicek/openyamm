# MM7 Chicken (7m504): zchicken a / b / c — Claude quadruped route on two legs, batch L

MM7 batch L model 6 ([BATCH_L.md](../mm7_batches/BATCH_L.md)). Monsters 466 Chicken A, 467 Chicken B, 468 Chicken C
(descriptors `zchicken a/b/c`, ambient farm animals). **Installed 2026-10-21** (the user asked for it after the batch;
the batch itself stopped at exports). Meshy: **15 of 100 credits** (Smart Topology 5, retexture 10). User artistic
acceptance is not recorded.

[Review viewer](review/viewer/index.html) (served at
`http://127.0.0.1:8912/level_generation/creatures/mm7_7m504_claude/review/viewer/`) ·
[HD masters](references_hd/selected_views_review.png) · [clay clips](review/clips_v1_three_quarter.png), [side](review/clips_v1_left.png)

| Item | Value |
|---|---|
| Runtime export | `export/mm7_7m504.glb`: one skinned mesh `M504`, one material, smooth-shaded (user review 2026-10-20: the first flat export showed every triangle), LODs **2,100** / 1,050 / 377 / 125 (LOD0 halved on the textured master by `halve_lod0.py` (user, 2026-10-20: "reduce tris now"; collapse before the armature, UV-seam vertices weighted 0.8, small pieces kept whole, the head, legs, paws/feet and tail protected (a face-only protection flattened the legs into blades))) tris + shadow LODs, 7 clips |
| Portable / editable | `export/mm7_7m504_lod0.glb`; `work/anim_v2u.blend` (rig, clips, UVs) |
| Textures | one atlas: 2K base colour, 1K normal / ORM, class map; head islands 2.5× (our Smart UVs) |
| Skeleton | 18 bones + `Socket_Mouth` (beak tip): Body, Chest, Neck1–2, Head, Tail1; per side Thigh, Shin, Tarsus, Foot, Wing1, Wing2 |
| Clips (30 fps) | Standing 2.0 s, Walking 0.433 s (stride 0.40 m), Attack 1.0 s (impact 0.5 s), Hit 0.5 s, Death 0.9 s, Dead 1.0 s, Fidget 1.6 s |

## Identity and tiers

Native `7m504*` (48 frames): a plump white hen with a small red comb and wattles, a yellow beak, pink-orange legs and a
short raised tail. **All three descriptors draw group m504 in palette 545** (no tint): one look, no colour variants and
no region mask; the binding has no `skin`. The native has only standing, a 7-frame walk (0.875 s) and a 3-frame death
(0.375 s); attack = walk, hit = fidget = stand.

## Route (the Cat's and Dog's, `../mm7_7m500_claude/`, `../mm7_m509_claude/`, with a bird rig)

1. HD masters (Codex, landscape), gated; Smart Topology 15k (one shell + 8 tail feather cards + 2 eyes + 5 flakes,
   dropped); `step1_clean.py` (`LENGTH=0.45`, 0.453 m tall).
2. `rig_chicken.py` (new): joints read off the shell's slices (a traced-leg measure failed on the short feathered legs):
   hock at the top of the bare shank (9 cm), knee and hip inside the feathers; the folded wing (the shell beyond
   |x| 7.5 cm at its height) on Wing1/Wing2 by an outward ramp; heat weights on a 6 mm voxel proxy (wing bones
   excluded), feet rigid below 1.5 cm by the nearer ankle–toe segment, feather cards rigid on Tail1, eyes on Head. The
   inner toe tips of both feet were fused at x = 0: the 14 bridge faces are deleted (tiny holes under the toes).
3. `anim_chicken.py` (new, on the cat's framework): knee shifted with the foot, Shin/Tarsus on two-bone IK with the
   hock bending back, Foot flat (toes curl in the swing). Walk: two cycles per native walk loop, 0.40 m per 0.433 s
   cycle with a head bob (the head holds still in the stance and thrusts forward); at the binding scale MM7's speed 140
   is 0.98 m/s, so the clip plays at 1.06×. One native cycle would need 0.85 m strides from a 45 cm hen. Peck attack;
   flinch with the wings flapping out; death: the wings flap open (≤ 45°, the wing is part of the shell) and it tips onto
   its side with the legs kicked out (native da–dc, corpse xa); fidget: two ground pecks.
4. `reduce_quad.py` (`SHELL_TRIS=3000 CLAW_MIN=9 CLAW_RATIO=0.5 EYE_RATIO=0.35`: "claws" = the eyes 9–10, "eyes" = the
   feather cards 1–8): **16,270 → 4,203**.
5. Smart UV (head 2.5×), Meshy retexture on our UVs, `compose_m504.py` (classes: eyes 6, legs and beak keratin 4, comb
   and wattles 3, feathers 2), `scripts/build_runtime.sh` (material extras only).

## Gates

- Halved LOD0 (`halve_lod0.py`, 2026-10-20), edge stretch p99: Standing 1.13, Walking 1.37, Attack 1.20, Hit 1.24, Death
  1.29, Fidget 1.26; floor -0.5-(-0.1) cm. Viewer, winding and textured renders rechecked.
- Edge stretch p99 / max (reduced mesh): Standing 1.12 / 1.29, Walking 1.23 / 2.42, Attack 1.19 / 1.41, Hit 1.23 /
  1.62, Death 1.25 / 1.88, Fidget 1.27 / 1.59.
- Floor: lowest point −0.1 cm standing (reduction), −0.4 cm in the corpse; the death's wing-flap hop lifts it 7 cm.
- `check_winding.py`: 0 inverted closed parts. Viewer: 7 clips, no console errors. Textured EEVEE frames (standing,
  head close-up, walk, death) inspected (`work/r_glb/`). Not checked in game (optional for batch L).

## Installed (2026-10-21, user request after the batch)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_7m504_claude/export/mm7_7m504.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `zchicken b` and `zchicken c`, identical):

```yaml
# MM7 Chicken 7m504 (466-468): ambient hen, brisk walk with head bob, peck attack, wing-flap death. One look (palette 545).
- descriptor: zchicken a
  model: worlds/mm7/models/mm7_7m504.glb
  scale: 143.5
  yaw_offset: -1.570796327
  animation:
    cast: Attack
    run: Walking
    stride_length: 0.40
    run_stride_length: 0.40
    upper_body_root: Chest
    look:
      nodes: [Neck2, Head]
      max_yaw_degrees: 60
      max_pitch_degrees: 25
    sockets:
      mouth: Socket_Mouth
    events:
      attack_melee: {impact: 0.5}
      attack_ranged: {impact: 0.5, release: mouth}
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Attack
    attack_ranged: Attack
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
```

Scale = native standing silhouette 65 px (`7m504sa2`, comb to toes, frame scale 1.0) / 0.453 m Standing height.

## For the user to review

- The walk runs two step cycles per native walk loop (a 45 cm hen cannot cover MM7's speed in one); the native walk
  timing is kept as the loop's period.
- The wings are part of the body shell: they lift and flap partly open (hit, death) but cannot spread fully as in the
  native death frames without separate wing geometry.
- Attack, hit and fidget are inventions (the native shows the walk or the standing frame).

## Gait rollout (2026-10-31, package q4)

**Run2** (hen run, duty 0.40, body leaning 12 deg, left foot down at 0 as Walking; 0.552 m in 0.30 s, authored 1.84) grafted onto the installed model by `../gait_rollout_20261031/q4/scripts/gait_m504.py` (executes `scripts/anim_chicken.py` up to its clip table on `work/anim_v2u.blend`). Binding: `run: Run2`, `run_stride_length: 0.552` for zchicken a-c (the run was Walking, played x2.12). Gate window: wander Walking x1.06, chase Run2 x1.06. Head bob 1.4 %, planted toe-out L +9.9 / R +2.6 as Walking.

Rebuild: `../gait_rollout_20261031/q4/README.md` (Rebuild). A far-LOD repair rerun (`lod_repair_claude`) or any rebuild of the installed GLB must re-graft these clips from `../gait_rollout_20261031/q4/work/m504_clips.glb` with `../claude_shared/graft_clips.py`. Rollback source: `../gait_rollout_20261031/q4/work/rollback/mm7_7m504.glb`.
