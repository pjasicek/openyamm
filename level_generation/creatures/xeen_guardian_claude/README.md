# Xeen Guardian (Xeen Construct B), Claude project, 2026-11-20

Lane S sub-agent build (owner `xeen-s3-guardian`, identity `xeen:guardian`, Meshy limit 30 credits). Monster row 11601
"Guardian", descriptor `Xeen Construct B`, level 24, melee Ener 3D7+9 with DrainSP plus an Ener missile, Fly Y. Clouds of
Xeen image 83 (`sprites/xeen/083.mon`, `083.att`): a floating polished chrome skull with a round red gem high on the
forehead and green glints in dark sockets; its attack fires lightning from the eyes.
Built with the [quadruped playbook](../CLAUDE_QUADRUPED_PLAYBOOK.md) (floating heads, flyers, rigid hard-surface
sections), [HD masters](../CLAUDE_HD_MASTER_REFERENCES.md), [creature textures](../CLAUDE_CREATURE_TEXTURES.md) and the
[texture quality pass](../claude_shared/TEXTURE_QUALITY_PASS.md).

**State:** installed in the Xeen world; the binding block is ready in [integration/actors.yml](integration/actors.yml)
for the parent (`xeen-s3`) to merge. Agent visual review done; not yet seen by the user.

**Bind only `Xeen Construct B`.** Decision D-19 (2026-11-20): Xeen's Guard (11603, `Xeen Construct D`, whose own sprite
is a silver armoured humanoid) gets its own model later (`xeen_guard_claude`); the Guardian model is not bound to it.
The region mask (R chrome, G gem, B eyes) still lets later skull tiers (Yak Master, Yak Lich share Xeen image 83)
recolour by ramps only.

## Deliverables

| File | What |
|---|---|
| `assets_source/worlds/xeen/models/xeen_guardian.glb` (sha256 `15ded8c4…`) | installed source (= `export/xeen_guardian.glb`); cooked runtime copy in `assets_dev/worlds/xeen/models/` (`e957bb1d…`) |
| `integration/actors.yml` | the binding block for `Xeen Construct B` (not merged by this agent) |
| `work/anim_v1.blend` | keyed master (rig `Guardian_Rig`, mesh `Skull`); `work/anim_base.blend` is the locked UV layout |
| `references_hd/` | five Codex masters (1024x1536, two runs, all first renders selected), `CODEX_BRIEF.md`, `generation_runs.json`, `selected_views_review.png` |
| `textures/` | `guardian_basecolor_graded.png` (2K), `guardian_normal_1k`, `guardian_mr_1k` (R AO, G roughness, B 0), `guardian_region_mask.png` (R skull, G gem, B eyes), `guardian_emission_rgb.png`, `guardian_ramps.json`, `guardian_material_classes.png` (9 metal, 11 gem, 6 eye), `guardian_ao_2k.png` |
| `review/` | `textured_sheet.png` (party eye height: front, quarter, side, the bite, the ranged release, corpse, face, back), `clips_side.png`, `clips_quarter.png`, `clean2_sheet.png` (parts), `raw_sheet.png`, `viewer_shots.png`, `ingame/sheet.png` |
| `review/viewer/` | review viewer (one skin, ramp baked, emission) |

## Mesh, rig and parts

Meshy Smart Topology v1 (meshy-t2, 15k, from `00_three_quarter.png`): 15,987 triangles, 37 pieces: cranium, a separate
mandible, 31 separate teeth, two small eye spheres, a hidden inner duplicate of the cranium shell and a sliver.
`scripts/clean.py`: drops the inner shell, the sliver and the Meshy eye spheres, cuts the forehead dome out (whole faces
under the bezel), fills five small cranium holes (5-8 edges), collapse-decimates per part (cranium 0.45, mandible 0.47,
teeth 0.6), and adds hand-built parts: a lathe bezel (240 triangles), a 12-sided brilliant-cut ruby (48, flat shaded) and
two eye-core spheres (100 each). **6,879 triangles** (cranium 3,920, jaw 1,110, upper teeth 692, lower teeth 669).
Face attribute `part` (0 cranium, 1 mandible, 2 upper teeth, 3 lower teeth, 4 bezel, 5 gem, 6/7 eyes) drives rig,
masks and classes. Rest: forward -Y, 0.80 m tall, chin at z 0.

`scripts/rig.py`, rigid weights (one influence per vertex): `Body` (hover root at the skull centre) > `Cranium`
(cranium, upper teeth, bezel; named Cranium because a joint `Skull` collided with the mesh node) > `Jaw` (pivot at the
condyles), `Gem`, `EyeL`, `EyeR` (scaled for flares). Socket bones: `Socket_Gem` (1.5 cm in front of the table),
`Socket_Eye_Left`, `Socket_Eye_Right`.

## Clips (30 fps, procedural: `scripts/anim.py`, after `mm6_bh_claude/scripts/anim_bh.py`)

