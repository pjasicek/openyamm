# MM7 Peasant Dwarf Male (`m302`) — Claude humanoid route (batch J, 2026-10-20)

MM7 batch J model 1 ([BATCH_J.md](../mm7_batches/BATCH_J.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights, solved fist), scripts adapted from `../mm7_m190_claude/` (the dwarf soldier:
same Dwarf Idle/Walk, one-handed prop in the right fist). **Not installed**: the install commands and the
`actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body
retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [viewer shots](review/shots_sheet.png) ·
[clay clips front](review/cl_front.png) / [left](review/cl_left.png) · [textured tiers](review/tex_sheet.png) ·
[gates](review/gates_final.txt) · [HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m302.glb` | body: one skinned mesh `Dwarf`, 9 colour variants (`m302_a1`…`m302_c3`) on one merged body+head material (2080×1024 atlases), colour LODs 10,429 / 5,213 / 1,875 / 623 tris + shadow LODs, 6 clips |
| `export/mm7_m302_club.glb` | rigid wooden club attachment on node `Sword` (1,104 / 552 / 198 / 66 tris) |
| `export/mm7_m302_lod0.glb` | full-detail portable export before LODs/split |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, body + head region masks, `m302_ramps.json`, material class maps, club maps |

## Native identity and the nine looks

Native MM7 bitmaps `m302*` (84 frames, `../mm7_m302/`). Stocky dwarf villager: green stocking cap with the tip hanging
at the back, long brown beard to the belt, green long-sleeved shirt under a brown leather vest with cream fleece trim,
leather bracers, belt with a round buckle, beige trousers, fleece boot cuffs, brown boots, a crude wooden club in the
right hand. Attack and shoot alias the walk in the native descriptors (no attack frames); peasants flee.

All nine descriptors share the frames and differ only in palette, so one mesh, rig and clip set covers them with two
recolour regions: **R cloth** (palette entries 160–248: cap and shirt) and **G hair** (entries 97–137: beard, nape hair
and the painted brows/moustache). Ramps are rank-matched to the native pixels: the region's pixels in the standing and
walking frames, ordered by palette-58 luminance; stop *i* takes each palette's mean colour in the *i*-th 16-quantile × 1.35.

| Descriptor | Skin | Palette | Cloth / hair |
|---|---|---:|---|
| 322 Peasant Dwarf MaleA A | `m302_a1` | 303 | purple / black |
| 323 MaleA B | `m302_a2` | 304 | blue / yellow |
| 324 MaleA C | `m302_a3` | 305 | pale blue / ginger |
| 325 MaleB A | `m302_b1` | 58 | green / brown (HD masters) |
| 326 MaleB B | `m302_b2` | 307 | wine / white |
| 327 MaleB C | `m302_b3` | 308 | brown / grey |
| 328 MaleC A | `m302_c1` | 309 | cream / black |
| 329 MaleC B | `m302_c2` | 310 | white / tan |
| 330 MaleC C | `m302_c3` | 311 | charcoal / yellow |

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png` (1.35 m): 16.1k tris in 19 shells; removed a ball on the cap
  brim and eight belt rivets (`step1_clean.py`). Kept: skin shell P00 (torso, arms, hands, face), vest, beard,
  trousers (belt included), cap, nape hair, boots, eyes.
- Joints (`joints_m302.py`): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at the narrowest arm
  ring near Meshy's wrist (the hands are part of the skin shell); ankles at the narrowest boot ring. Five fingers fitted
  per hand by connectivity (`fit_fingers.py`, `HAND_PIECES=0`).
- Weights (`weights_fix.py`): skin, vest, trousers and boots on Meshy's weights + shoulder fade + neck free of the
  shoulders; the vest's arm share capped at 0.3; cap and eyes rigid on the head; beard and nape hair copy the torso skin
  without arm/clavicle share, mixed with `B_Head` (1 at the top → 0.35 at the tip). Reduced after weighting per shell
  (`reduce_rigged.py`): 15.48k → 10.43k, head and hands protected.
- Club (`make_club.py`): 0.56 m, a 12-sided lathe of the `references_hd/club.png` silhouette, planar texture
  256 × 1024; frame in the fist: `club_frame.py` (head out of the thumb side).

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 6.67 | Mixamo Dwarf Idle (3): wide burly stance; the club hangs diagonally down to the knee as in `m302sa0..4` |
| Walking | 1.10 | Mixamo Dwarf Walk (short heavy steps, 1.35 m stride), club swinging with the arm; floor pass |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1: thrown back with the arms out (native `m302na..ne`); blends 0.2 s |
| Death | 3.63 | Mixamo Standing React Death Backward: steps back, falls onto the back (native `m302da..dd`); club kept in hand, cleared of the floor; travel halved |
| Dead | 1.00 | last Death pose held |
| Fidget | 4.43 | Mixamo Dwarf Idle (2): the left hand rises and strokes the beard (native `m302fa..fd`) |

No attack (native attack = walk alias) and no run: the speed is 140 units/s, below the run threshold
(2.4 × scale = 215). The source hammer grip held the club level; `wrist_tilt.py` cocks the right wrist 35° (ulnar
deviation) so it hangs like the native's (faded out over the death fall). `thumb_relax.py` keeps half of the source
curl on the open left thumb (G5). `sword_clear.py` (club surface sampled) and the floor rule clear the club.

## Gates (`review/gates_final.txt`)

- G5 hand stretch: right fist ≤ 2.04x; left hand ≤ 3.21x (4.4–4.8x before the thumb relax).
- G4 arm stretch p99 ≤ 1.71 (hit recoil).
- G6: no club in the body in any clip; the club's lowest point 0.8 cm above the floor in the death; hit: the club
  touches the left index by 0.5 cm in one frame; death: forearms 0.2–0.5 cm into the thighs on the ground; fidget: the
  left hand in the beard (intended).
- Soles: grounded feet −2.1…+1.3 cm (the idle's right sole sits 2 cm low throughout, as the m190 idle).
- Jerk: largest steps are the source hit recoil and death fall (head 18°, hand 26° per 1/48 s); idle/walk/fidget smooth.
- Viewer: 54/54 look/clip switches, no console errors; textured viewer shots inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m302_claude/export/mm7_m302.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m302_claude/export/mm7_m302_club.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 150 px × sprite scale
0.799988 / model height 1.3398 m = **89.57** (every descriptor). Repeat for the other eight descriptors with their
skins from the table above (`Peasant Dwarf MaleA B` → `m302_a2`, …, `Peasant Dwarf MaleC C` → `m302_c3`) and
`scale_reference: Peasant Dwarf MaleA A`:

```yaml
# MM7 Peasant Dwarf Male m302 (322-330): one body, nine palette looks; club attachment on node Sword; no attack.
- descriptor: Peasant Dwarf MaleA A
  model: worlds/mm7/models/mm7_m302.glb
  scale: 89.57
  yaw_offset: -1.570796327
  skin: m302_a1
  animation:
    cast: Standing
    run: Walking
    stride_length: 1.348
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
  clips:
    standing: Standing
    walking: Walking
    attack_melee: Standing
    attack_ranged: Standing
    hit: Hit
    dying: Death
    dead: Dead
    fidget: Fidget
  attachments:
  - model: worlds/mm7/models/mm7_m302_club.glb
    node: Sword
```

The Dwarf Walk's natural 1.23 m/s × 89.57 = 110 units/s plays at 1.27x for the 140 units/s peasants. No in-game check
was run.

## Known limits / for user review

- The face has no modelled moustache (the beard starts below the mouth); brows stay brown in every look.
- Attack binds to Standing (as the accepted MM6 peasant rebuild): the native attack is the walk cycle.
- Colours were fitted to the native palettes, not checked in game lighting.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; `work/source_rest.json`
is the humanoid set's rest, copied from m190). Club once: `make_club.py`. Texture chain once: `export_uploads.py`, Meshy
jobs (`requests/`), `transfer_uv.py` (UVMap, then HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`,
`compose_m302.py`; then `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Gates:
`club_attach.py` + `g6_prop.py` (PROP_HAND=R), `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`, `jerk_probe.py`,
`stride.py`, `stand_height.py`. Unused scripts copied from m190 (attack, run, axe) remain for reference.

## Walk and ankle fix (user review 2026-10-20)

Batch A's fixes (`mm7_m222_claude`), applied in the chain and replayed (STAGE=anim, then the runtime build and viewer):
- **Ankle twist:** `foot_level.py` updated to batch A's current rule: the walk takes one constant roll per foot in the
  foot's own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted);
  the other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved to
  the same ankle paths). Walk head height second difference 1.92 → 0.56 cm (batch A's fixed walk: 0.54); foot
  rotation step change per frame 19-22 → 10.8-11.4°.
- Viewer check 54/54, no console errors. Previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.
