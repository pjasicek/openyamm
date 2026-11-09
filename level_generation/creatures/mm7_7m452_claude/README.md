# MM7 Peasant Goblin Male (`7m452`) — Claude humanoid route (batch J, 2026-10-20)

MM7 batch J model 5 ([BATCH_J.md](../mm7_batches/BATCH_J.md)). Scripts from `../mm7_m302_claude/` (source-frame rig,
mesh-measured hands, rule-based weights, solved fist around a one-handed prop) with the goblin lessons of
`../mm6_gob2_claude/` (arm clearance for the long arms, finger pieces by connectivity). **Not installed**: the
install commands and the `actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5
for joint estimates, body retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [viewer shots](review/shots_sheet.png) ·
[clay clips front](review/cl_front.png) / [left](review/cl_left.png) / [carry](review/cl_swf.png) ·
[textured looks](review/tex_sheet.png) · [billhook](review/billhook_sheet.png) · [gates](review/gates_final.txt) ·
[HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_7m452.glb` | body: one skinned mesh `Goblin`, 9 colour variants (`7m452_a1`…`7m452_c3`) on one merged body+head material (2080×1024 atlases), colour LODs 11,791 / 5,895 / 2,121 / 706 tris + shadow LODs, 6 clips |
| `export/mm7_7m452_billhook.glb` | rigid billhook attachment on node `Sword` (854 / 426 / 152 / 50 tris) |
| `export/mm7_7m452_lod0.glb` | full-detail portable export before LODs/split |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, body + head region masks, `7m452_ramps.json`, material class maps, billhook maps |

## Native identity and the nine looks

Native MM7 bitmaps `7m452*` (86 frames, `../mm7_7m452/`; the corpse frame is named `m452xa0`, without the `7`). An
orc-like MM7 goblin villager: tall and muscular, yellow-green skin, a bald head with a grey topknot, pointed ears, a
sleeveless red patterned tunic with grey fur trim, belt with a brass buckle, studded leather bracers, blue-grey striped
trousers, tall brown boots, and a billhook (long wooden shaft, hooked iron blade). Attack and shoot alias the walk.
The base art is palette 497 (descriptor 446, look `7m452_c2`).

