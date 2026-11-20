# MM7 Dwarven Soldier / Lieutenant / Commander (`m190`) — Claude humanoid route (batch C, 2026-10-20)

MM7 batch C model 3 ([BATCH_C.md](../mm7_batches/BATCH_C.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights, solved fist). The scripts combine `../mm7_m222_claude/` (one-handed weapon route:
overhead chop, sword clearance, timing) with `../mm7_m218_claude/` (side-aware grip scripts, gates).
**Not installed**: the install commands and the `actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart
Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10). User artistic acceptance is not
recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [tier close-up](review/shots/tier_check.png) ·
[actions](review/shots/actions_sheet.png) · [clay clips](review/cl_tq.png) · [gates](review/gates_final.txt) ·
[HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m190.glb` | body: one skinned mesh `Dwarf`, 3 tier variants (`m190_a/b/c`) on one merged body+head material (2080×1024 atlases), colour LODs 10,027 / 5,013 / 1,803 / 598 tris + shadow LODs, 8 clips |
| `export/mm7_m190_axe.glb` | rigid double-bitted axe attachment on node `Sword` (1,016 / 508 / 182 / 60 tris) |
| `export/mm7_m190_lod0.glb` | full-detail portable export before LODs/split (review viewer source) |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, region mask, `m190_ramps.json`, material class maps, axe maps |

## Native identity and tiers

Native MM7 bitmaps `m190*` (124 frames), tier palettes from the sprite frame tables (`m191-193`): **A Dwarven Soldier =
191** (dark green cloth, the HD masters' colours), **B Dwarven Lieutenant = 192** (blue-violet), **C Dwarven Commander =
193** (red). Stocky dwarf: horned steel helmet with a gold rim and top spike, long braided ginger beard, sleeveless mail
shirt with steel shoulder guards, green collar, brown belt, mail skirt over a ragged green skirt, leather bracers with
gold rims, bare thighs, steel boots; a double-bitted axe in the right hand. The native descriptors also scale the
sprites per tier (1.0 / 1.05 / 1.10), so each tier gets its own model scale below.

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png`: 15,940 tris in 29 shells; three 1–4-triangle slivers removed.
  Torso/head/beard/hair/collar are one shell (P00); separate hands, bare upper arms, bracers, legs, mail skirt, ragged
  skirt, boots, helmet, horns, braids, shoulder guards, buckle, eyes.
- **Smart Topology gave each hand six digits** (thumb + five fingers; the masters show four). `remove_finger.py` cuts the
  shortest, outermost finger at its separation depth, caps the stump and relaxes the cap ring (a small flat facet stays
  on the outer knuckle). Remaining fingers 17.9 / 19.5 / 18.5 / 16.9 cm (index → pinky).
- Joints (`joints_m190.py`): Meshy for the axial joints, shoulders, hips, knees and elbows (t ≈ 0.47–0.49, centred on
  the arm + bracer section); wrists at the hand shells' openings; ankles at the narrowest boot ring. Fingers fitted by
  connectivity (`fit_fingers.py`, with a five-digit fallback for the thumb).
- Weights (`weights_fix.py`): skin = Meshy (+ shoulder fade, neck free of the shoulders, **the beard free of the arms
  and clavicles**); helmet, horns and eyes rigid on the head; braids copy the beard without arm share; bracers copy the
  arm and hand skin (the rim follows the wrist; rigid bracers opened a gap at the hand); shoulder guards copy the skin;
  both skirts pelvis → thighs per vertex, blended into a copy of the skin under them where they lie on the body (full
  copy within 1.5 cm, the rule from 5 cm on; user review 2026-10-20: the hip skin poked through the mail in the walk).
  Reduced after weighting: 15.76k → 10.03k body triangles. `sync_weights.py` carries the weights into the textured
  master (`rig_v6.blend`; same mesh vertex for vertex).
- Axe (`make_axe.py`): 0.70 m, traced from `references_hd/axe.png`: 8-sided haft at the fist's 1.6 cm radius (gold
  bands wider), pommel ball, top spike, two crescent blades as wedges 1.2 cm → 0.2 cm thick; planar texture 512 × 1024.
  Its frame in the fist is `axe_frame.py` (export rule, blade plane 90° from the knuckle line).

## Clips (G1: `review/g1_sheet.png`)

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 6.67 | Mixamo Dwarf Idle (3): wide burly stance; the axe hangs head-down by the knee like `m190sa0` |
| Walking | 1.10 | Mixamo Dwarf Walk (short heavy steps, 1.19 m stride), axe swinging with the arm; floor pass |
| Running | 0.73 | Mixamo Standard Run fitted (2.54 m stride) + authored carry (`carry.json`: axe up and forward at the side, the source arm swung the haft through the chest); loop seam spread over 6 frames (`loop_close.py`) |
| Attack | 1.80 | Mixamo Sword And Shield Slash (2): overhead raise, downward chop into a crouch (native `m190aa..ah`); planted + 20 % of its legs, 0.3 s ready pause, **blow at 0.983 s** (native action 1.0 s; the game acts at its end); axe blades and the left hand cleared of the legs |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1; blends 0.2 s; axe cleared |
| Death | 3.63 | Mixamo Standing React Death Backward: steps back and falls onto the back (native `m190da..dd`); axe kept in the fist, cleared of the floor. (Falling Back Death rolled this short body over its head.) |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.37 | Mixamo Sword And Shield Power Up (planted): axe swept up, chest out; axe cleared of the helmet |

`sword_clear.py` samples the haft and the blade outline (and the floor for the death) and turns the hand ≤ 45°;
`arm_clear.py` (from m406) swings the upper arm out where a hand would enter the thighs.

## Textures

Meshy body retexture (own UVs, copied back exactly) + head retexture (1K head set: the face above the head joint, helmet,
horns, eyes, braids and **the whole beard**, so the beard has no seam). `compose_m190.py`: body skin (the bare arm,
hand and leg shells only; Meshy painted the thighs green) repainted to one albedo × Meshy's fine shading; the head keeps
Meshy's colour; AO grade; specular classes (steel, gold, leather, cloth, beard, horn, skin; gold restricted to the
helmet and horns on the head set because the ginger beard shares its hue). One recolour region (R): the green collar
and the ragged skirt. Ramps: each tier palette's saturated entries among the native cloth pixels (indices 199–233),
sorted by luminance, × 1.35 (the darkest eighth dropped).

## Gates (final rig, `review/gates_final.txt`)

- G5 hand stretch: right fist ≤ 3.59x, left ≤ 4.45x (the thumb's swing and curl capped at 30°, `THUMB_MAX`: the
  thumb leaves the palm only 8 cm up this hand and a full wrap tore the thumb–index web, 8.6x).
- G4 arm stretch p99 ≤ 2.22.
- Skirts (`skirt_poke.py`, skin vertices under the mail P07 / ragged skirt P03 at rest that come out in front of it):
  Walking ≤ 0.2 cm (was 3.5 cm), Standing, Attack and Fidget ≤ 0.1 cm, Hit 0.8 cm, Running 1.3 cm (was 6 cm; every
  tier walks in game).
- Feet flat (`foot_flat.py`): planted roll within 2.1° in Standing, Attack and Fidget (was 6-10° onto the outer edges);
  the walk's planted frames level, larger rolls only at heel strike and toe-off.
  The roll correction is weighted to the flat-planted frames, capped at 20° and smoothed over the clip (second
  review: a frame-by-frame roll at heel strike and toe-off twitched the walking ankles up to 44° per 1/48 s); foot
  turn in Walking and Running ≤ 17.2° per 1/48 s, the source clips' own rate.
- Walk bob (`bob_smooth.py`, third review: the head went down, up, down around each heel strike, a 1-3 cm pelvis hitch
  already in the source walk): pelvis height low-passed over the cycle (harmonics ≤ 4), legs re-solved to the same feet
  (ankles within 4 mm); bob 5.9 → 5.0 cm, one smooth dip per step (`head_bob.py`).
- G6 (`g6_prop.py` on `axe_attach.py`'s copy with the modelled axe): no axe, forearm or hand inside the body in
  Standing, Walking, Running, Hit, Death and Fidget; Attack: the axe touches the left hand by 0.7 cm at frame 43 of the
  recovery. Lowest axe point 2.6 cm above the floor in the death.
- Soles: grounded feet within −2.5…+1.5 cm (the idle's soles sit 1.6 cm low throughout).
- Jerk: the source attack's overhead whip (right hand 50° per 1/48 s at the blow) is kept; the run's arm ≤ 18°.
- Viewer: 24/24 tier/clip switches, no console errors; textured tier and action shots inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m190_claude/export/mm7_m190.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m190_claude/export/mm7_m190_axe.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 150 px (horns included) ×
the tier's sprite scale / 1.433 m: **A 104.69, B 109.92, C 115.16**. Repeat for `Dwarf B` (`m190_b`, scale 109.92)
and `Dwarf C` (`m190_c`, scale 115.16):

```yaml
# MM7 Dwarf m190 (229-231): overhead axe chop, axe attachment on node Sword.
- descriptor: Dwarf A
  model: worlds/mm7/models/mm7_m190.glb
  scale: 104.69
  yaw_offset: -1.570796327
  skin: m190_a
  animation:
    run: Running
    stride_length: 1.185
    run_stride_length: 2.542
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 0.983}
      attack_ranged: {impact: 0.983}
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
  - model: worlds/mm7/models/mm7_m190_axe.glb
    node: Sword
```

Speeds 160 / 180 / 200 units/s are below the run threshold (2.4 × scale = 251 / 264 / 276), so every tier walks; the
Dwarf Walk's natural 1.08 m/s plays at 1.42x / 1.52x / 1.61x. No in-game check was run.

## Known limits / for user review

- The sixth finger was removed by script; the outer knuckle keeps a small flat facet.
- The fist is a loose hook around the haft (thumb capped at 30°); the axe covers it at game distance.
- All tiers walk at 1.4–1.6x the Dwarf Walk's natural speed.
- A little chest mail beside the lower beard is in the head texture set (painted by the head retexture).

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim). Axe once:
`make_axe.py` (Blender). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap,
then HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m190.py`; then `scripts/build_runtime.sh`,
`viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `axe_attach.py` + `g6_prop.py` (PROP_HAND=R),
`g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`, `jerk_probe.py`, `stride.py`, `stand_height.py`.
