# MM7 Bronze / Brass / Gold Golem (`m254`) — Claude humanoid route (batch I, 2026-10-20)

MM7 batch I model 5 ([BATCH_I.md](../mm7_batches/BATCH_I.md)). Shared Claude humanoid playbook (source-frame rig,
mesh-measured hands, connectivity fingers, rule-based weights), scripts from `../mm7_m414_claude/` (Titan) with the
unarmed clip timing of `../mm7_m470_claude/` (Ghoul) and the plant/face-forward rules of `../mm7_m290_claude/` (Monk).
**Not installed** (batch rule): the install command and the `actors.yml` binding are below. Meshy: **30 of 100
credits** (Smart Topology 5, auto-rig 5 for joint estimates and skin weights, body retexture 10, head retexture 10).
User artistic acceptance is not recorded.

[Review viewer](http://127.0.0.1:8912/level_generation/creatures/mm7_m254_claude/review/viewer/) ·
[tiers vs native](review/tiers_vs_native.png) · [tier shots](review/shots/tier_check.png) ·
[clip shots](review/shots/actions_sheet.png) · [clay clips front](review/clips_front.png) /
[side](review/clips_right.png) · [attack](review/attack_sheet.png) · [gates](review/gates_final.txt) ·
[HD masters](references_hd/selected_views_review.png) · [head masters](references_head/selected_views_review.png)

## Deliverables

| File | What |
|---|---|
| `export/mm7_m254.glb` | runtime: one skinned mesh `Golem`, 3 tier variants (`m254_a/b/c`) on one merged body+head material (2080x1024 atlases), colour LODs 10,051 / 5,024 / 1,808 / 598 tris + shadow LODs, 8 clips |
| `export/mm7_m254_lod0.glb` | full-detail portable export before LODs (review viewer source); `export/export_info.json`, `export/lods.json` |
| `work/rig_v6.blend` | editable textured master (rig, gated clips, Meshy UVs, head split); `work/rig_v5.blend` the gated chain |
| `textures/` | body and head 1K sets (base, normal, ORM: R spec mask, G roughness), region masks (both sets), `m254_ramps.json`, material class maps |
| `actors_m254_binding.yml` | the binding to add later (below) |

## Native identity, tiers and height

Native MM7 bitmaps `m254*` (120 frames, `mm7_m254/`), descriptors 277–279 `Golem A/B/C`, sprite groups m255/m256/m257,
palettes **A Bronze Golem = 255** (green stripes, the HD masters' colours), **B Brass Golem = 256**, **C Gold Golem =
257**, sprite scale 1.299988, hit material Metal. A living gold-bronze statue of a muscular pharaoh: green-striped nemes
with a striped crown (modius), two ivory horns, striped false beard, a dark broad collar with 24 gold studs, black
wrist and ankle cuffs, a striped shendyt (front apron, back panel, waist wrap) over dark briefs, bare metal feet.
The palettes recolour only the striped cloth, in **two families whose brightness order flips**: entries 151–198 (A dark
green, B light cyan, C tan) and 212–250 (A green, B deep blue, C red). Gold, collar, cuffs and horns do not change.

**Height:** binding scale = native standing silhouette 195 px x 1.299988 / 1.6646 m (Standing frame 0, horns
included; `stand_height.py`) = **152.29**: horn tips 253.5 units (descriptor height 215 is the collision height).

## Anatomy decisions

- **Skinned humanoid, not rigid plates.** Smart Topology returned one closed cast-metal skin (P00: torso, head, arms,
  hands with five separated fingers, legs, feet) with continuous sculpted musculature, plus separate garment shells. A
  rigid-piece rig ("each piece 100 % on one bone") would need cut joints the statue does not have, so the body deforms
  like a humanoid; the hard accessories are rigid (below). The golem's weight is in the motion (below), not in plates.
- **Pieces** (`step1_clean.py`, labels in `weights_fix.py`): skin P00; loincloth P01; collar P02; crown P03; nemes P04;
  belt P05; beard P06; horns P07/P08; ankle cuffs P09/P10; wrist cuffs P11/P12; horn sockets P13/P14; eyes P15/P16;
  24 collar studs P17–P40; ear studs P41/P42; nine 3–5-vertex slivers on the crown top (P43–P51) deleted.
- **Joints** (`joints_m254.py`): Meshy auto-rig for the axial joints, clavicles, shoulders, hips, knees and elbows; wrists
  at the narrowest skin ring within 3 cm of Meshy's, ankles at the narrowest leg ring 6–16 cm up (skin shell only; the
  cuffs are separate rings). Symmetry within 1.5 cm. Frame error 0.
- **Hands/fingers**: fingers by connectivity (`fit_fingers.py`). The thumbs leave the palm only 8 cm from the wrist, so
  the cut kept just their distal 3.5 cm and the source curl stretched the left thumb web to 5.7x: `thumb_fix.py`
  straightens each thumb chain and extends it 3.5 cm back into the palm (G5 now <= 4.35x). Hand vertex selection in
  `build_rig.py` is limited to the skin near the forearm axis (one skin shell: the thighs are near the hands).
- **Weights** (`weights_fix.py`): skin = Meshy + shoulder fade + neck/head free of the shoulders; crown, horns,
  sockets, beard, eyes, ear studs rigid `B_Head`; nemes head -> neck -> upper chest by height (no arm weight); belt
  copies the skin (no arm); collar copies the skin with the arm share capped at 0.35 and no neck/head share (the plate
  does not follow the head); studs rigid on the collar under them; cuffs rigid on the mean skin weights under them
  (they take the twist bones' share rigidly); loincloth wrap as the belt, the front apron pelvis -> 80 % thighs with ONE
  0.5 left/right mix, the wide back panel a gentle 0.25–0.75 mix. Twist bones (forearm 0.6, ramp 15–85 %).
  Reduced after weighting 15.6k -> 10.05k (head and hands protected; studs 1135 -> 480).
- **Heavy, stiff motion**: an upright walk with its pelvis bob low-passed (`bob_smooth.py`) and a floor pass, played
  at 0.62–0.70x of its natural speed by the game; the idle is Mixamo Orc Idle (very little secondary motion); the attack
  is planted (feet step at most 12 cm) with a deliberate overhead raise and a fast, accelerating smash that stops dead
  and holds 0.4 s before recovering.

## Clips (G1: candidates rendered on the mannequin before modelling, `review/g1_*`)

| Clip | s | Source and adaptation |
|---|---:|---|
| Standing | 5.33 | Mixamo Orc Idle: arms held out with bent elbows and clawed hands, slight forward lean (native `m254sa`); floor pass |
| Walking | 1.00 | Mixamo Walk (upright like `m254wa..wh`; Orc/Mutant walks stoop), pelvis bob low-passed, floor pass; stride 1.678 m |
| Running | 0.73 | Mixamo Standard Run fitted (2.115 m stride); never reached at the tier speeds |
| Attack | 1.83 | **Double-fist smash** (native `m254aa..ah`): no library clip raises both arms overhead and smashes both fists down (Mixamo "Standing Melee Attack Downward"/"Mutant Swiping" are one-armed, the 2H magic area attacks spread the arms to the floor, the set's axe chop 1 smashes into the floor). Body: set `2HandAxeAttack5` planted on Standing (`plant.py`, DROP 0.5) and faced front (`face_forward.py`); arms authored over it (`author_smash.py`): rise forward, both arms straight up with the fists together (0.57 s), an accelerating downswing well in front of the face, both fists side by side in front of the belly with the trunk 12 deg forward (blow **0.967 s**), held, recovered; 0.13 s ready pause, 20 % of the chop's legs with IK steps, eased to Standing |
| Hit | 0.50 | Humanoid set Unarmed get-hit front 1; blends 0.2 s; floor pass |
| Death | 3.63 | Mixamo Standing React Death Backward (travel halved): falls onto the back, legs up, then flat (native `m254na/nb`, `da..dd`) |
| Dead | 1.00 | last Death pose held (native corpse `m254xa`) |
| Fidget | 4.67 | Mixamo Mutant Flexing Muscles planted (20 % legs): the native flex with clenched fists (`m254fa..fe`) |

Timing: MM7 has no contact frame for `m255a`–`m257a` in `engine/rendering/sprite_attack_timing.yml`, so the game acts
when the 1.0 s native attack animation (8 x 125 ms) has played; the blow at 0.967 s needs a 1.03x fit. If a contact
frame is added later (the native fists land on frame `ae`, index 4 = 0.5 s), the wind-up would need a ~1.9x stretch:
then shorten the overhead hold and the ready pause (`SMASH` env of `author_smash.py`, `LEAD`). The monster table gives
the golems a 10–20 % "Arrow" missile (Attack 2) and no spell; `attack_ranged` uses the same smash.

## Textures (`scripts/compose_m254.py`)

Meshy body retexture (own UVs, copied back exactly by `transfer_uv.py`) + head retexture (1K head set: the face above a
level neck cut, crown, horns, beard, eyes, ear studs and the nemes, whose lappets and the beard cover the cut).
- Gold (skin, trims, studs): one albedo from the native gold pixels (mean below the 90 % luminance quantile, chroma of
  the light tones, x 1.4: sRGB 148,108,59) times Meshy's fine shading, mixed 0.85; AO graded.
- Region mask **R = dark-green stripes, G = light-green stripes** (body and head sets, same ramps): green cloth texels
  (plus green spill on the skin/collar) split by luminance against the masked local mean, crisp (the shader mixes the two
  channels one after the other, so soft splits left green showing through); padded, blurred 0.7.
- Ramps: each tier's native pixels of the family, rank-matched to the region texels, quantiles capped at 85 % (the
  top is baked highlight), gain 1.3 (dark family) / 1.0 (light family).
- ORM: R = per-class specular mask (gold 0.8, collar/cuffs 0.5, cloth 0.1, horns 0.35, eyes 0.8), G = roughness, B = 0;
  runtime extras `openyamm_specular=1`, `openyamm_specular_mask=true`, `pbr.metallicFactor=0` on Golem*.
- Class maps `textures/m254_material_classes.png`, `m254_head_material_classes.png` (9 metal, 8 cloth, 4 horn, 6 eye).

## Gates (final chain `work/rig_v5.blend`, `review/gates_final.txt`)

- G3: joints symmetric within 1.5 cm, frame error 0; hand frames within 25–40 deg of the source (thumbs after the fix).
- G4 arm stretch p99: Standing 1.2, Walking 1.2, Hit 1.7, Death 1.8, Fidget <= 2.3, Attack overhead <= 2.6 (the
  clavicle band under the collar at full shoulder flexion).
- G5 hand stretch max: <= 2.7x in every clip except Attack left 4.35x (thumb web while the fist closes at the raise).
- G6 contacts (closed skin inside test): Walking, Running, Hit, Death, Fidget 0; Standing left hand 1.6 cm on the thigh
  (one frame); Attack fists 2.0–2.1 cm into each other when clasped overhead, left forearm 0.8 cm.
- Arms into the torso (closed skin only): 0 in every clip except Attack left upper arm 2.9 cm against the neck while
  the arms are straight overhead (frames 19–22).
- Soles: grounded feet -0.7..+1.0 cm (Walking), -0.2..+0.2 (Attack), 0 (Standing), Hit -1.0..+1.3 (its stagger lifts
  both feet 1 cm for two half frames).
- Flat feet: planted roll <= 2.8 deg in Standing, Attack and Fidget; the walk's larger rolls are heel strike/toe-off
  (the probe counts every walk frame as planted at the golem's low foot clearance).
- Jerk: the smash's whip (right upper arm 46 deg per 1/48 s at the blow) is the intended impact; idle and walk <= 7 deg.
- Arm and hand gate: rig before poses (fingers inside the fingers, no upper-arm weight on chest/neck, collar copies
  the skin), fists from the source curl, key poses from the native frames as intent, targets in the chest heading frame,
  numbers on every frame (above), posture vs Standing (floor pass, planted feet), textured viewer shots of both hands and
  feet inspected.
- `g6_skirt_poke.py` reports 5.0 cm (its search cap) in every clip at single frames: an edge-flip artefact of the probe
  on the wrap's open border; the textured side and three-quarter walk shots show no thigh through the panels.
- Viewer: `run_creature_review.py check` 24/24 tier/clip switches, no console errors, failed []; winding check 0
  inverted closed parts.

## For the user to review

- The gold reads as warm bronze-gold in the viewer (no specular there); in game the 0.8 specular mask adds the sheen.
  If it should read brighter/yellower, raise `GOLD_GAIN` in `compose_m254.py` (1.4 now) and rebuild.
- The authored smash: the fists rise forward, meet overhead, and come down side by side in front of the belly; the
  set's guard stance shows as a small 12 cm step of each foot.
- Tier B/C stripe colours come from the native pixels (B cyan + deep blue, C tan + red); at distance the two stripe
  colours mix.
- Not checked in game (optional in batch I).

## Install later (not run)

**Reduced version:** [`../mm7_m254_reduce_claude/`](../mm7_m254_reduce_claude/README.md) (2026-10-20, 10,051 -> 8,043
triangles) — install its `export/mm7_m254.glb` instead of this one; the binding below is unchanged.

```sh
python3 tools/install_model.py level_generation/creatures/mm7_m254_claude/export/mm7_m254.glb --world mm7
```

Then add [actors_m254_binding.yml](actors_m254_binding.yml) (Golem A/B/C, skins `m254_a/b/c`) to
`assets_dev/worlds/mm7/models/actors.yml`:

```yaml
- descriptor: Golem A          # repeat for Golem B / m254_b and Golem C / m254_c
  model: worlds/mm7/models/mm7_m254.glb
  scale: 152.29
  yaw_offset: -1.570796327
  skin: m254_a
  animation:
    run: Running
    stride_length: 1.678
    run_stride_length: 2.115
    upper_body_root: B_Spine
    look: {nodes: [B_Neck, B_Head], max_yaw_degrees: 30, max_pitch_degrees: 20}
    events:
      attack_melee: {impact: 0.967}
      attack_ranged: {impact: 0.967}
  clips: {standing: Standing, walking: Walking, attack_melee: Attack, attack_ranged: Attack, hit: Hit,
          dying: Death, dead: Dead, fidget: Fidget}
```

Tier speeds 160/170/180 units/s stay under the run threshold (2.4 x 152.29 = 365): the golem always walks, at
0.62–0.70x of the walk's natural 1.68 m/s (256 units/s at this scale) — a slow, heavy stride.

## Replay

Claim the project, then `CREATURE_3D_TOKEN=<token> scripts/rebuild.sh` (STAGE=rig, then STAGE=anim; the anim stage
includes `author_smash.py`). Texture chain once: `export_uploads.py`, Meshy jobs (`requests/`), `transfer_uv.py
work/rig_v5h.blend meshy/retexture_v1 work/rig_v6.blend`, `uv_raster.py` (UVMap, HeadUV, 1024), `bake_ao_natm.py`,
`compose_m254.py`; then `scripts/build_runtime.sh`, `viewer_tiers.py`, `update_viewer_manifest.py`. Gates:
`scripts/gates.sh` (writes `review/gates_final.txt`). G1 probes: `mixamo_preview.py`, `rpg_preview.py`,
`set_hand_probe.py`, `mx_hand_probe.py`.

## Notes for shared tools (not changed, batch rule)

- `arm_torso_probe.py` and `g6_skirt_poke.py` (copied per project) count open shells (collar, nemes, loincloth) as
  "inside": the project copies here restrict the torso to the closed skin and the strip list to the loincloth. A shared
  version could read the closed-shell list from the garment labels.
- `run_creature_blender.sh` takes the project lock, so two Blender steps of one project cannot run at once.
