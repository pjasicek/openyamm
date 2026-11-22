# Xeen's Guard (Xeen Construct D, row 11603), Claude project, 2026-11-21

Lane S sub-agent build (parent `xeen-s7`, owner `xeen-s7-guard`, identity `xeen:guard`, Meshy limit 30 credits).
Decision D-19. Row 11603 "Xeen's Guard", level 60, melee only (Energy), ground walker (`fly: N`), descriptor height
160 / radius 90. Clouds of Xeen image 62 (`sprites/xeen/062.mon`, `062.att`): a headless chrome-silver plated brute,
an egg dome with a red seam and a round red gem where the head would be, clawed hands, cyan hip tubes, black briefs,
ribbed knee rings and black boots; its attack fires a green beam from the gem.
Built with the [humanoid playbook](../CLAUDE_HUMANOID_NPC_PLAYBOOK.md) (arm and hand gate, feet and floor rules),
the quadruped playbook's "Rigid hard-surface creatures" (one bone per plate), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the review viewer and in game (static model
spawns in XD-21). The binding is **not** merged (the parent owns `actors.yml`): the ready block for `Xeen Construct D`
is [integration/actors.yml](integration/actors.yml). Not accepted by the user. **Meshy: 15 of 30 credits.**

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_guard.glb` (sha256 `b9ad0ca4…`) | installed source = `export/xeen_guard.glb`; cooked runtime copy in `assets_dev/worlds/xeen/models/` (`55ec3df7…`) |
| `integration/actors.yml` | the binding for `Xeen Construct D` (skin `guard_a`, scale 84.5, impact 1.033 s, gem glow) |
| `work/anim_v1.blend` | keyed master (rig `Guard_Rig`, mesh `Guard`); `work/rig_uv.blend` is the locked UV layout, `rig_v1.blend` the rig, `seg_v1.blend` the plates, `clean_v1.blend` the cleaned Meshy mesh |
| `references_hd/` | five Codex masters (1024x1536, two runs), `CODEX_BRIEF.md`, `generation_runs.json`, `codex_run1/2.log`, `selected_views_review.png` |
| `native/` | original frames `mon_0000`, `mon_0003`, `att_0000..0003`; `sheet_standing_front.png`, `sheet_attack.png` (Codex inputs, 4x hard pixels) |
| `textures/` | `guard_basecolor_graded.png` (2K), `guard_normal_1k`, `guard_mr_1k` (R AO, G roughness, B 0), `guard_region_mask.png` (R chrome, G red, B cyan, A black), `guard_ramps.json`, `guard_emission_mask.png` (gem), `guard_material_classes.png`, `guard_ao_2k.png` |
| `review/` | `textured_sheet.png` + `textured_*.png` (EEVEE at party eye height: front, quarter, side, wind-up, blow, walk, run, hit, corpse, gem/hands/feet close-ups, back), `clips_quarter.png`, `clips_side.png` (clay, plates coloured by bone), `raw_*.png`, `clean_*.png`, `seg_*.png`, `rig_*.png`, `uv_quality_upload.json`, `texture_quality.json`, `viewer_shots.png`, `shots/`, `ingame/` |
| `review/viewer/` | review viewer: `xeen_guard_a.glb` (ramps baked for three.js, gem emission), every clip |

## Mesh: rigid plates

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 16,300 triangles, 20 pieces (body shell,
separate hands with long wrist cuffs, dome, gem, soles, hip tubes, chest rivets) with needle strips from the right
hand to the right knee and between the knees and holes in the right shin. `scripts/clean.py`: 1.90 m tall, needles
(aspect > 10, edge > 6 cm) and slivers deleted, **symmetrized +X -> -X** (the creature's left half was clean; the red
forearm band is paint), rivets dropped (paint), fins removed, holes refilled.

`scripts/segment.py` (cut planes in `scripts/joints.json`) bisects the shell into **one plate per bone** along clean
planar cuts at the creases (boot top, knee-ring top, the briefs' leg opening, the waist band's edges, the shoulder
plane, the pauldron's lower edge, the elbow), splits the hands' cuffs onto the forearms, caps every cut, decimates per
plate and adds dark joint spheres (waist x2, hips, knees, ankles, elbows, shoulders) sized to stay inside the shell.
The deltoid ball is a **pauldron on the clavicle**: the upper arm turns under it (a deltoid on the upper arm showed its
flat cut face when the arm rose). **11,642 triangles** (shell 6.2k, hands 1.7k, dome 0.8k, joint spheres 1.2k, caps
0.9k). Face attributes `bone` and `part` (0 shell, 1 gem, 2 joint sphere, 3 cut cap, 4 hand, 5 dome, 6 tube, 7 sole).

## Rig

`scripts/rig.py`: `Guard_Rig` with the stand-in mm8_m592's `B_*` names (Pelvis, Spine, Spine1, Spine2, Neck, Head;
Clavicle, UpperArm, Forearm, Hand, Thigh, Calf, Foot per side) on our joints, all bones unconnected; `Socket_Gem`
(child of `B_Head`) 1.5 cm in front of the gem. Rigid weights: every vertex 100 % on its plate's bone (0 vertices on two
bones, 0 unweighted). Fingers are part of the hand plate (the claws stay spread, as on the sprite).

## Clips (retargeted from the stand-in mm8_m592, `scripts/retarget.py`, 30 fps)

Reference pose S0 = the source's Standing frame 0. Every bone takes the source's world rotation change since S0 on top
of our standing posture (`W = D(t) Q R`): the trunk pitched forward 14 degrees (hunch), the dome (B_Head) and the
clavicles with half the source's own motion, our A-pose arms (hands forward of the hips, claws spread, as the sprite
holds them; matching the source's long hanging arms pushed our big hands far out). Pelvis and feet move by K = 1.14 x
the source's displacement (0.9 horizontally, 0.81 in the walk, 0.5 in the death); legs are two-bone IK to the feet
with a forward-and-out knee pole (bowed knees as on the sprite); a pelvis drop where a leg cannot reach (5-frame
minimum, blurred, wrapped on loops); one foot always on the floor in walks and idles; the death hands the legs to
plain FK on our wide stance and eases the hunch out as it falls (the source's narrow stance crossed our boots).

| Clip | Source | Length | Notes |
|---|---|---|---|
| Standing | Standing | 2.0 s loop | dome top 1.834 m (1.832-1.835) |
| Walking | Walk2 | 0.7 s loop | stride **0.71 m** per cycle (planted-foot speed x cycle), pelvis 2-10 cm lower than standing |
| Running | Jog | 0.63 s loop | stride **1.18 m**; a suspension phase (14 of 20 frames both feet up to 5 cm) |
| Attack | Attack | 1.5 s | claws raised over the dome (0.6 s), slammed down at the party: **impact 1.033 s** (hands' centre at 95 % of its 1.02 m drop, 0.67 m in front) |
| Hit | Hit | 0.5 s | recoil |
| Death | Death | 1.3 s | staggers back, falls on its back (travel halved), corpse on the floor |
| Dead | Death's last pose | 1.0 s | |
| Fidget | Fidget | 0.63 s | |

No Cast / missile (melee only): `cast` and `attack_ranged` = Attack. No Sprint (a heavy construct).

### Gates (`scripts/gates.py` on the master, `scripts/clip_gates.py` on the export)

Arm and hand gate, every clip: contacts (deepest point of a hand, forearm or upper arm inside the closed trunk,
thigh, calf or dome plate, and leg against leg; ray parity) **<= 1.13 cm** (Running: upper arm into the chest; all
other clips <= 1.0 cm); wrist swing (hand against forearm from the bind relation) **<= 22.2 deg**; forearm twist
**<= 5.0 deg**, largest step 3.5 deg; soles: Standing/Attack/Hit/Fidget at 0, Walking never without a foot down.
Motion (largest per-frame vertex step / second difference, cm at 30 fps; source mm8_m592 at the same rate in brackets):

| Clip | Step | Accel | Seam | Lowest (units) |
|---|---|---|---|---|
| Standing | 0.06 (0.1) | 0.01 | 0.00 | -0.01 |
| Walking | 21.4 (12.5) | 13.5 (12.0) | 0.00 | 0.00 |
| Running | 20.5 (16.4) | 13.7 (18.3) | 0.00 | 0.00 |
| Attack | 63.7 (102.7) | 52.1 (154) | | -0.01 |
| Hit | 9.1 (15.6) | 7.5 (17.2) | | -0.01 |
| Death | 33.4 (26.7) | 16.5 (24.2) | | -0.03 |
| Fidget | 1.8 (3.4) | 0.6 (2.3) | | -0.01 |

The walk's larger step is the swing foot at heel strike (bigger boots, K 1.14); its jerk matches the source's.
Floor audit (`floor_audit.audit` with this binding block on the installed GLB): **ground, standing -0.01, walking
0.0..0.0, living lowest -0.01, corpse 0.0 world units, no problems.**

## Textures

UVs (`scripts/uv.py`, `uv_atlas.unwrap` defaults: PartUV charts, seam pass, sparrow; `cut_closed`, `weld=0` so the
plates' coincident cut vertices stay apart, the dome 1.4x denser): **no fallback**. Meshy `retexture_v1` (meshy-7, 4K,
PBR, original UVs; views 01, 03, 02, 04) returned the same layout. Quality (`texture_quality.py export/xeen_guard.glb`):
**atlas 74.2 %, density p10/p50/p90 964/1044/1152 (spread 1.20), 175 islands, fragments 0.5 %, stretch p90 1.22.**

`scripts/compose.py`: colour 4K -> 2K once (Lanczos); classes from the paint's hue limited by plate part: red (seam,
stripes, forearm band, boot stripes), cyan (tubes wholly, waist ring), green rivets and palm dots (kept, no region),
black (boots, briefs, waist band, knee rings, soles; the knee rings' smeared upper rim forced dark), chrome (the rest,
x1.25: paint median 0.50 against the sprite's 0.55, sprites carry baked shading); joint spheres and cut caps dark
gunmetal (Meshy painted them white where its views saw through the gaps); the gem a procedural ruby lit by its
normal. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5 --contrast 1.06 --saturation 1.15`), `gutter_fill.py`
last on every map. Roughness: chrome 0.25-0.5, black 0.3-0.55, cyan 0.2-0.4, gem 0.12; metallic 0, specular on.

