# Xeen Flying Feet (Xeen Construct A, monster 11600), 2026-11-20

Lane S sub-agent build (identity `xeen:feet`, Meshy limit **35 credits**; stage 1 by `xeen-s2-feet`, the rest by
`xeen-s3-feet`). Clouds of Xeen image 26 (`sprites/xeen/026.mon`, `026.att`): two disembodied bare feet with two small
white wings at each ankle (Hermes' talaria). Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md)
(floating heads / flyers / rigid sections), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md),
[creature textures](../CLAUDE_CREATURE_TEXTURES.md), the [texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md)
and the [LOD playbook](../LOD_PLAYBOOK.md).

**State: installed** (`tools/install_model.py --world xeen`), checked in the viewer and in game (static model spawns
in XD-21). The binding is **not** merged (the lane parent owns `actors.yml`): the ready block is
[integration/actors.yml](integration/actors.yml). Not accepted by the user.

## Deliverables

| Item | Value |
|---|---|
| Installed | `assets_source/worlds/xeen/models/xeen_feet.glb` = `export/xeen_feet.glb` (runtime copy cooked into `assets_dev/worlds/xeen/models/`) |
| Binding block | `integration/actors.yml` (descriptor `Xeen Construct A`, skin `feet_a`, scale 267) |
| Masters | `references_hd/00`-`04` (Codex, two runs, medium effort; `generation_runs.json`, `selected_views_review.png`, `CODEX_BRIEF.md`); one **right** foot, the left is its mirror |
| Masters (blend) | `work/foot_v2.blend` (single textured foot, v2 UVs), `work/rig.blend` (the pair on `Feet_Rig`), `work/anim.blend` (keyed clips; export source) |
| Textures | `textures/feet_basecolor_graded.png` (2K), `feet_normal_1k.png`, `feet_mr_1k.png` (R baked AO, G roughness, B 0), `feet_region_mask.png` (R skin, G wings), `feet_ramps.json`, `feet_material_classes.png` (1 skin, 2 feathers, 4 nails) |
| Review | `review/viewer/` (viewer, `xeen_feet_a.glb`), `review/party_sheet.png` (party eye height: front, three-quarter, side, the blow x2, hit, corpse, back), `review/clips_{front,side,quarter}.png` (clay clip sheets), `review/close_sheet.png` (Eevee close-ups), `review/texture_quality.json`, `review/motion_audit/` |

## Mesh

Meshy Smart Topology 15k of `00_three_quarter` (16,181 triangles, 5 pieces: foot, two wing feather layers, the medial
wing, an ankle bump). Scaled to a 0.26 m foot, reduced per part (`foot_single.py`: foot 0.20, wings 0.20) to 3,234
triangles. **Every part came back double-walled**: an enclosed inner shell (979 triangles, found by visibility:
no point of a face sees out along any of 162 directions) took 44 % of the first paint atlas. `foot_v2.py` removes it
(a single normal-ray test also removed partly covered skin at the wing roots and between the toes and left holes) and
lays new UVs: **2,255 triangles per foot, 4,510 for the pair**. The left foot is the right one mirrored (faces
reversed, same UVs).

## Rig and clips (`rig_feet.py`, `anim_feet.py`, 30 fps)

Bones: `Root`; per side `Foot_s` (rigid), `Toes_s` (ramped in over the ball of the foot), `WingIn_s`, `WingOut_s`
(rigid, hinge at the wing root). Layout as the native frames: the right foot higher and further back, toes turned out
22 deg; the left foot lower and nearer, toes to the party. Each frame is a parameter set per foot (offset, yaw, pitch,
roll, toe curl, wing raise and fold) turned into bone matrices.

| Clip | Length | What |
|---|---|---|
| Standing | 2.0 s loop | the feet bob in turn (1 s), wings 2.5 Hz, slight sway |
| Walking | 2.0 s loop | leaned 10 deg toes-down, wings 3.5 Hz |
| Running | 2.0 s loop | leaned 18 deg, wings 4.5 Hz |
| Attack | 1.0 s | the left foot draws back and up with its sole turned to the party, stamps forward 0.32 m: **impact 0.45 s** (stamp complete; furthest forward frame 14) |
| Hit | 0.5 s | both feet jolt back, roll 16 deg, wings flare |
| Death | 1.6 s | wings flare and stop, the feet tumble: the right one onto its outer side, the left onto its inner side; wings fitted to the floor |
| Dead | 1.0 s | Death's last pose |
| Fidget | 2.0 s | toe wiggle (left), two heel taps (right) |

One-shot clips start and end on Standing frame 0 (same wing phase per side).

### Gates (`work/anim_info.json`, `review/motion_audit/xeen_feet.json`)

- Flyer rule: one lift 5.97 cm baked into every living clip (lowest living point = the Running toe dip, 0.0 cm);
  Standing 3.7-8.1 cm, Attack 5.7-15.1 cm; the Death eases it out, corpse 0.2 cm. Floor audit (`floor_audit.audit`
  with this binding block, the rows now say Fly Y): **flier, living lowest -0.0, corpse +0.53 world units, no
  problems**.
