# MM7 Elven Archer / Elven Scout / Elven Ranger (`m214`) — Claude humanoid route (batch C, 2026-10-20)

MM7 batch C model 1 ([BATCH_C.md](../mm7_batches/BATCH_C.md)). Built with the shared Claude humanoid playbook
(source-frame rig, mesh-measured hands, rule-based weights, solved left bow fist). **Not installed**: everything stays
in this project until the user decides; the install commands and the `actors.yml` binding are below.
Meshy: **30 of 100 credits** (Smart Topology 5, auto-rig 5 for joint estimates, body retexture 10, head retexture 10).
User artistic acceptance is not recorded.

[Review viewer](review/viewer/index.html) (serve the repository root, e.g. port 8912) ·
[tier shots](review/shots/tiers_sheet.png) · [actions](review/shots/actions_sheet.png) ·
[full draw close-ups](review/shots/draw_zoom.png) · [gates](review/gates_final.txt)

## Deliverables (`export/`)

| File | What |
|---|---|
| `mm7_m214.glb` | body: one skinned mesh `Elf`, 3 tier variants (`m214_a/b/c`) on one merged body+head material (2080×1024 atlases), colour LODs 8,037 / 4,008 / 1,427 / 455 tris + shadow LODs, 8 clips, `Socket_Arrow_Release` |
| `mm7_m214_bow.glb` | rigid bow attachment on node `Bow` (1,328 / 664 / 238 / 78 tris) |
| `mm7_m214_arrow.glb` | rigid nocked-arrow attachment on node `Arrow` (36 tris; node scale 0 = hidden) |
| `mm7_m214.blend` | editable master (rig, textured mesh with props and string, clips), images packed |
| `mm7_m214_lod0.glb` | full-detail portable export before LODs/split (review viewer source) |

## Native identity and tiers