Skin `guard_a` (`textures/guard_ramps.json`, tier-A fit error mean / p95 in 8-bit levels): chrome 1.37/4.3, red
7.0/27.8, cyan 9.0/38.6, black 0.48/1.38 (red and cyan carry highlights the luminance ramp flattens; both under 10
mean). One skin (one row, one palette); the four regions let later tiers recolour by numbers.
Emission: the gem only (`claude_shared/emission.py`, grey mask, colour [0.95, 0.06, 0.04] x 0.9, pulse 0.2 / 2.4 s,
bloom). The far LODs carry no emission (their transferred mask cannot tell the gem from the red seam; the gem is a few
pixels at their switch sizes).

## LODs

**11,642 / 5,820 / 2,907 / 1,455** (LOD1 `tools/build_actor_lods.py` through `scripts/lods_wrap.py`; LOD2/3 the
`repair.py` ladder in the project copy `lodrepair/`, first step **r25_12** accepted: LOD1 outline 0.7 % colour 7.4,
LOD2 2.9 % / 10.3, LOD3 3.6 % / 10.8); `verify_far_only` OK; shadow LODs tucked 15 mm. Plates of different bones stay
apart in every level (the LOD welds join only equal skin weights). `lodrepair/work/guard/xeen_guard/` keeps
`r25_12.built.glb` and `bake_r25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **84.5** world units per model metre: the dome top stands 1.834 m in Standing -> **155 units** (sprite frame 0:
116 px x the Xeen bindings' 1.34 units/px); the claws span 1.65 m -> 140 units (sprite 137 px = 184). `yaw_offset
-pi/2`, skin `guard_a`, `cast: Attack`, `run: Running`, `stride_length 0.71`, `run_stride_length 1.18`,
`upper_body_root: B_Spine`, look on `B_Head` (20/10 degrees), socket `gem: Socket_Gem`, events
`attack_melee: {impact 1.033, glow [gem], color [80, 255, 90], glow_scale 0.7}` (the green beam charges at the gem
through the wind-up and goes out as the claws land). No `death_effect` (the corpse lies on its back).

**Recommended collision for row 11603: height 155, radius 55** (pauldrons 1.1 m wide -> 93 units, claws 140 units
spread; the descriptor's 160 / 90 takes the sprite's full claw span as the radius).

## Checks

- Winding: 0 inverted closed parts (export and installed source). Installed with `tools/install_model.py --world xeen`.
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_guard_claude check`: 8 clip
  switches, no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root); shots
  in `review/shots/`, sheet `review/viewer_shots.png`.
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 176 units = 2.08 model m, 4.2 m away; close-ups of
  the gem, both hands, both feet).