- Contacts: the two feet never touch (BVH overlap, every frame of every clip: 0). Wings inside their own foot (ray
  parity, samples more than 3 cm from the root): 0-1 sampled vertices at the deepest downstroke, 0 in Attack, Death,
  Dead.
- Loop seams 0.0 mm (Standing, Walking, Running). Smoothness: accel p99 (body heights per s^2) 23 Standing, 48
  Walking, 81 Running, 54 Hit, 36 Death, 182 Attack (the 0.1 s stamp, intended). Rigid parts: no deformation faults.
- Winding: 0 inverted closed parts.

## Textures

Meshy `foot_retexture_v1` (meshy-7, 4K, PBR) on the first `uv_atlas` layout (v1: atlas 75.4 %). After the inner shell
was removed, `transfer_paint.py` carried the 4K paint onto the v2 layout by UV correspondence (one resample straight to
2K colour / 1K normal and roughness; the normal map re-expressed per triangle from the v1 to the v2 tangent frame), so
no second paint was needed. Two fixes were needed for clean seams: v1 island edges eroded by 3 texels and refilled
before sampling, and texels a triangle touches without a sub-sample filled from their neighbours (they stayed black and
drew hairlines along every v2 seam). Grade: `--fine 1.0 --local 0.0 --ao-strength 0.5 --contrast 1.06 --saturation
1.15` (**local 0**, not 0.3: the local-contrast blur crossed the 4-texel gutters of the tight sparrow pack and drew
light seams); `gutter_fill.py` last on every map.

Quality (`texture_quality.py export/xeen_feet.glb`): **atlas 78.2 %**, density p10/p50/p90 2998/3155/4117 (spread 1.37:
the toes are 1.4x denser by design; every bone 3137-3148), 166 islands (both feet), **fragments 2.6 %**, **stretch
p90 1.18**.

Skin `feet_a` (one tier uses the model): region R = skin (foot, ankle bumps, toes, nails), G = the wings, from the
geometry. The paint matches the native palette (native mid 192,132,92 / light 228,184,160; paint median 210,141,94,
hue 24 deg), so the ramp reproduces the graded paint: fit 1.93 / 5.31 levels (mean / p95) skin, 1.72 / 5.75 wings.
Later construct tiers on this model are ramp numbers only. Specular 0, metallic 0.

## Scale, LODs

Scale **267** from the silhouette area (playbook flyers): native idle body area 1530 px x (1.34 units/px)^2 against the
model's mean front silhouette over Standing, 0.0384 m^2 (width alone would give 294, height 249).

LODs 4,510 / 2,254 / 2,018 / 1,341 (LOD1 `build_actor_lods.py`; LOD2/3 the `repair.py` ladder in the project copy
`lodrepair/`, step **r45_30** accepted: LOD2 outline 4.1 % colour 8.8, LOD3 11.3 % / 7.6; the thin feathers fail the
stronger collapses); `verify_far_only` OK; shadow LODs tucked 2-15 mm.

## Meshy credits: 15 of 35

| Job | Credits |
|---|---|
| `foot_smart_topology_v1` (meshy-t2, 15k) | 5 |
| `foot_retexture_v1` (meshy-7, 4K, on `texturing/foot_upload.glb`) | 10 |

## Replay

```sh
TOK=<lease>; cd level_generation/creatures/xeen_feet_claude
TOK=$TOK scripts/step.sh pieces.py foot_smart_topology_v1 foot 0.31   # scale 0.26 m foot, pieces
# foot_single.py 0.20 0.20 made texturing/foot_upload.glb (refuses to overwrite: the paint belongs to it)
TOK=$TOK scripts/step.sh foot_v2.py all        # inner shell out, v2 UVs (sparrow packs differently per run: the
                                               # transfer follows whatever layout this writes)
TOK=$TOK scripts/step.sh bake_ao.py && TOK=$TOK scripts/step.sh rig_feet.py foot_v2.blend
scripts/build_textures.sh                      # transfer, compose, grade, gutter fill
TOK=$TOK scripts/step.sh anim_feet.py          # clips + gates -> work/anim.blend, work/anim_info.json
TOK=$TOK scripts/build_runtime.sh && TOK=$TOK scripts/far_lods.sh
python3 ../../../tools/install_model.py export/xeen_feet.glb --world xeen
python3 scripts/viewer_tiers.py && python3 scripts/update_viewer_manifest.py
```

Checks: `scripts/clip_sheet.py 7 front|side|quarter` + `sheet_join.py`, `party_views.py`, `closeup.py`,
`front_area.py` + `front_area_px.py` (scale), `views.py` / `tex_views.py` / `boundary_check.py` (mesh sheets).

## Known limits

- The ankle under the wing roots carries a few dark painted crease marks from the masters (mostly hidden by the
  wing roots).
- Wings flap as rigid pieces (no feather bend); the Hit/Death feather burst of the native frame 3 is motion only, no
  loose feather particles.
- The stump top is the reduction's rounded cap (the masters drew a flat cut; the native sprite never shows it).
- Standing hovers 3.7 cm (about 10 world units) above the floor at its lowest, because Running's lean sets the shared
  flyer lift.
