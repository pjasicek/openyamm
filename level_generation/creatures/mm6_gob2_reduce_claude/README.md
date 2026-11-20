# MM6 Goblin (BGoblin A/B/C) reduction (2026-10-13)

User: optimise the New Sorpigal goblin, female/male peasant, guard and mage. `../reduce_installed.sh gob2 Goblin "<title>"`
(texture-aware reduction of the installed `assets_source/worlds/mm6/models/mm6_gob2.glb`, no retexture). Limits scaled to
the model's height: p99 4.9 mm, max 24.51 mm. Pick r55: visual pick: no step passes the surface limits, which count skin hidden under the armour (worst: neck under the collar in Hit, invisible in renders `review/pose/`); 55 % and 45 % look identical to the source in the worst poses.

| step | triangles | p99 / max mm | IoU min | SSIM | |
|---|---:|---|---|---|---|
| source | 11,027 | | | | |
| 70 % | 7,717 | 3.91 / 31.2 | 0.995 | 0.9896 | fail |
| 55 % | 6,063 | 6.45 / 31.2 | 0.9889 | 0.985 | **pick** |
| 45 % | 4,961 | 8.51 / 35.21 | 0.9804 | 0.9779 | fail |
| 40 % | 4,409 | 9.58 / 42.83 | 0.9726 | 0.9737 | fail |
| 35 % | 3,859 | 11.48 / 44.77 | 0.9661 | 0.9676 | fail |
| 30 % | 3,307 | 13.61 / 45.18 | 0.9601 | 0.962 | fail |
| 25 % | 2,755 | 17.5 / 71.25 | 0.9493 | 0.9543 | fail |

`export/mm6_gob2.glb`: LODs 6,063 / 3,002 / 1,050 / 322, variants carried to every LOD and shadow mesh.
Viewer `review/viewer/` (installed vs pick, every variant and clip; passes `check_viewer.mjs`), close renders
`review/close/sheet_*.png`. Not installed yet.

## Teeth, shin spikes and retexture (2026-10-13, not installed)

User: "goblin: fix the teeth ... and the shin guard teeth ... and regenerate textures." From the 55 % candidate:
- `scripts/build_gob.py`: `piece` labels from the gated master (`../mm6_gob2_claude/work/rig_v6.blend`, same rest
  space) voted per connected piece, head faces from the installed atlas half; the 14 teeth (pieces 60-78, B_Head) and
  the four greave spikes (37/62, 50/59, on the calves) rebuilt as 6-sided cones (root sunk 35 %); two texture sets
  with fresh smart-project UVs (body 5,025 / head 1,129 triangles); Meshy uploads. 6,154 triangles.
- Meshy `body_retexture_r55` + `head_retexture_r55` (the original requests and HD/head references, original UVs on):
  20 credits; UV parity exact for both sets.
- `scripts/build_gob_runtime.sh`: parity, rasters, `compose_gob.py` (the original compose plus: gold-ivory shin spikes,
  ivory teeth, dark mouth interior, warm spike paint on the greave plates filled from the plate, the whole head skin in
  the tier mask so nose speckles recolour, no sword swatches), `export_master.py`, `assemble_gob.py` (new geometry and
  maps into the installed GLB: rig, clips, sockets and the Sword joint unchanged, head primitive + GoblinHead_A/B/C
  added), prepare, LODs 6,154 / 3,045 / 1,066 / 370, `carry_variants.py`, the original shadow tuck,
  `clamp_lod_uvs.py` (LOD decimation pushed 4 corners past 1.0, which the head merge refuses), head merge (2080x1024
  atlas), viewer tiers. 30 s.
- Review: `review/final/sheet_mouth_shins.png`, `review/final/sheet_tiers.png`; viewer entries `gob2_*_r55t` (81
  loads pass). Timings: geometry 4 min, Meshy 2 min, compose/runtime with three fix rounds 4 min; 11 min in all.
