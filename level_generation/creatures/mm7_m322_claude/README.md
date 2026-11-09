# MM7 Peasant Elf Female (`m322`) — Claude humanoid route (batch J, 2026-10-20)

MM7 batch J model 4 ([BATCH_J.md](../mm7_batches/BATCH_J.md)). Scripts from `../mm7_m302_claude/` (the peasant route:
source-frame rig, mesh-measured hands, rule-based weights, solved fist) with the staff in the LEFT fist and the Mage's
upright staff carry (`author_carry.py` and `armik.py` from `../mm7_m274_claude/`). **Not installed**: the install
commands and the `actors.yml` binding are below. Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint
estimates, body retexture 10, head retexture 10). User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root) · [viewer shots](review/shots_sheet.png) ·
[clay clips front](review/cl_front.png) / [left](review/cl_left.png) / [walk, hit, fidget](review/cl_w.png) ·
[textured](review/tex_sheet.png) · [gates](review/gates_final.txt) · [HD masters](references_hd/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m322.glb` | body: one skinned mesh `Elf`, 9 colour variants (`m322_a1`…`m322_c3`) on one merged body+head material (2080×1024 atlases), colour LODs 11,188 / 5,593 / 1,978 / 634 tris + shadow LODs, 6 clips |
| `export/mm7_m322_staff.glb` | rigid crooked wooden staff attachment on node `Sword` (1,160 / 580 / 208 / 68 tris) |
| `export/mm7_m322_lod0.glb` | full-detail portable export before LODs/split |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split) |
| `textures/` | body and head 1K sets, body + head region masks, `m322_ramps.json`, material class maps, staff maps |

## Native identity and the nine looks

Native MM7 bitmaps `m322*` (84 frames, `../mm7_m322/`). Tall slender elf woman: long straight red hair, pointed ears, a
short laced brown leather corset-vest over a bare midriff, bare arms with long brown bracers, green trousers laced at
the front and open-laced down the outer legs, brown ankle boots, a crooked wooden staff held upright in her LEFT hand
like a walking stick. Attack and shoot alias the walk; peasants flee.

All nine descriptors share the frames and differ only in palette: one mesh, rig and clip set with two recolour
regions, **R cloth** (palette entries 100–169: trousers) and **G hair** (entries 174–234, its dark magenta shades
included). Cloth ramps rank-matched to the native pixels; hair ramps histogram-matched (a linear rank map turned the
base red hair magenta, because the hair texels sit low in their luminance range). × 1.35.

| Descriptor | Skin | Palette | Trousers / hair |
|---|---|---:|---|
| 331 Peasant Elf FemaleA A | `m322_a1` | 323 | green / red (HD masters) |
| 332 FemaleA B | `m322_a2` | 324 | blue / black |
| 333 FemaleA C | `m322_a3` | 325 | red / auburn |
| 334 FemaleB A | `m322_b1` | 326 | pale green / blonde |
| 335 FemaleB B | `m322_b2` | 327 | black / white |
| 336 FemaleB C | `m322_b3` | 328 | brown / strawberry blonde |
| 337 FemaleC A | `m322_c1` | 329 | sky blue / red |
| 338 FemaleC B | `m322_c2` | 330 | green / black |
| 339 FemaleC C | `m322_c3` | 331 | coral / blonde |

## Model, rig and weights

- Smart Topology of `references_hd/00_three_quarter.png` (1.75 m): 15.9k tris in 50 shells; a 1-tri sliver removed.
  One skin shell P00 holds the body, head, vest, trousers, bracers and boots; separate hands (P02 right, P03 left),
  long hair P01, eyes, mouth bits, vest lacing and ~35 small studs/grommets.
- Joints (`joints_m322.py`, m190's script): Meshy for the axial joints, shoulders, hips, knees and elbows; wrists at the
  hand shells' openings; ankles at the narrowest leg ring of at least 15 cm perimeter (a 0.6 cm fold won without it).
  Five fingers fitted per hand by connectivity.
- Weights (`weights_fix.py`): skin on Meshy + shoulder fade + neck free of the shoulders; eyes and mouth rigid on the
  head; the hair copies the torso skin without arm/clavicle share, mixed with `B_Head` (1 at the top → 0.4 at the tips);
  lacing/studs/grommets rigid on the mean of the skin under them. Reduced after weighting: 15.9k → 11.2k.
- Staff (`make_staff.py`): 1.49 m (0.85 of her height as on `m322sa0`), a 10-sided lathe of the `references_hd/staff.png`
  silhouette, grip 70 % up from the butt; frame in the fist `staff_frame.py` (left hand).
- Fist: source grip from the Armed-Shield idle's left fist (the pistol idle put the index on the trigger), solved per
  finger round the 1.6 cm handle (`grip_solve.py SIDE=L`).

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 2.00 | humanoid set Relax Idle; staff carried upright in the left fist, butt on the floor (native `m322sa`) |
| Walking | 1.17 | Mixamo Standard Walk (user review 2026-10-20: the Relax Walk Female swayed the hips too much); staff kept upright in the world (`CARRY_FRAME=world`) |
| Hit | 0.50 | humanoid set Unarmed Get Hit F2: recoils back, the free arm out (native `m322na..ne`); staff upright with 20 % of the source wrist motion; floor-cleared |
| Death | 3.63 | Mixamo Standing React Death Backward: steps back, falls onto the back, staff in hand, cleared of the floor (native `m322da..xa`) |
| Dead | 1.00 | last Death pose held |
| Fidget | 9.43 | Mixamo Weight Shift (the native fidget barely moves); staff carried upright |

No attack (native attack = walk alias; bind to Standing) and no run (140 units/s is below the run threshold 209).
The world-up roll reference of m302's `armik.py` was degenerate for a near-vertical staff; the Mage's `armik.py` (skewed
reference) is used. `thumb_relax.py` keeps half of the source curl on the open right thumb.

## Gates (`review/gates_final.txt`)

- G5 hand stretch ≤ 1.94x (2.56x on the right hand in the death); G4 arm stretch p99 ≤ 1.31.
- G6: the staff touches the left thigh by 2.6 cm (hit) and the foot by 2.2–3.6 cm (death, fidget); its butt goes up
  to 5.8 cm into the floor in the death and 1 cm while standing; the right hand rests 2.6 cm into the thigh in the
  fidget (Weight Shift's hand on the hip/thigh). The hit's floor clearance left one frame unresolved.
- Soles −3.2…+2.4 cm; jerk: the hit recoil is fast (upper arm 49° per 1/48 s), idle/walk/fidget smooth.
- Stride ≈ 2.07 m (Standard Walk: planted-foot travel 1.78 m/s × 1.167 s cycle; walk fix 2026-10-20).
- Viewer: 54/54 look/clip switches, no console errors; textured viewer shots inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m322_claude/export/mm7_m322.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m322_claude/export/mm7_m322_staff.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml`. Scale = native standing silhouette 191 px × sprite scale
0.799988 / model height 1.7516 m = **87.23** (every descriptor). Repeat for the other eight descriptors with their
skins from the table above and `scale_reference: Peasant Elf FemaleA A`:

```yaml
# MM7 Peasant Elf Female m322 (331-339): one body, nine palette looks; staff attachment on node Sword; no attack.
- descriptor: Peasant Elf FemaleA A
  model: worlds/mm7/models/mm7_m322.glb
  scale: 87.23
  yaw_offset: -1.570796327
  skin: m322_a1
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
  attachments:
  - model: worlds/mm7/models/mm7_m322_staff.glb
    node: Sword
```

The Standard Walk's natural 1.78 m/s × 87.23 = 155 units/s plays at 0.9x for the 140 units/s peasants. No in-game check
was run.

## Known limits / for user review

- The staff glides with the hand in the walk (it is held upright, not planted step by step like a real walking stick).
- Small staff/floor and staff/leg contacts in the hit and death (Gates); the Weight Shift fidget is long (9.4 s).
- Some magenta in the hair shadows on the base look, as in the native palette.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; `work/source_rest.json`
copied from m302; `creature.json` holds the carry). Staff once: `make_staff.py`. Texture chain once:
`export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap, then HeadUV), `uv_raster.py` (both, 1024),
`bake_ao_natm.py`, `compose_m322.py`; then `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`.
Gates: `staff_attach.py` + `g6_prop.py` (PROP_HAND=L), `g5_hand_stretch.py`, `g4_weights.py`, `sole_probe.py`,
`jerk_probe.py`, `stand_height.py`. Unused scripts copied from m302/m190 (attack, run) remain for reference.

## Walk and ankle fix (user review 2026-10-20)

Batch A's fixes (`mm7_m222_claude`), applied in the chain and replayed (STAGE=anim, then the runtime build and viewer):
- **Ankle twist:** `foot_level.py` updated to batch A's current rule: the walk takes one constant roll per foot in the
  foot's own frame and one constant pelvis shift (the per-frame roll switched on and off as each foot landed and lifted);
  the other clips' roll is weighted by flatness, capped at 20° and smoothed.
- **Head zigzag:** `walk_bob.py` after `clip_timing.py` evens the walk's pelvis height (both steps alike, legs re-solved to
  the same ankle paths). Walk head height second difference 2.59 → 0.80 cm (batch A's fixed walk: 0.54); foot
  rotation step change per frame 19 → 10.3-11.8°.
- **Walk clip:** Mixamo Standard Walk replaces the humanoid set's Relax Walk Female (too much hip sway); 1.17 s.
- Viewer check 54/54, no console errors. Previous masters kept as `work/rig_v5_prewalkfix.blend` / `rig_v6_prewalkfix.blend`.
