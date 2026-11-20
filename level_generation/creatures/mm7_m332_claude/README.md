# MM7 Peasant Elf Male (`m332`) — Claude humanoid route (batch J, 2026-10-20)

MM7 batch J model 3 ([BATCH_J.md](../mm7_batches/BATCH_J.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights), scripts adapted from `../mm7_m302_claude/` (the peasant dwarf, without the
club; both hands open). **Not installed**: the install command and the `actors.yml` binding are below. Meshy:
**30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10). User
artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [viewer shots](review/shots_sheet.png) ·
[clay clips front](review/cl_front.png) / [left](review/cl_left.png) · [walk](review/cl_walk.png) ·
[textured](review/tex_check.png) · [gates](review/gates_final.txt) · [HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m332.glb` | runtime: one skinned mesh `Elf`, 9 colour variants (`m332_a1`…`m332_c3`) on one merged body+head material (2080×1024 atlases), colour LODs 11,070 / 5,533 / 1,989 / 654 tris + shadow LODs, 6 clips |
| `export/mm7_m332_lod0.glb` | full-detail portable export before LODs |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, body + head region masks, `m332_ramps.json`, material class maps |

## Native identity and the nine looks

Native MM7 bitmaps `m332*` (84 frames, `../mm7_m332/`). Tall, muscular elf villager: blonde hair combed back into a
ponytail, pointed ears, a sleeveless brown leather vest laced over the bare chest with brass studs, leather wrist
bracers and an upper-arm band, a brass belt with a sheathed dagger on his right hip, tight burgundy hose, brown shoes.
Empty hands; attack and shoot alias the walk in the native descriptors.

One mesh covers the nine descriptors with two recolour regions: **R cloth** (palette entries 150–245: the tights) and
**G hair** (entries 107–146: the ponytail and the hair painted on the scalp). Ramps are rank-matched to the native pixels
(palette 59 luminance order) × 1.35; the tights use a fixed ±40 % luminance band around their median.

| Descriptor | Skin | Palette | Tights / hair |
|---|---|---:|---|
| 340 Peasant Elf MaleA A | `m332_a1` | 333 | green / black |
| 341 MaleA B | `m332_a2` | 334 | blue / ginger |
| 342 MaleA C | `m332_a3` | 59 | burgundy / blonde (HD masters) |
| 343 MaleB A | `m332_b1` | 60 | brown / grey |
| 344 MaleB B | `m332_b2` | 61 | grey / brown |
| 345 MaleB C | `m332_b3` | 62 | mustard / white |
| 346 MaleC A | `m332_c1` | 339 | charcoal / blonde |
| 347 MaleC B | `m332_c2` | 340 | cream / light brown |
| 348 MaleC C | `m332_c3` | 341 | white / dark grey |

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png` (1.75 m): 15.8k tris in 32 shells: one skin shell (body, head
  with the painted hair, shoes, bracers), vest, separate hands, ponytail, belt, buckle, dagger (4 parts), right
  upper-arm band, 9 studs, 8 lacing crosses, eyes.
- **Smart Topology gave each hand six digits** (as m190): `remove_finger.py` cuts the outermost (pinky-side) finger at
  its separation depth and caps it. `ponytail_fix.py` pulls the ponytail, which arced away from the back like a horn,
  toward the back with one smooth curve (the Meshy weight transfer keeps the original positions).
- Joints (`joints_m332.py`): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at the hand shells'
  openings; ankles at the narrowest leg ring. Five fingers fitted per hand by connectivity (`HAND_PIECES=2,3`).
- Weights (`weights_fix.py`): skin, vest and hands on Meshy's weights + shoulder fade and a free neck; vest arm share
  ≤ 0.3; eyes rigid on the head; ponytail copies the back skin without arm weight, mixed with `B_Head` (1 at the top →
  0.6 at the tip); studs and lacing on the mean of the vest weights under them; the arm band copies the arm skin; belt,
  buckle and dagger rigid on the pelvis. Reduced after weighting: 15.8k → 11.1k (head and hands protected).

## Clips (G1: `review/g1_sheet.png`)

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 5.10 | Mixamo Unarmed Idle 01: arms bowed out, wide stance (native `m332sa`) |
| Walking | 1.17 | Mixamo Standard Walk; foot levelling, floor pass |
| Hit | 0.50 | humanoid set Unarmed Get Hit F2, planted (its 45° fighting stance turned him to profile): recoils back with the arms flung out (native `m332na..ne`) |
| Death | 3.63 | Mixamo Standing React Death Backward: steps back, falls onto the back spread-eagled (native `m332da..xa`); travel halved |
| Dead | 1.00 | last Death pose held |
| Fidget | 9.43 | Mixamo Weight Shift (the native fidget barely moves) |

No attack (native attack = walk alias) and no run (speed 140 < the run threshold 205). Both thumbs keep half of the
source curl (`thumb_relax.py`, G5); `arm_clear.py` swings the arms out where the hands entered the thighs (walk, fidget,
death).

## Textures (`scripts/compose_m332.py`)

Body 1K + head 1K (head set: the skin shell above the jaw, the ponytail and the eyes). Body skin repainted to one albedo
× Meshy's shading; the neck seam (both sets painted a jagged vest-collar band) is flat skin feathered over 3 cm; the
tights are taken by position (legs between the shoe tops and the belt), flattened around their median and not AO-graded
(the narrow native ramp turned Meshy's dark seat patches and AO spots black); procedural eyes (Meshy painted the eye
shells skin-coloured).

## Gates (`review/gates_final.txt`)

- G5 hand stretch: right ≤ 3.83x, left ≤ 2.61x (right 5.3x before the thumb relax: a thumb vertex carries 0.16
  forearm-twist weight).
- G4 arm stretch p99 ≤ 1.58 (hit recoil).
- G6: no forearm or hand inside the body after `arm_clear.py` (3.2–3.6 cm before); only proximity hits on the belt and
  dagger shells.
- Soles: the left foot hovers 1.4–2.8 cm in Standing, Hit and Fidget (foot levelling left its heel up); the right foot
  sits on the floor; the walk reaches −2.8 cm.
- Jerk: the hit recoil's steps up to 41° per 1/48 s on the arms (the source snap); idle, walk and fidget smooth.
- Stride: `stride.py`'s planted-foot detection misfires on the hovering foot; measured directly 2.07 m per cycle.
- Viewer: 54/54 look/clip switches, no console errors; textured viewer shots inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m332_claude/export/mm7_m332.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 187 px × sprite scale
0.799988 / model height 1.7517 m = **85.40** (every descriptor). Repeat for the other eight descriptors with their skins
from the table above and `scale_reference: Peasant Elf MaleA A`:

```yaml
# MM7 Peasant Elf Male m332 (340-348): one body, nine palette looks; no weapon in hand, no attack.
- descriptor: Peasant Elf MaleA A
  model: worlds/mm7/models/mm7_m332.glb
  scale: 85.4
  yaw_offset: -1.570796327
  skin: m332_a1
  animation:
    cast: Standing
    run: Walking
    stride_length: 2.07
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
```

The walk's natural 1.77 m/s × 85.4 = 151 units/s plays at 0.93x for the 140 units/s peasants. No in-game check was run.

## Known limits / for user review

- The left foot hovers about 2 cm in the idle, hit and fidget.
- The ponytail still hangs a few cm off the upper back (it was a stiff arc in the Smart Topology return).
- The sixth finger was removed by script (a small capped stump on the outer knuckle).
- Hair is painted on the scalp shell (no hair geometry beyond the ponytail).
- The HD side/back views show an arm band on both arms; the mesh has one on the right (the left is painted).

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; `work/source_rest.json`
copied from m302). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap, then
HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m332.py`; then `scripts/build_runtime.sh`,
`viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `g6_prop.py` (PROP_HAND=X, no prop), `g5_hand_stretch.py`,
`g4_weights.py`, `sole_probe.py`, `jerk_probe.py`, `stride.py`, `stand_height.py`. Unused copied scripts (club, axe,
attack, run) remain for reference.

## Walk and ankle fix (user review 2026-10-20)

Batch A's fixes (`mm7_m222_claude`), applied in the chain and replayed (STAGE=anim, then the runtime build and viewer):
- **Ankle twist:** `foot_level.py` updated to batch A's current rule: the walk takes one constant roll per foot in the
  foot's own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted);
  the other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved to
  the same ankle paths). Walk head height second difference 2.71 → 0.77 cm (batch A's fixed walk: 0.54); foot
  rotation step change per frame 12-13 (after the ankle fix) → 10.6-11.6°.
- **Ankle joints:** `joints_m332.py` had fitted the ankles to 5 cm shoe-strap rings, the left 12 cm forward of the right, so the left foot hovered 1.4-2.8 cm and tilted 29°. The ankle ring must now be 15-45 cm (else Meshy's ankle): both 30 cm, symmetric. The rig and clips were rebuilt; the reduced mesh is unchanged (11,070 tris), so the texture chain was replayed from the stored Meshy results (UV transfer exact, no new jobs) and the earlier "left foot hovers" limit no longer applies.
- Viewer check 54/54, no console errors. Previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.