All nine descriptors share the frames; three recolour regions (the skin never changes): **R tunic** (palette entries
185–255), **G trousers** (152–181), **B topknot** (135–150). Ramps are histogram-matched to the native pixels: stop
*i* (texel luminance lo + i/15·(hi − lo), the region's 2nd–98th percentile) takes each palette's mean colour around the
same quantile of the native pixels (palette 497 luminance order) × 1.35. (Equal-width rank windows rendered the
dark-skewed trousers near black.)

| Descriptor | Skin | Palette | Tunic / trousers |
|---|---|---:|---|
| 439 Peasant Goblin Male A A | `7m452_a1` | 453 | brown / olive |
| 440 A B | `7m452_a2` | 454 | white / black |
| 441 A C | `7m452_a3` | 455 | ochre / green |
| 442 B A | `7m452_b1` | 393 | black / black |
| 443 B B | `7m452_b2` | 493 | white / red |
| 444 B C | `7m452_b3` | 494 | purple / black |
| 445 C A | `7m452_c1` | 495 | black / brown |
| 446 C B | `7m452_c2` | 497 | red / blue-grey (HD masters) |
| 447 C C | `7m452_c3` | 498 | olive / olive |

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png` (1.8 m): 15.1k tris in 15 shells after removing a stray blob:
  torso+arms (one shell), head (topknot and ears in it), trousers, tunic skirt with belt, hands, boots, bracers,
  buckle, eyes, mouth, a neck bead.
- Joints (`joints_7m452.py`, m190's script): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at
  the hand shells' openings; ankles at the narrowest boot ring. Five fingers per hand by connectivity.
- Weights (`weights_fix.py`): skin, head, trousers, hands and boots on Meshy + shoulder fade + neck free of the
  shoulders; eyes and mouth rigid on the head; bracers copy the arm skin under them; buckle and bead rigid on the mean
  of the skin under them; tunic skirt pelvis → thighs per vertex (belt band on the pelvis). Reduced after weighting:
  15.1k → 11.8k (head and hands protected).
- Billhook (`make_billhook.py`): 1.4 m, a 10-sided lathe of the shaft and socket from `references_hd/billhook.png`
  (shaft radius = the fist's 2 cm handle) and the blade as a bevelled plate from the silhouette (cells dissolved);
  planar texture. Gripped 28 % up the shaft, the blade out of the thumb side (`club_frame.py`).

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 5.10 | Mixamo Unarmed Idle 01 (arms bowed out); authored carry: the billhook level at the right hip, blade forward |
| Walking | 1.17 | Mixamo Standard Walk; authored carry (0.3 of the arm swing) as the native walk; left arm cleared of the thigh |
| Hit | 0.50 | humanoid set Unarmed Get Hit F2: recoils back with the arms out (native `7m452na..ne`); billhook cleared |
| Death | 3.63 | Mixamo Standing React Death Backward: falls onto the back (native `7m452da..dd`); billhook kept, cleared of the floor; travel halved |
| Dead | 1.00 | last Death pose held |
| Fidget | 9.43 | Mixamo Weight Shift with the carry; left arm cleared of the thigh |

No attack (the native attack is the walk cycle) and no run: speed 140 units/s, below the run threshold (2.4 × scale =
259). The source arm swing drove the blade into the floor and through the legs; `author_carry.py` (`carry.json`:
wrist beside the right hip, the pole 6° out and 10° down in the pelvis frame) holds it level in Standing, Walking and
Fidget; Hit and Death keep their source arms with a 12° wrist cock (`wrist_tilt.py`).

## Gates (`review/gates_final.txt`)

- G5 hand stretch: right fist ≤ 2.73x, left hand ≤ 2.62x.
- G4 arm stretch p99 ≤ 1.64 (hit recoil).
- G6: no billhook, hand or forearm inside the body in Standing, Walking, Hit and Fidget; Death: the billhook touches the
  left thigh by 4.8 cm in one frame of the backward stride and the right hand the right thigh by 1.0 cm; the billhook's
  lowest point 2.3 cm above the floor.
- Head clearance: n/a (gob2's gate tests its pauldron shells; this goblin has no shoulder armour).
- Soles: grounded feet −1.9…+1.5 cm. Jerk: the source hit recoil is fast (spine 29° per 1/48 s); idle/walk smooth.
- Viewer: 54/54 look/clip switches, no console errors; textured viewer shots inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_7m452_claude/export/mm7_7m452.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_7m452_claude/export/mm7_7m452_billhook.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 193 px × sprite scale 1.0 /
model height 1.7905 m = **107.79** (every descriptor). Repeat for the other eight descriptors with their skins from
the table above and `scale_reference: Peasant Goblin Male A A`:

```yaml
# MM7 Peasant Goblin Male 7m452 (439-447): one body, nine palette looks; billhook attachment on node Sword; no attack.
- descriptor: Peasant Goblin Male A A
  model: worlds/mm7/models/mm7_7m452.glb
  scale: 107.79
  yaw_offset: -1.570796327
  skin: 7m452_a1
  animation:
    cast: Standing
    run: Walking
    stride_length: 2.028
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
  - model: worlds/mm7/models/mm7_7m452_billhook.glb
    node: Sword
```

The Standard Walk's natural 1.74 m/s × 107.79 = 187 units/s plays at 0.75x for the 140 units/s peasants. No in-game
check was run.

## Known limits / for user review

- One-handed billhook carry throughout; the native stands and fidgets holding it with both hands (raising it upright
  in the fidget).
- Death: one-frame billhook/thigh contact (4.8 cm) during the backward stride.
- The topknot is tiny in the native (2.3k pixels), so its ramps are approximate.
- LOD0 body is 11.8k (head and hands protected); a further cut on the torso/trousers is possible if needed.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; `work/source_rest.json`
copied from m302). Billhook once: `make_billhook.py`. Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`),
`transfer_uv.py` (UVMap, then HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_7m452.py`; then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `club_attach.py` + `g6_prop.py`
(PROP_HAND=R), `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`, `jerk_probe.py`, `stride.py`, `stand_height.py`.

## Walk and ankle fix (user review 2026-10-20)

Batch A's fixes (`mm7_m222_claude`), applied in the chain and replayed (STAGE=anim, then the runtime build and viewer):
- **Ankle twist:** `foot_level.py` updated to batch A's current rule: the walk takes one constant roll per foot in the
  foot's own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted);
  the other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved to
  the same ankle paths). Walk head height second difference 2.70 → 0.78 cm (batch A's fixed walk: 0.54); foot
  rotation step change per frame 8 → 10.5-11.3°.
- Viewer check 54/54, no console errors. Previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.

## Floor and death fix (user review 2026-10-20, after install)

- **Soles under the floor in Standing (−1.5…−1.9 cm):** Standing had no floor pass. `floor_const.py` (before
  `clip_timing.py`) gives it one constant pelvis lift (1.8 cm) that puts the median lowest sole on the floor; the one-shots
  blend from the corrected pose. Standing soles now −0.1…+0.1 cm.
- **Billhook through the left thigh in the death (4.8 cm):** the Mixamo Standing React Death Backward swung the fist
  across the body in its backward stride, and no wrist turn could clear the 1.4 m pole (a carried arm faded out over the
  fall pushed the forearm into the torso instead). The death is now the humanoid set's **Armed Death 1** (one-handed
  weapon kept at the side; staggers and falls onto the back, 1.07 s; `set_clips.txt`). `sword_clear.py` also gained
  options used for the death: `KEEP_GARMENTS` (the tunic skirt over the thighs), `PARITY` (ray-parity inside test),
  `ALLVERTS`/`GRIP` (sample every billhook vertex and the grip), `MAXANG`, `CONSIST` (one turn axis per contact span).
  G6 on the attached billhook: nothing inside the body in any clip, the billhook stays above the floor; the right hand
  no longer touches the right thigh (`arm_clear.py Death:R`).
- Runtime rebuilt; the reduced, installed model took the new clips with `../mm7_7m452_reduce_claude/scripts/transplant_clips.py`.
  Previous masters: `work/rig_v5_prefloorfix.blend`, `work/rig_v6_prefloorfix.blend`.
