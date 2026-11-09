# MM7 Thief / Rogue / Master Thief (`m410`) — Claude humanoid route (batch C, 2026-10-20)

MM7 batch C model 4 ([BATCH_C.md](../mm7_batches/BATCH_C.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights, solved fist); scripts from `../mm7_m190_claude/` (and through it
`mm7_m222_claude`, `mm7_m218_claude`). **Not installed**: install commands and the `actors.yml` binding are below.
Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10).
User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [tier close-up](review/shots/tier_check.png) ·
[actions](review/shots/actions_sheet.png) · [clay clips](review/cl_tq.png) · [draw close-ups](review/draw_sheet.png) ·
[gates](review/gates_final.txt) · [HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m410.glb` | body: one skinned mesh `Thief`, 3 tier variants (`m410_a/b/c`) on one merged body+head material (2080×1024 atlases), colour LODs 11,282 / 5,639 / 2,029 / 675 tris + shadow LODs, 8 clips |
| `export/mm7_m410_dagger.glb` | dagger attachment on node `Dagger` (282 / 140 / 50 / 23 tris) |
| `export/mm7_m410_lod0.glb` | full-detail portable export before LODs/split (review viewer source) |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split, Dagger bone) |
| `textures/` | body and head 1K sets, region masks (body: vest + trousers; head: cap), `m410_ramps.json`, class maps, dagger maps |

## Native identity and tiers

Native MM7 bitmaps `m410*` (124 frames), tier palettes from the sprite frame tables (`7m411`, `m412`, `7m413`):
**A Thief = 84** (purple vest and cap, green trousers: the HD masters' colours), **B Rogue = 85** (green, brown-orange),
**C Master Thief = 86** (red, dark red). Lean human thief: knitted cap, red face mask, studded quilted vest with padded
shoulder caps, bare arms with gold bangles (left) and a leather band (right), belt with a coin pouch (right hip) and a
dagger sheath (left hip), leather trousers, tall laced boots. The native stands empty-handed; the attack draws the
dagger, strikes and sheathes it again.

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png`: 101 shells; `step1_clean.py` removes 81 shells of ≤ 36
  triangles (vest studs, boot-lace bits, belt rivets: painted by the texture), the head and mask spikes running onto the
  chest (vertices below 1.43 m), the pouch's 20 cm spike (above 1.10 m, capped) and three sliver faces → 12,787 tris.
  The torso shell carries the arms and hands.
- Joints (`joints_m410.py`): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at the narrowest arm
  ring within 5 cm of Meshy's; ankles at the narrowest boot ring between 7 and 15 cm. Fingers fitted by connectivity.
- Weights (`weights_fix.py`): skin = Meshy (+ shoulder fade, neck free of the shoulders); cap and eyes rigid on the head;
  belt, strap, buckle and mask copy the skin without arm share; pouch rigid; wrist band and bangles copy the arm/hand;
  shoulder caps copy the skin; **sheath 0.75 pelvis / 0.25 left thigh** (a pelvis-rigid sheath went into the running
  thigh). Reduced after weighting: 12.79k → 11.28k.
- Spikes (third review): a 23 cm sliver from the mask across the chest to the right upper arm and shards off the
  mask that the cut missed; `despike.py` moves the six spike tips back onto the surface (rest positions only: the
  same mesh, UVs, weights and textures), on the gated rig in the chain and once on the textured master.
- Dagger (`make_dagger.py`): 0.35 m from `references_hd/dagger.png`: diamond-section blade, crossguard, 1.4 cm grip (the
  solved fist), pommel.

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 3.00 | Mixamo Standard Idle, hands empty, dagger in the sheath; arms swung clear of the thighs (`arm_clear.py`) |
| Walking | 1.00 | Mixamo Walk (1.86 m stride); floor pass |
| Running | 0.73 | Mixamo Standard Run fitted (2.02 m stride) |
| Attack | 1.67 | **Authored** (`author_dagger.py`, native `m410aa..ah..aa`): the right wrist is solved onto the hilt in the left-hip sheath (cross-draw, elbow forward), the dagger leaves the sheath at 0.33 s; the body blends into the humanoid set's Dagger-Attack R3 (raised wind-up, forward lunging thrust; lunge narrowed and raised, arms smoothed at the thrust), **blow at 0.862 s** (native ag/ah ≈ 0.875 s); the recovery plays 1.5x; the hand returns to the sheath and lets go at 1.37 s; floor pass |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1; blends 0.2 s; arms cleared |
| Death | 2.20 | Mixamo Falling Back Death (travel halved): thrown back, legs up (native `m410da..dd`) |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.00 | Mixamo Shrugging (planted): arms out to the sides (native `m410fa..fd`) |

The `Dagger` bone (child of `B_Pelvis`) is keyed in every clip: in the sheath (following the sheath's deformed vertices
by a rigid best fit) and in the right fist from the draw to the sheathing; the solved fist is weighted in only then.

## Textures

Meshy body retexture (own UVs, copied back; 6 faces Meshy altered differ by ≤ 9 mm) + head retexture (1K head set: the
head shell, cap, mask, eyes). `compose_m410.py`: skin of both sets repainted to one albedo × Meshy's shading; AO grade;
specular classes. Recolour regions: **R = vest, shoulder caps and cap** (native entries 147–245), **G = trousers**
(81–137); the head set has its own mask (the cap) with the body's ramps. Ramps: each tier's colours of the region's
native pixels, sorted by luminance and **rank-matched to the texels** (evenly spaced stops turned the dark trousers
black), × 1.35.
Texture repair (user review 2026-10-20: angular light/dark patches on the bare arms and the trousers). Causes found
by unlit, lighting-only and flat-colour renders (`scripts/glb_close.py`, `EMIT=1` / `WHITE=1`): 18k arm texels failed
the skin colour test (Meshy's warm highlights read as gold, pale ones as metal) and kept Meshy's raw paint with a
gold/metal shine; the rest-pose AO baked on the low-poly mesh has per-triangle steps; and the UV-space blurs of the
skin repaint and of the patch evening reached into unrelated islands packed beside each other in this fragmented
atlas. `compose_m410.py` now forces the bare arms and hands to skin by bone, paints the body skin flat (one albedo, no
Meshy shading; the face keeps its detail), averages the AO over the 3D surface (1.5 cm), evens the vest and trousers
in 3D (local luminance over 0.6 cm replaced by its 2.5 cm average) and gives skin and trousers the class roughness
alone. `frame_raster.py` + `smooth_skin_normals.py` (after the compose) write a 3 cm smoothed normal field into the
arm skin of the normal map, so the large arm triangles light as one rounded surface.
Second review (same day): a skin triangle still stuck out of the vest at the right biceps, a fold left beside a
moved spike tip; `despike.py` now also relaxes folded faces within two rings of the moved tips (unfold stage), writes
the moved vertices to `work/despike_moved.json`, and `moved_raster.py` + `repaint_moved.py 0.04` (after
`smooth_skin_normals.py`) repaint the reshaped faces from the surrounding surface (they still carried stretched trim
paint, a gold smear on the arm).

## Gates (final rig, `review/gates_final.txt`)

- G5 hand stretch ≤ 3.99x (Hit, right); G4 arm stretch p99 ≤ 2.45.
- G6 (`dagger_attach.py` + `g6_prop.py`): Standing, Walking, Hit and Fidget clean (≤ 0.3 cm). Running: the sheathed
  dagger touches the forward-swinging left thigh by 2.3 cm (frame 0.5). Death: the sheathed dagger is 3.9 cm into the
  bent left thigh while lying (frame 48). **Attack: at the draw (frames 8.5–10) and the sheathing (~39–41) the right
  hand and forearm press up to 5 cm into the belly/belt** — the hilt sits within a fist's thickness of the belt
  (the cross-draw itself is solved with the elbow forward; the default solver range put the forearm through the torso).
- Soles: grounded feet −2.1…+1.3 cm (the idle's lowest sole sits 1.8 cm low; the attack is floored to it).
- Feet flat (`foot_flat.py`): planted roll within 2.3° in Standing, Attack and Fidget (one attack frame 9.3°) (was 7-10°
  onto the outer edges; user review 2026-10-20, `foot_level.py` now also levels the sole roll while planted); the walk's
  planted frames level, larger rolls only at toe-off. The roll correction is weighted to the flat-planted frames, capped
  at 20° and smoothed over the clip (second review: a frame-by-frame roll at heel strike and toe-off twitched the
  walking ankles up to 44° per 1/48 s); foot turn in Walking and Running ≤ 16.9° per 1/48 s, the source clips' own rate.
- Walk bob (`bob_smooth.py`, third review: the head went down, up, down around each heel strike, a 1-3 cm pelvis hitch
  already in the source walk): pelvis height low-passed over the cycle (harmonics ≤ 4), legs re-solved to the same feet
  (ankles within 4 mm); bob 7.0 → 6.2 cm, one smooth dip per step (`head_bob.py`).
- Jerk: the source's thrust (a smooth bell, smoothed to ≤ 67° per 1/48 s) at the blow.
- Viewer: 24/24 tier/clip switches, no console errors; textured shots of every tier and clip inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m410_claude/export/mm7_m410.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m410_claude/export/mm7_m410_dagger.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `Thief B` / `m410_b` and `Thief C` / `m410_c`).
Scale = native standing silhouette 186 px × the sprite frame scale 1.1 (all three tiers, `m410.yml`/`m412.yml`) / 1.822 m:

```yaml
# MM7 Thief m410 (406-408): dagger drawn from the left-hip sheath, lunging thrust; dagger attachment on node Dagger.
- descriptor: Thief A
  model: worlds/mm7/models/mm7_m410.glb
  scale: 112.30
  yaw_offset: -1.570796327
  skin: m410_a
  animation:
    run: Running
    stride_length: 1.863
    run_stride_length: 2.018
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
  - model: worlds/mm7/models/mm7_m410_dagger.glb
    node: Dagger
```

Speeds 250 / 260 / 270 units/s against the run threshold 2.4 × 112.30 = 269.5: tiers A and B walk (the walk's natural
1.86 m/s = 209 units/s plays at 1.20x / 1.24x), tier C runs (natural 2.75 m/s = 309 units/s, played at 0.87x). No
in-game check was run.

## Known limits / for user review

- The hand and forearm touch the belt for about two frames at the draw and the sheathing (see G6).
- The sheathed dagger touches the left thigh in the run (2.3 cm) and in the lying death (3.9 cm).
- Tier C (270 units/s) sits just above the run threshold (269.5) and runs; A and B walk.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim). Dagger once:
`make_dagger.py` (Blender). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py`
(UVMap, then HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m410.py`; then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `dagger_attach.py` + `g6_prop.py`
(PROP_HAND=R), `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`, `jerk_probe.py`, `stride.py`, `stand_height.py`;
`probe_dagger.py` prints the dagger track.
