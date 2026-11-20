# MM6 fire elemental (fie1) — 3D model

Installed for all three tiers on 2026-10-13, awaiting user review: Fire Beast (`ElemFire A`, palette 204), Fire
Spirit (`ElemFire B`, 728) and Fire Elemental (`ElemFire C`, 729) in `assets_dev/worlds/mm6/models/actors.yml`.
Not Meshy: the restored sprites (`../mm6_fie1/redo_2x/aligned_2x`) show a featureless dark-red human shape inside a
cage of flame, so the figure is an MPFB2 body on library clips and the flames are built from the restored pixels,
like the air elemental (`../mm6_aie1_claude`). No Meshy credits and no image generation were used.

## Build

```sh
./scripts/rebuild.sh     # figure, retarget, textures, model, runtime GLB (run from this directory)
# then, from the repository root:
python3 tools/install_model.py level_generation/creatures/mm6_fie1_claude/export/mm6_fie1.glb --world mm6
```

`rebuild.sh` runs `build_figure.py` (MPFB body, `work/figure.blend`), `retarget.py` (Mixamo clips,
`work/anim.blend`), `make_texture.py` (textures, profile), `build_model.py` (`work/fie1.blend`,
`export/mm6_fie1_raw.glb`) and `finish_glb.py` (`export/mm6_fie1.glb`). Review helpers: `render_views.py` (clay or
unlit EEVEE sheets, `--only` a LOD) and `compare_sprite.sh` (restored sprite views above same-scale renders).

Regression: `OPENYAMM_REGRESSION_FILTER=mm6_fie1 ./build/game/openyamm --world mm6 --headless-run-regression-suite
actors` (`mm6_fie1_actor_model_tiers_follow_sprite_scales`: every tier binds and stands 150–200 units tall at the
shared native frame scale 0.7).

## How it works

- **Figure**: MPFB body (androgynous, slim), helpers removed, face/hands/feet smoothed, decimated to 3,000
  triangles, arms lowered 18° and legs closed 4° in its rest pose, 1.66 units tall from 0.36 above the pivot (the
  sprite's figure spans about 0.2–2.05; it sits a little higher so the hanging legs stay in the narrowing cage).
  Unlit and opaque; its texture is baked mottled red from the restored core pixels' colour percentiles, shaded by a
  soft key and ambient occlusion.
- **Clips** (24 fps) from `anim_library/mixamo`, retargeted by `retarget.py` (spine, clavicles and legs copy the
  source's rotation change from its rest; arms copy absolute directions, A-pose to T-pose):
  Standing/Walking = *Floating* with the arms and legs eased toward the rest pose (`calm`); Walking adds the flight
  lean (20° forward about mid-cage, measured from the restored side views). Attack = *Standing 2H Magic Area Attack
  02*, 1.1–2.5 s (hands gather, then burst apart at about 0.65 s; impact event 0.75 s). Hit = *Standing React Small
  From Headshot* (turned to face forward, legs floating, arms calmed). Death = *Standing React Death Backward*
  0–0.75 s. Dead holds everything hidden (the native corpse is empty).
- **Flame cage** (`fie1_flame.png`, 1024×512, tiles both ways): six front/back walk frames unwrapped as cylinders
  over 12–88 % of the cage height, folded so it repeats in v; the restored core mask (the figure seen through the
  cage) is transparent. One revolved shell (radius 1.12× the mean silhouette); its far inside and near outside are
  two layers, so the lattice is kept under a tiling random mask (92 %) that leaves the sprite's gaps open, with
  alpha raised 1.3× (thin edges washed out over bright ground).
- **Fringe** (`fie1_fringe.png`): eight strips of the sprite's outer flame tongues (1.0–1.6× the silhouette radius) on
  radial fins (12/8/6 per LOD). A fin faces the camera exactly where it forms the outline, so the silhouette shows the
  sprite's own tongues. Strips that started inside the silhouette drew vertical streaks across the body.
- **Motion**: cage and fins scroll upward (`openyamm_uv_scroll` [0, 0.4]: flames rise about 40 game units a second,
  continuous across clips). A vertical Cage bone chain under Root sways; leaf CageW bones carry the width (breathing,
  attack flare, hit pinch, death swell); Cage1's uniform scale grows and finally removes the cage. Only leaf bones
  scale non-uniformly.
- **Fx** (`fie1_fx.png`, four quadrants): hand burst (attack frame c) on three orthogonal quads per hand (BurstL/R,
  crackling with held random twists while the hands are out), star flash (death d), sparks (death e) and embers
  (death f), each on three vertical quads at the chest (FxStar/FxSparks/FxEmbers).
- **Materials** (primitive order): Body (opaque), Flame and Fringe (blended, single-sided, faces ordered back to
  front), Fx (blended); all unlit, no specular, no edge darkening.
- **Tiers**: the restored package recolours only the figure, so only the Body material has a region (all of it) and
  per-tier ramps fitted to the restored LUT recolour of the baked body (`textures/fie1_ramps.json`; mean error 2.2 /
  3.3 / 5.1, p95 10 / 12 / 21 8-bit levels; the LUT indexes sRGB luma, the ramps linear luminance). The flames are
  identical in every tier, as in the sprites.
- **LODs** (`extras.openyamm_lods`): 6,098 / 2,804 / 1,304 triangles, shells and fins rebuilt with fewer segments
  (decimation would break the blend order), the figure decimated 50 % / 25 %.
- Scale 69.9997 = 100 Blender units per native pixel × frame scale 0.699997; B/C use `scale_reference`.

## Reviewed

`review/`: standing and walking next to the restored sprite (front, side, three-quarter, back), the Attack/Hit/Death
clips, the three LODs, placed models outdoors (New Sorpigal: standing, attack peak, flight profile) and the three
tiers live indoors (Agar's Laboratory: approach, attack, death). Raw captures and tours are in `review/ingame/`.

## Known limits

- The cage is paler and yellower than the sprite's orange-red rim: the unlit shell cannot darken toward its silhouette,
  and the fins only partly make up for it.
- Near-edge-on fins still add faint vertical lines over the body from some angles.
- Feet and hands can touch the cage edge in some idle frames.
- The actor's glow light is the sprite frame's (white, radius 256/300), unchanged.
- Death sparks and the star are geometry, not particles; no additive glow.

## Floor fix — 2026-10-21

`--hover -0.056268 Death Dead` (flier rule). Before, in world units at tier A: living lowest at +3.9 (suggested hover -0.056268); dying sinks to -21.3.
Applied by [`floor_fix.py`](../claude_shared/floor/README.md) to the installed source (kept in
`work/floor_fix_base/mm6_fie1.glb`), written to `export/mm6_fie1_floor.glb` and installed as `mm6_fie1.glb`; only animation
samplers changed. Earlier exports and the editable `.blend` master predate it: rerun the same operation after any
re-export. Part of the [creature post-process](../CREATURE_POSTPROCESS.md) MM6 pass.
