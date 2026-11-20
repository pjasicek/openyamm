# MM6 sea serpent (seas) — 3D model, 2026-10-08

Sea Serpent / Sea Monster / Sea Terror (descriptors 625–627; Hermit's Isle `outa3.odm`, Eel Infested Waters
`oute1.odm`), installed as `assets_dev/worlds/mm6/models/mm6_seas.glb`, bound in
`assets_dev/worlds/mm6/models/actors.yml` (opt-in via `debug.actor_models=true`).
Viewer: <http://127.0.0.1:8901/level_generation/creatures/mm6_seas_claude/review/viewer/> (checked with
`claude_shared/check_viewer.mjs`).

| Item | Value |
|---|---|
| References | Codex HD views `references_hd/` (native walk pose: column rising from the water, arched forward) + `05_foam_ring.png` (top-down foam ring) |
| Model | Meshy `multi-image-to-3d` (four views, textured, 2k, remesh 20k): 20,886 tris |
| LOD0/1/2/3 | 8,000 / 4,000 / 1,440 / 480 (+ foam collar 384) |
| Rig | 16 bones up the column (Root at the waterline … Head) + unparented FoamRoot |
| Clips (24 fps) | Standing 3.0 s, Walk/Attack/Hit/Death/Fidget 1.125 s (native timing), Dead (sunk) |
| Tiers | shared skin; regions R scales, G crest/spikes, B belly; foam its own material (region R = foam); palettes 813/814/815 |
| Scale | 528 (native stand frame 240 px × frame scale 2.2 against the 1 m model); C via `scale_reference` (2.8) |
| Meshy credits | 30 of 100 |

## Pipeline (scripts/)

`prepare_seas.py` → `rig_seas.py` on `hd_base` (→ `rig_20k.blend`) → `reduce_bent.py` 8000 → `bake_reduced.py`
(89° islands, cage 12 mm) → `rig_seas.py` on `hd_reduced` → `bake_creature_ao.py` on `hd_reduced` (before the foam)
→ `add_foam.py` → `anim_seas.py` → `dump_uv3d.py` (body triangles only) → `grade_basecolor.py --ao` →
`compose_seas.py` → `build_runtime.sh --install` → `viewer_tiers.py` → `update_viewer_manifest.py`.

## Triangle reduction (installed 2026-10-14)

The installed model is the reduction from [mm6_seas_reduce_claude](../mm6_seas_reduce_claude/README.md): body 8,000 ->
6,286 triangles (head 90 %, body 75 %), foam collar, textures and tiers unchanged, with the revised Attack below.
The LOD row above describes the pre-reduction model (rollback source in that project).

## Notes

- **Attack (revised 2026-10-14, user request)**: the windup leans and turns to one side, the strike sweeps forward
  and down across to the other (it was a symmetric smash in one vertical plane). `anim_seas.py` `attack()`;
  `work/anim_v1.blend` re-keyed. The reduced runtime model carries it: `../mm6_seas_reduce_claude/README.md`.

- **Foam collar**: the sprites paint turquoise foam at the waterline. Here it is a slightly domed annulus with the
  Codex foam ring as an alpha cut-out (MASK) texture, on an unparented `FoamRoot` bone so it stays on the water while
  the body leans; clips spin and pulse it, Death shrinks it away while the body sinks. It is exported as its own mesh
  node `Foam`: `build_actor_lods.py` only reduces and shadows `Seas` (merged shadows need opaque materials), and the
  thin ring needs neither. Mesh and bone names must differ (the engine rejects duplicate node names).
- **Reduction**: protecting the whole head kept a third of the mesh at full density (13.8k floor); only edges folded
  more than 90° (spike/claw tips, teeth) are protected. 8k matches 20k in head, full and back views; 7k showed bake
  holes on the belly.
- **Indoor scale bug fixed in the engine**: indoors `GameplayRuntimeActorState::height` is the padded collision
  height (at least 2 × radius + 2), and the 3D model scale used it, so wide monsters (this one: radius 160, height
  111) rendered 2.9× too big indoors. New `bodyHeight` (unpadded) is used for the model scale instead.
- **Tier ramps keep the texture's own brightness** (user review 2026-10-08: "torso too speckled with black dots").
  Histogram-matching each region to the native palette mapped the Meshy belly's narrow luminance (0.12–0.28) onto the
  sprite's painted-shading range (0.002–1.0), a ~7x contrast boost that turned its fine pebbles into black/white
  dots. `compose_seas.py` now takes only the colour from the palette (band-averaged chroma from its 15th–95th
  percentile, interpolated by the texel's luminance percentile) and keeps the texel's luminance, scaled so the
  region mean matches the native mean × 1.35. The belly mask also grows into the ring creases.
- Known limits: very faint seams in the red tier's belly creases; Dead is fully sunk (no corpse, as the sprite).