Jaw angles are relative to the modelled opening (2 cm tooth gap); -7.5 degrees brings the rows together (0.1-0.3 cm
apart, never through each other).

| Clip | Length | What | Event |
|---|---|---|---|
| Standing | 2.0 s loop | hover bob 2 cm, slow sway, the jaw chatters shut and open (native idle) | |
| Walking | 1.0 s loop | 8 degree nose-down lean, faster bob, small chatter | |
| Running | 0.8 s loop | 14 degree lean, stronger bob | |
| Attack | 1.0 s | draws back with the jaw gaping and the eyes flaring (x1.35), lunges 13 cm and bites shut | **impact 0.45 s** (the bite) |
| AttackRanged | 1.0 s | rises 6 cm, jaw gapes, eyes flare to x2.1 and the gem to x1.5 (native att 0-2), fades back | **impact 0.50 s**, glow `eye_left, eye_right, gem`, release `gem` |
| Hit | 0.5 s | knocked back 9 cm with a 18 degree twist, jaw snaps open | |
| Death | 1.5 s | shudders with the jaw gaping while the eyes go out (x0.3) and the gem dims, drops and rolls onto its left side, small bounce | |
| Dead | 1.0 s | Death's last pose (on its side on the floor) | |
| Fidget | 2.0 s | a jaw-chattering cackle while the skull turns side to side | |

No cast clip (`cast: Attack`: the row has no spell).

**Flyer floor rule:** one uniform hover lift (0.0792 m = 9.9 units) in every living clip, so the lowest point over all
living clips (the Attack lunge) meets the floor; the death eases it out and the skull never cuts the floor while it
rolls. No `z_offset`. Floor audit (`floor_audit.audit` with this binding on the export; Fly Y in the generated row):
**flier, standing 7.8..13.8, walking 4.3..9.4, living lowest 0.0, corpse 0.0 world units, no problems.**

Gates (`scripts/clip_gates.py export/xeen_guardian.glb`, largest per-frame vertex step / second difference, loop seam):

| Clip | Step cm | Accel cm/f² | Seam cm | Lowest units |
|---|---|---|---|---|
| Standing | 3.70 | 3.54 | 0.00 | +7.84 |
| Walking | 3.58 | 3.56 | 0.00 | +4.31 |
| Running | 3.64 | 3.57 | 0.00 | +0.58 |
| Attack | 14.16 | 11.37 | (one-shot) | 0.00 |
| AttackRanged | 4.08 | 3.41 | | +9.72 |
| Hit | 10.92 | 6.66 | | +9.86 |
| Death | 7.80 | 6.86 | | 0.00 |
| Fidget | 5.18 | 4.60 | | +8.20 |

The Attack's large step is the chin during the bite snap (31 degrees in about 0.07 s), the Hit's the knock-back:
intended. Contacts: rigid pieces; the jaw range keeps the teeth apart by construction (gap >= 0.1 cm at -7.5 degrees).

## Textures

UVs `scripts/uv.py` (`uv_atlas.unwrap` defaults): **PartUV failed** on this mesh (31 loose teeth; the error is in
`work/uv_report.json`), so it fell back to xatlas charts, then the seam pass and sparrow packing. Measured
(`texture_quality.py`): **atlas 72.7 %, density p10/p50/p90 856/905/981 (spread 1.15), 105 islands, fragments 0.0 %,
stretch p90 1.24**. Meshy `retexture_v1` (meshy-7, 4K, PBR, original UVs; views 01, 03, 02, 04) returned the same layout.

`scripts/compose.py`: colour 4K -> 2K once; red or green specks the masters' gem and glints projected onto chrome turned
to their own grey (19,193 texels); chrome x1.3 brighter (`SKULL_GAIN`: Meshy median 105 of 255 vs the sprite's grey
median 92, sprites carry baked shading); the gem painted procedurally per facet (dark to bright ruby by facet normal)
and the eye cores as emerald with a light green front. Gentle grade (`--fine 1.0 --local 0.3 --ao-strength 0.5
--contrast 1.06 --saturation 1.15`), procedural texels restored after it (`keep_procedural.py`), `gutter_fill.py` last
on every map. Roughness: chrome 0.28-0.55 (Meshy), gem 0.12, eyes 0.2; metallic 0, specular left on (chrome).

Skin `guardian_a` (`textures/guardian_ramps.json`, tier-A fit error mean/p95 in 8-bit levels): skull 0.77/2.21,
gem 2.09/7.29, eyes 11.31/51.6 (small eye islands mixed at the 1K fit size; they read green in game).

Emission (`scripts/emission_rgb.py`: a colour emissive texture, red gem and green eyes in one material, factor 0.9,
pulse 0.2 over 2.4 s). The far LODs get their own emission maps from their own transferred masks
(`scripts/far_emission.py`), since lod_repair's far materials kept LOD0's emissive map on their new UVs.

