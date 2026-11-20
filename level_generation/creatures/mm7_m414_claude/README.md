# MM7 Titan / Storm Titan / Blood Titan (`m414`) — Claude humanoid route (batch C, 2026-10-20)

MM7 batch C model 5 ([BATCH_C.md](../mm7_batches/BATCH_C.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, rule-based weights, solved fist); scripts from `../mm7_m190_claude/` (the one-handed weapon route
of `mm7_m222_claude`) with the hand/compose rules of `../mm7_m410_claude/`. **Not installed**: install commands and the
`actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body
retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [tier close-up](review/shots/tier_check.png) ·
[actions](review/shots/actions_sheet.png) · [clay clips](review/cl_tq.png) · [idle carry](review/st_sheet.png) ·
[gates](review/gates_final.txt) · [HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m414.glb` | body: one skinned mesh `Titan`, 3 tier variants (`m414_a/b/c`) on one merged body+head material (2080×1024 atlases), colour LODs 10,320 / 5,159 / 1,857 / 617 tris + shadow LODs, 8 clips |
| `export/mm7_m414_sword.glb` | short-sword attachment on node `Sword` (290 / 144 / 52 / 22 tris) |
| `export/mm7_m414_lod0.glb` | full-detail portable export before LODs/split (review viewer source) |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, region masks (tunic + crest, both sets), `m414_ramps.json`, class maps, sword maps |

## Native identity, tiers and height

Native MM7 bitmaps `m414*` (116 frames), tier palettes from the sprite frame tables (`7m415`, `m416`, `7m417`, sprite
scale **3.5**): **A Titan = 91** (dark blue tunic, white crest: the HD masters' colours), **B Storm Titan = 92** (olive,
orange crest), **C Blood Titan = 93** (red, pink crest). A giant classical warrior of grey stone: crested steel
helmet with gold trim, sleeveless blue scale tunic and skirt with gold-edged shoulders, gold lion belt, vambraces and
greaves with gold lightning bolts, gold sandals, a short sword in the right hand.

**Height check (requested):** binding scale = native standing silhouette 206 px × sprite scale 3.5 / 1.9275 m (the
idle's height, crest included) = **374.06**. In game: helmet top (crest excluded) **655 units**, within 1 % of the
descriptor height **650**; crest top 711–721 units (the native sprite's 206 × 3.5 = 721 includes the crest); head joint
571, shoulders 521. Measured from the model (`scripts/height_parts.py`, `stand_height.py`) with the binding scale; no
in-game run (optional in batch C).

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png`: 15,446 tris in 13 clean shells (torso with neck and face,
  both legs with greaves and sandals, both arms with vambraces and hands, three skirt tiers, belt, helmet dome, cheek
  and neck guard, crest, eyes); no cleanup needed.
- Joints (`joints_m414.py`): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at the narrowest arm
  ring within 3 cm of Meshy's (± 5 cm caught the left vambrace's edge and turned the left thumb 107°); ankles at the
  narrowest leg ring between 6 and 16 cm. Fingers fitted by connectivity (both hands within 37° of the source frame).
- Weights (`weights_fix.py`): skin = Meshy (+ shoulder fade, neck free of the shoulders); helmet, guards, crest and eyes
  rigid on the head; belt copies the skin without arm share; the three skirt tiers pelvis → thighs per vertex.
  Reduced after weighting: 15.45k → 10.32k.
- Sword (`make_sword.py`): 0.90 m leaf blade traced from `references_hd/sword.png` (diamond section), gold crossguard,
  1.6 cm grip (the solved fist), gold pommel; on the `Sword` bone at the solved right fist (export rule).

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 3.00 | Mixamo Standard Idle + authored carry: the fist in front of the right hip, blade forward-up across the thighs (native `m414sa`) |
| Walking | 1.00 | Mixamo Walk (1.85 m stride) + authored carry (user review 2026-10-20: the empty-hand swing turned the fist palm-up and swept the blade across the thighs): 0.8 of the swing kept, the palm against the hip (hand roll held within 45° of fingers-down, `psi=180`), the blade forward; floor pass |
| Running | 0.73 | Mixamo Standard Run fitted (2.06 m stride) + carry: the sword held up and forward at the side; loop seam spread over 6 frames |
| Attack | 1.63 | Mixamo Sword And Shield Slash (2): overhead raise, diagonal downward slash (native `m414aa..af`); planted + 20 % of its legs, 0.1 s ready pause, **blow at 0.783 s** (native action 0.75 s); sword cleared of the body |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1; blends 0.2 s |
| Death | 3.63 | Mixamo Standing React Death Backward (travel halved): falls onto the back (native `m414da..db`). **Deviation:** the native then crumbles into a rubble pile (`m414dc..dd`, corpse `m414xa`); not modelled — the corpse is the lying body |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.37 | Mixamo Sword And Shield Power Up (planted): sword swept up, chest out (native `m414fa..fe`) |

## Textures

Meshy body retexture (own UVs, copied back exactly) + head retexture (1K head set: the face above a level mid-neck cut
under the neck guard, helmet, guards, crest, eyes). `compose_m414.py`: stone skin of both sets repainted to one albedo
× Meshy's shading; AO grade; specular classes. Recolour regions: **R = tunic, skirt tiers, vambraces and greaves**
(native entries 144–213), **G = crest** (223–252); the head set has its own mask with the body's ramps. Ramps
rank-matched to the native pixels (m410 rule), × 1.35. Meshy painted a little blond hair under the helmet's cheek
guards (the native shows none).

## Gates (final rig, `review/gates_final.txt`)

- G6 (`axe_attach.py` + `g6_prop.py` with the modelled sword): no sword, forearm or hand inside the body in any clip;
  lowest sword point 2.9 cm above the floor in the death.
- G5 hand stretch ≤ 4.2x (Hit, left; source curl); right fist ≤ 2.53x. G4 arm stretch p99 ≤ 2.33.
- Soles: grounded feet −2.4…+1.5 cm (the idle's lowest sole sits 2.3 cm low).
- Feet flat (`foot_flat.py`): planted roll within 1.7° in Standing, Attack and Fidget (was 7-9° onto the outer
  edges; `foot_level.py` now also levels the sole roll while planted); the walk's planted frames level, larger rolls
  only at toe-off.
  The roll correction is weighted to the flat-planted frames, capped at 20° and smoothed over the clip (second
  review: a frame-by-frame roll at heel strike and toe-off twitched the walking ankles up to 44° per 1/48 s); foot
  turn in Walking and Running ≤ 16.8° per 1/48 s, the source clips' own rate.
- Walk bob (`bob_smooth.py`, third review: the head went down, up, down around each heel strike, a 1-3 cm pelvis hitch
  already in the source walk): pelvis height low-passed over the cycle (harmonics ≤ 4), legs re-solved to the same feet
  (ankles within 4 mm); bob 6.4 → 5.7 cm, one smooth dip per step (`head_bob.py`).
- Arms into the torso (`arm_torso_probe.py`): none above 1 cm in any clip.
- Jerk: the source slash's whip (right hand 51° per 1/48 s at 0.67 s) is kept, as for the Chain Fighter.
- Viewer: 24/24 tier/clip switches, no console errors; textured shots of every tier and clip inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m414_claude/export/mm7_m414.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m414_claude/export/mm7_m414_sword.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `Titan B` / `m414_b` and `Titan C` / `m414_c`):

```yaml
# MM7 Titan m414 (409-411): overhead sword slash, sword attachment on node Sword. Helmet top 655 units (descriptor 650).
- descriptor: Titan A
  model: worlds/mm7/models/mm7_m414.glb
  scale: 374.06
  yaw_offset: -1.570796327
  skin: m414_a
  animation:
    run: Running
    stride_length: 1.846
    run_stride_length: 2.056
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 0.783}
      attack_ranged: {impact: 0.783}
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
  - model: worlds/mm7/models/mm7_m414_sword.glb
    node: Sword
```

Speed 200 units/s (all tiers) is far below the run threshold (2.4 × 374.06 = 898): the Titan always walks, and the
walk's natural 1.85 m/s (690 units/s at this scale) plays at **0.29x** — a slow, heavy stride (see Known limits).
The titans also cast (Psychic Shock, Sparks); the native has no cast sprite (shoot = attack), so `attack_ranged` uses
the slash. No in-game check was run.

## Known limits / for user review

- The walk plays at 0.29x its natural speed (MM7's speed 200 on a 655-unit giant): it reads as slow and heavy. A
  shorter-stride walk would play faster but shuffle; your call.
- The native crumbling death and rubble corpse are not modelled.
- Meshy painted some blond hair under the helmet.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim). Sword once:
`make_sword.py` (Blender). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py`
(UVMap, then HeadUV), `uv_raster.py` (both, 1024), `bake_ao_natm.py`, `compose_m414.py`; then
`scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `axe_attach.py` (any held prop in
`work/props.blend`) + `g6_prop.py` (PROP_HAND=R), `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`,
`jerk_probe.py`, `stride.py`, `stand_height.py`, `height_parts.py`.