- In game: `review/ingame/` (XD-21, `build-xeen/game/openyamm`, `model spawn` of the installed GLB at scale 84.5 yaw
  pi: Standing, the blow, Dead; forced LOD 2 and 3; wind-up; walk; `sheet.png`); `review/ingame/tour.yml` has the
  command. Exit 0, no model errors in the log. The gem glows at LOD0/1.

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture, from `00_three_quarter.png` | 5 | `01a1fb45-d9d8-741c-b384-8c9f533cbe37` (primary), succeeded |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs (`texturing/guard_upload.glb`), views 01, 03, 02, 04 | 10 | `01a1fb6e-fa37-7599-b9da-bb9a91002c58` (primary), succeeded |

No animation purchases (all clips retargeted from the installed stand-in).

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_guard_claude
TOK=$TOK scripts/step.sh inspect_raw.py; TOK=$TOK scripts/step.sh clean.py
TOK=$TOK scripts/step.sh segment.py; TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/guard_upload.glb exists (the paint belongs to that layout)
TOK=$TOK scripts/step.sh retarget.py [clip ...]     # rig_uv.blend -> anim_v1.blend
TOK=$TOK scripts/step.sh gates.py; TOK=$TOK scripts/step.sh measure.py
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]       # compose, grade, gutter fill, ramps, export, LODs, skin, emission, far LODs, winding
python3 scripts/viewer_tiers.py && python3 ../claude_shared/emission.py review/viewer/xeen_guard_a.glb \
  review/viewer/xeen_guard_a.glb --material Guard --mask textures/guard_emission_mask.png --color 0.95,0.06,0.04 \
  --strength 0.9 && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_guard.glb 84.5