- Remaining: the back yoke is painted leather (the installed model's back was iron); slightly paler ivory teeth than
  the installed yellow; faint dark lines on the greave plates.

### Review 1 fixes (2026-10-13, compose only, no Meshy)

User: "has some triangles on his head + his bottom teeth should resemble the top ones ... its a goblin?" and "it lost
like some normal maps or ... the 'definition' ... compare orig stomach with new one".
- Measured (`scripts/definition_metrics.py`, `work/definition_metrics_{before,after}.json`): normal maps the same size
  (2080x1024), scale 1 and weak tilt (1-2 deg) on both; the loss was the skin's painted muscle lines plus flatter tier
  ramps rebuilt from the softer Meshy skin (linear luminance 0.02-0.19 vs the installed 0.01-0.82).
- `scripts/installed_lookup.py`: every new texel's point on the installed surface (UV + tangent frames of both meshes;
  smooth frames - the welded GLB import marked the installed faces sharp, which first gave a 16 deg normal mismatch
  and added facets; now 1.3 deg mean).
- `compose_gob.py`: body skin takes the installed stored skin luminance where both are skin (216,858 of 219,328
  texels; the new hue is kept), other body texels take the installed 5 px detail band, the installed normal map is
  carried into the new tangent frames (glTF convention), the installed tier ramps are kept, head skin keeps its new
  detail but takes the installed face's luminance distribution (quantile match), 14 face UV islands painted off-tone
  are shifted to their 3D neighbours' tone, the eye mask holds only iris/white/pupil, both tooth rows are dirty
  yellowed ivory dark at the gum (lower row 18 % darker, it faces the light), the gum next to the teeth is dark.
- Sheets: `review/defn/definition_sheet.png` (installed vs new, A and B: torso front/3/4/side, arm front/out),
  `review/face/face_sheet.png` (A/B/C: front, both 3/4, both sides, top), `review/face/eye_compare.png`.
- Left as is: the dark wedge above each eye is the brow/socket roof fold of the source mesh (present on the installed
  model too); a few skin flecks on the pauldron rims.

## Installed (2026-10-13)

User: "goblin accepted". `export/mm6_gob2.glb` (6,154 tris, LODs 3,045 / 1,066 / 370, variants on every LOD and
shadow mesh) installed as `mm6_gob2.glb`; previous source in `work/mm6_gob2_source_pre_reduce.glb`.
`mm6_gob_actor_models_bind_sorpigal_goblins` passes.

## Floor fix — 2026-10-21

`--ground-loop` Standing, Walking, Fidget; `--raise` Running, Attack, Cast, Hit; `--ground-death Death Dead`. The whole body stood about 5 cm (0.053 m) into the floor in every clip since the original export. Before, in world units at tier A: standing at -5.1; walking sinks to -7.2; Cast sinks to -10.1; Running sinks to -4.8; Attack sinks to -10.0; Standing sinks to -6.2; Hit sinks to -7.2; Fidget sinks to -6.2; Walking sinks to -7.2; corpse at -6.5; dying sinks to -7.7.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_gob2.glb`), written to `export/mm6_gob2_floor.glb` and installed as `mm6_gob2.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.

## Gait rollout (2026-10-31)

Package [h06 of the gait rollout](../gait_rollout_20261031/h06/README.md) appended new locomotion clips (Sprint) to
the installed `assets_source/worlds/mm6/models/mm6_gob2.glb` (existing clips, meshes, skins and materials unchanged)
and installed it; the bindings are in `../gait_rollout_20261031/h06/bindings.yml`. Rebuild from the pre-gait copy:
`level_generation/creatures/gait_rollout_20261031/h06/scripts/rebuild.sh gob2`. A far-LOD repair, head-bob or
reduction rerun on this model must re-graft these clips: copy the new source over
`../gait_rollout_20261031/h06/work/mm6_gob2_pre_gait.glb`, rerun that rebuild and install its export.