Native MM7 bitmaps `m214*` (120 frames) decoded with the real tier palettes from the sprite frame tables
(`engine/rendering/sprite_frames/monsters/m215-217.yml`): **A Elven Archer = 215** (olive garments, blond hair), **B
Elven Scout = 216** (green, silver; the HD masters' colours), **C Elven Ranger = 217** (red, auburn).
`references_native/` has the sheets. Female elf, short silver hair, pointed ears, green sleeveless vest with ivory
piping and two waist straps, cropped trousers with calf lacing, bare feet, bracer on the left (bow) forearm (copied to
the right forearm too, at the user's request), quiver across the back with the fletchings over the right shoulder,
recurve bow in the left hand.

HD masters (Codex, `references_hd/`, `references_head/`, prompts and hashes in `generation_runs.json`): five body views,
bow reference, four head views. Gated against the native views (identity, sides, quiver/bracer/pouch sides, digits).

## Model, rig and weights

- Smart Topology of `00_three_quarter.png` (14,653 tris, 48 shells: the arm is three shells — sleeve-like upper arm in
  the vest piece, forearm, hand). Joints (`joints_m214.py`): Meshy's auto-rig for the axial joints, shoulders, hips,
  knees and elbows (t ≈ 0.50, centred on the arm section), wrists at the hand shells' openings, ankles at the
  narrowest shin ring. Fingers fitted by connectivity (5 per hand), source-frame rig (52 bones + twist + props).
- Weights (`weights_fix.py`): skin shells keep Meshy's weights (+ shoulder fade, neck free of the shoulders); hair,
  eyes rigid head; quiver and its arrows rigid `B_Spine2`; straps and lacing copy the skin under them; pouches rigid
  on the skin mean. Reduction after weighting with head and hands protected: body 14.65k -> 7.87k (+ bow, arrow, string).
- Bow (`make_bow.py`): limbs traced from the HD bow reference, 1.15 m, 15.5 cm brace height; held in the solved left
  fist (`grip_solve.py` SIDE=L, 14 mm grip, from the humanoid set's 2Hand-Bow idle), rolled 15.9° in the hand so the
  full-draw anchor lies in the bow plane. String: skinned tube in the body (`Bow` ends, `StringNock` middle) drawing a
  white swatch of the body texture. Arrow: a separate rigid prop.

## Clips

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 4.87 | Mixamo longbow-pack "unarmed idle 01"; authored bow carry (`author_carry.py` SIDE=L): grip beside the hip, bow forward-down along the side (native m214sa) |
| Walking | 1.00 | Mixamo "Walk" (1.855 m stride); the bow arm holds the idle's arm beside the body (`arm_hold.py`: world orientation of the idle's arm, ±6° swing against the right arm); floor pass |
| Running | 0.73 | Mixamo Standard Run fitted (`run_fit.py`, 2.13 m stride); carry held forward and out (never used in game: tiers walk 160-180 units/s, below the run threshold) |
| Attack | 1.77 | Mixamo "Standing Draw Arrow" + "Standing Aim Recoil" (`author_bow.py`): reach over the right shoulder into the quiver (arrow appears at 0.33 s), carry it over the shoulder, nock (0.57 s), raise and draw 65 cm to the face, **release at 1.100 s** (arrow hidden, string snaps back), lower; eased from/to Standing; the source's 0.9 m bow stance narrowed to 40 % and the pelvis raised 85 % of its drop; the right elbow turned up to 20° out of the neck at the quiver reach (`elbow_clear.py`, frames 9–11) |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1 + carry; blends 0.12 / 0.20 s; floor pass |
| Death | 3.00 | Mixamo longbow-pack "standing death backward 01", travel halved, floor pass: falls onto the back (native m214da..dd) |
| Dead | 1.00 | last Death pose held |
| Fidget | 2.47 | authored over Standing: the bow raised across the front (upper tip toward the chest, lower tip down and out), held, lowered (native m214fa..fe) |

The native attack is 18 raw ticks = 1.125 s with no contact frame (the game acts when it ends); the clip's release at
1.10 s sits within 2 % of it.

User review 2026-10-20: the walk tucked the bow arm against the body (now held as in the idle); the feet stood on
their outer edges (`foot_level.py` now also levels the sole roll while planted: batch A's rule, the run roll only).

## Textures

Meshy body retexture (own UVs, copied back exactly: 0 mm face mismatch) + head retexture (1K head set: head skin
above a level neck cut, hair, eyes). `compose_m214.py`: one skin albedo (median of both sets) × Meshy's fine shading,
AO grade, specular classes in ORM red, material class maps. Region mask: **R = green garments**, **G = hair** (plus
the grey-painted scalp under the hair mesh). Ramps rank-matched to the native sprite pixels of each region (palette
indices 104-171 cloth, 62-103 hair in the head area; only entries that differ between the tier palettes), × 1.35.
Meshy painted the tooled leather bracer on the left forearm only; `bracer_map.py` + `bracer_apply.py` (after
`compose_m214.py`) copy it onto the right forearm through the mirrored rest geometry (base colour, ORM, region mask,
classes; normals turned through the mirror frame; second review 2026-10-20).

## Gates (final export, `review/gates_final.txt`)

- G5 hand stretch: left fist 4.22x in every clip (solved grip), right ≤ 3.69x (limit ~4.5).
- G4 arm stretch p99 ≤ 1.97 at the extremes (full draw, quiver reach, hit, run, death).
- Arms into the torso (`arm_torso_probe.py`, upper arms and forearms): none above 1 cm in any clip.
- G6 (`g6_bow.py`, half frames, skin inside test): bow, string, arrow and both arms clear of the skin in Standing,
  Walking, Running, Hit and Fidget. Known: Attack frame 15 (0.5 s) the right hand passes through the upper bow limb
  for about two frames while bringing the arrow forward (source hand path); frame 11 the arrow grazes the hair 1.8 cm
  as it leaves the quiver; Death frame 45 the bow touches the left shin 0.9 cm. The bow never goes below the floor.
- Soles: grounded feet within -1.5..+0.5 cm in every clip (Walking -0.4..+0.5).
- Feet flat (`foot_flat.py`, sole plane of the planted foot): roll within 1.6° in Standing, Attack and Fidget (was
  5-6° onto the outer edges); the walk's planted frames level, larger rolls only at toe-off.
  The roll correction is weighted to the flat-planted frames, capped at 20° and smoothed over the clip (second
  review: a frame-by-frame roll at heel strike and toe-off twitched the walking ankles up to 44° per 1/48 s); foot
  turn in Walking and Running ≤ 17.5° per 1/48 s, the source clips' own rate.
- Walk bob (`bob_smooth.py`, third review: the head went down, up, down around each heel strike, a 1-3 cm pelvis hitch
  already in the source walk): pelvis height low-passed over the cycle (harmonics ≤ 4), legs re-solved to the same feet
  (ankles within 4 mm); bob 7.4 → 7.3 cm, one smooth dip per step (`head_bob.py`).
- Viewer: 24/24 tier/clip switches, no console errors; textured shots of every tier and clip inspected.

## Install later (not done)

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m214_claude/export/mm7_m214.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m214_claude/export/mm7_m214_bow.glb --world mm7
python3 tools/install_model.py level_generation/creatures/mm7_m214_claude/export/mm7_m214_arrow.glb --world mm7
```

Binding for `assets_dev/worlds/mm7/models/actors.yml` (repeat for `Elf Archer B` / `skin: m214_b` and
`Elf Archer C` / `skin: m214_c`). Scale = native standing silhouette 207 px (SFT scale 1) / 1.7316 m standing height:

```yaml
# MM7 Elf Archer m214 (247-249): bow and nocked-arrow attachments, arrows launch from Socket_Arrow_Release.
- descriptor: Elf Archer A
  model: worlds/mm7/models/mm7_m214.glb
  scale: 119.54
  yaw_offset: -1.570796327
  skin: m214_a
  animation:
    sockets:
      arrow_release: Socket_Arrow_Release
    run: Running
    stride_length: 1.855
    run_stride_length: 2.13
    upper_body_root: B_Spine
    look:
      nodes: [B_Neck, B_Head]
      max_yaw_degrees: 45
      max_pitch_degrees: 25
    events:
      attack_melee: {impact: 1.1}
      attack_ranged: {impact: 1.1, release: arrow_release}
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
  - model: worlds/mm7/models/mm7_m214_bow.glb
    node: Bow
  - model: worlds/mm7/models/mm7_m214_arrow.glb
    node: Arrow
```

No in-game check was run (optional for the batch; several batch sessions share the machine).

## Replay

Claim the project (`tools/creature_workspace.py`), then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh`
(STAGE=rig, then STAGE=anim; the left grip is solved on the unanimated weights inside the chain). Texture chain once:
`export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py` (UVMap, then HeadUV), `uv_raster.py` (both layers,
1024), `bake_ao_natm.py`, `compose_m214.py`, `bracer_map.py` (Blender) + `bracer_apply.py`; then
`scripts/build_runtime.sh` (syncs the clips from `work/rig_v5.blend`
into `work/rig_v6.blend`), `viewer_tiers.py`, `update_viewer_manifest.py`. Gates: `g6_bow.py`, `g5_hand_stretch.py`,
`g4_weights.py`, `sole_probe.py`, `jerk_probe.py`, `probe_bow.py`, `stride.py`, `stand_height.py`.
Do not regenerate the head unwrap casually: it is the correspondence contract of the paid head texture.