python3 ../claude_shared/tier_textures.py textures/guard_basecolor_graded.png textures/guard_region_mask.png \
  textures/guard_ramps.json work/tier_guard && TOK=$TOK scripts/step.sh render_textured.py
```

Review sheets: `views.py`, `pose_view.py`, `clip_sheet.py <view>` + `sheet_rows.py <view>` (plates coloured by bone,
`colorize.py`), `probe_m592.py` (the stand-in's rest skeleton and clips).

## Known limits

- Rigid plates: bending joints open dark gaps showing the joint spheres and cut caps (knees in the walk, the elbows
  and pauldrons when the arms rise overhead in the wind-up, the hips in the run). Read as robot joints; no smooth
  skin anywhere.
- The UV layout spends about a third of the atlas on the hidden joint spheres and cut caps (uniform density); the
  visible shell still meets every target. A relayout with those parts scaled down would need a new 10-credit paint.
- The knee rings keep some white smear from the paint on their lower edge; small at play distance.
- The corpse lies on its back with the boots raised (the source's death pose on our straight FK legs).
- The red and cyan ramps flatten the paint's highlights a little (fit error 7-9 levels mean).
- The far LODs (2, 3) do not glow.
- Seen in game only as debug-spawned models (no binding merged yet); not accepted by the user.
