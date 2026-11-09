# MM6 air elemental (aie1) — 3D model

Accepted by the user on 2026-10-13 (`creature_3d_progress.json`). Installed for all three tiers: Dust Devil
(`ElemAir A`, palette 198), Twister (`ElemAir B`, 199) and Air Elemental (`ElemAir C`, 724) in
`assets_dev/worlds/mm6/models/actors.yml`. Not Meshy: a wind funnel has no surface or anatomy, so it is built
procedurally in Blender from the restored x2 frames (`../mm6_aie1/redo_2x/aligned_2x`, which the user rates above the
native ones).

## Build

```sh
python3 scripts/make_texture.py      # textures/aie1_wind.png, aie1_profile.json, aie1_region_mask.png, aie1_ramps.json
/snap/bin/blender --background --factory-startup --python scripts/build_model.py   # work/aie1.blend, export/*_raw.glb
python3 scripts/finish_glb.py        # LOD wiring, runtime material, tiers -> export/mm6_aie1.glb
python3 ../../../tools/install_model.py export/mm6_aie1.glb --world mm6
```

Regression: `OPENYAMM_REGRESSION_FILTER=mm6_aie1 ./build/game/openyamm --world mm6 --headless-run-regression-suite
actors` (tier heights follow the native frame scales 0.6 / 0.7 / 0.8).

## How it works

- **Wind atlas** (1024 x 2048, four 512-row bands): body (four restored standing frames unwrapped as cylinders, cos^2
  crossfades so it tiles round), outer streaks (the body's pale streaks only, smeared along the wind), dust wisps
  (sparse streaks in the restored dust colours from `masks_2x` green) and lightning (texels of attack frames b/c/d
  brighter than any standing streak, unwrapped at 1.35 x the standing silhouette so the branches that leave the body
  sit on the bolt shells).
- **Geometry**: core and outer shells revolved from the mean standing silhouette, thin dust rings outside them whose
  edges stand out past the body as the sprite's horizontal wisps, and up to three lightning shells. One
  alpha-blended, single-sided, unlit material; faces are ordered back to front (inner sides outermost-first, then
  outer sides core-first), and the engine keeps a blended primitive's authored triangle order.
- **LODs** (`extras.openyamm_lods`), built as the same layers with fewer segments rather than decimated, which would
  break the blend order: 4,352 / 1,984 / 720 triangles (3 / 2 / 1 lightning shells).
- **Spin** is texture scroll (`openyamm_uv_scroll`, 1.0/s: the core turns once a second), which also runs on creature
  models (`u_modelScroll`, see `engine/render/MODEL_RENDERING.md`), so it is continuous across clip changes. Core,
  outer and dust layers repeat the texture 1x, 2x and 3x round, so they turn at 1, 1/2 and 1/3 turns a second.
- **Rig**: Root (moves, uniform scale), six Funnel bones (sway and lean only), a leaf Wind bone per funnel bone
  (non-uniform width scale; it deforms the wind and dust) and a leaf Bolt bone per funnel bone per lightning shell.
  No scaled bone has children, so the chain never shears. Bone space: Y is vertical, +X rotation tilts toward −Y
  (forward; `yaw_offset: -pi/2`). A bolt shell is hidden by scaling its bones to 0.001 (it collapses onto the axis).
- **Clips** (24 fps, native 125 ms frames): Standing (4 s snaking sway; also walking and fidget), Attack (0.75 s: the
  funnel gathers, flares 20 % and leans in while the three lightning shells light one after another with held,
  jumping twists and random drop-outs; `events.attack_melee.impact` 0.33 s at the peak), Hit (width pinch to 58 %
  and recoil, recovers), Death (thins to nothing and sinks to 60 %), Dead (held gone; the native corpse is empty).
- **Tiers**: one shared atlas plus `aie1_region_mask.png` (R cool wind and lightning, G warm dust, by the restored
  `materials.py` hue rule) and per-tier ramps fitted by `region_variants.fit_ramps` to the restored package's own
  recolour (`materials.recolor` with `recolor_vectors.json`) of this atlas. Fit error: mean ≤ 1.7, p95 ≤ 5.1 8-bit
  levels (tier A cool region worst).
- Scale 59.9991 = 100 Blender units per native pixel x native frame scale 0.599991; B/C use `scale_reference`.

## Reviewed

`review/`: standing next to the restored sprite, all three tiers outdoors at one camera, the Attack clip, the
Standing/Hit/Death clips, forced LOD 0/1/2 and the Air Elemental attacking indoors (Agar's Laboratory). The hostile
flyer climbs over the party outdoors, so the attack was checked on a placed model there and live indoors.

## Known limits

- The inspect portrait has no clock of its own: it reuses the last world frame's scroll time.
- No dust swirl particles at the base (an effects addition, not part of the model).
- Lightning is alpha-blended white, not additive glow.

## Floor fix — 2026-10-21

`--hover -0.144721 Death Dead` (flier rule). Before, in world units at tier A: living lowest at +8.7 (suggested hover -0.144721).
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_aie1.glb`), written to `export/mm6_aie1_floor.glb` and installed as `mm6_aie1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