## LODs

**6,879 / 3,436 / 1,711 / 855**, shadow LODs tucked (`shrink_shadow_lods.py`, then lod_repair's). Far chain: project
copy of `lod_repair_claude/scripts` in `lodrepair/` (outputs stay here). The plain step r25_12 passed the gates but
**dropped the eye cores and most of the gem** (far masks without G/B); the curvature step **c25_12** keeps them and was
taken: LOD2 outline 2.2 %, colour 9.1; LOD3 3.4 %, 7.7 (gates 6 % / 16 and 13 % / 19.5); `verify_far_only.py`: OK.
`lodrepair/work/eyes/xeen_guardian/` keeps `c25_12.built.glb` and `bake_c25_12/` for map-only reruns.

## Binding (integration/actors.yml)

Scale **125** (0.80 m skull -> 100 units: the sprite's 76 px at the Xeen witch's 136 px = 182 units), `yaw_offset
-pi/2`, skin `guardian_a`, `cast: Attack`, `run: Running`, `stride_length 0.5`, `gait_rate [0.8, 1.5]`,
`upper_body_root: Cranium`, look on `Cranium` (40/30 degrees), sockets `gem`, `eye_left`, `eye_right`, `eye_color [60,
230, 70]`, events `attack_melee.impact 0.45`, `attack_ranged {impact 0.5, glow [eye_left, eye_right, gem], release
gem}`. No `death_effect` (the skull falls and lies on the floor).

## Checks

- Winding: 0 inverted closed parts. Installed with `tools/install_model.py --world xeen` (cooked runtime copy).
- Viewer: `python3 tools/run_creature_review.py --project level_generation/creatures/xeen_guardian_claude check`:
  9 clips switched, no console errors (served by `python3 -m http.server 8912 --bind 127.0.0.1` from the repo root).
- Renders: `review/textured_sheet.png` (EEVEE, party eye height 1.41 model m = 176 units, 3 m away) and the viewer
  shots; in game `review/ingame/` (XD-21, `model spawn` of the installed GLB at scale 125, Standing / the bite / the
  ranged release, forced LOD 2 and 3, the corpse, a close one): loads, gem and eyes glow at every LOD.
- `build-xeen/game/openyamm` segfaults at exit (exit -11), also in the plain new-game preparation scenario of
  `run_game.sh` without any of this model loaded; the captures complete before it. Not investigated (no builds here).

## Meshy credits: 15 of 30

| Job | Kind | Credits | Task |
|---|---|---|---|
| `smart_topology_v1` | image-to-3d, meshy-t2 smart-topology 15k, no texture | 5 | `01a1f956-5ee5-74e6-b3bc-9e3ab8ad10c5` (primary) |
| `retexture_v1` | retexture, meshy-7, 4K, PBR, original UVs | 10 | `01a1f962-1658-75d8-8bb3-b54d838f8b4e` (primary) |

## Rebuild

```sh
TOK=<lease>; cd level_generation/creatures/xeen_guardian_claude
TOK=$TOK scripts/step.sh prep.py; TOK=$TOK scripts/step.sh clean.py; TOK=$TOK scripts/step.sh rig.py
# uv.py refuses to run once texturing/guardian_upload.glb exists (the paint belongs to that layout);
# rename_bone.py was the one-off Skull -> Cranium rename on the locked anim_base.blend
TOK=$TOK scripts/step.sh anim.py
TOK=$TOK scripts/step.sh dump_uv3d.py; TOK=$TOK scripts/step.sh bake_ao.py     # only after a layout change
TOK=$TOK scripts/build_runtime.sh [--install]   # compose, grade, ramps, gutter fill, export, LODs, skin, emission, far LODs
python3 scripts/viewer_tiers.py && python3 scripts/emission_rgb.py review/viewer/xeen_guardian_a.glb \
  review/viewer/xeen_guardian_a.glb --material Guardian --image textures/guardian_emission_rgb.png --strength 0.9 \
  && python3 scripts/update_viewer_manifest.py
python3 scripts/clip_gates.py export/xeen_guardian.glb; TOK=$TOK scripts/step.sh render_textured.py
```

## Known limits

- The chrome reads mid grey in dim rooms (XD-21's robbers' den): lit PBR metal with specular, not the sprite's painted
  highlights. `SKULL_GAIN` in `compose.py` is the knob if the in-game comparison with the sprite asks for it.
- The native attack's lightning forks are not modelled: the engine's charge glow at both eyes and the gem and its
  release burst stand in for them.
- The mouth never quite closes (0.1-0.3 cm between the tooth rows at full chatter), by design so the teeth never cross.
- Eye ramp fit error is high (11 levels mean) because the eye islands are tiny at the 1K fit size; visually green.
- PartUV fell back to xatlas charts (targets met anyway).
- Seen in game only as debug-spawned models (no binding merged yet); not accepted by the user.
