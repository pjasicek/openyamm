# MM9 FXF effect-sprite restoration

Restoration packages: [Spell Reaver — discarded experiment; original textures active](spell_reaver/README.md).

This is a future restoration guide only for the MM9 SPR animations referenced by
`CLIENTFX/CLIENTFX/SPELLS.fxf`. It does not authorize image generation and it must not be applied to other MM9
sprites, MM9 world textures, model skins, UI art, water/lava surface sprites, native projectile sprites outside the
FXF library, or the MM6–MM8 prepared restoration queue.

The authoritative scope is the 35 `kind: sprite` records with `origin: spells_fxf` in
`assets_dev/engine/effects/mm9/resource_bindings.yml`. Their 204 frame references resolve to 177 unique DTX textures.
The currently supported runtime subset packages 34 descriptors and 172 unique PNGs; `sprites/spells/leaf.spr` remains
outside that package because `spell-armor` requires unsupported deforming geometry. Recompute these counts from the
binding manifest before a future run rather than expanding scope from filenames found elsewhere.

The supplemental `bloodhit1.spr` and `bloodspray1.spr` records have `origin: hardcoded_melee_contact` and are
explicitly outside this restoration guide. Their source behavior and fidelity limits are documented in
`re_mm8/mm9_vfx/MELEE_HIT_EFFECTS.md`.

## Allowed SPR families

Only these original paths belong to this guide:

- `sprites/dragonbreath.spr`
- `sprites/fire/bluetorch.spr`, `torchflame3.spr`, `torchflame4.spr`
- `sprites/firebreath.spr`, `flareparticle.spr`, `flies.spr`, `oval.spr`, `spirit.spr`
- `sprites/smoke/blacksmoke.spr`, `noisesmokeupwardphase.spr`, `smokenoise.spr`
- `sprites/spells/bluering.spr`, `bwring.spr`, `feather.spr`, `greendot.spr`, `leaf.spr`, `lightball.spr`,
  `redflare.spr`, `skull.spr`, `wash.spr`, `washright.spr`, `whiteflare.spr`
- `sprites/weapons/blurredbluestar.spr`, `blurredblueyelstar.spr`, `blurredgreenorastar.spr`,
  `blurredgreenyelstar.spr`, `blurredpurplestar.spr`, `blurredredstar.spr`, `blurredredyelstar.spr`,
  `blurredwhitestar.spr`, `blurredyellowstar.spr`, `firebolt.spr`, `greenoraringexplode.spr`,
  `ringexplodeblue.spr`

The SPR file supplies frame order and timing; the referenced DTX images are the artwork restoration targets. Preserve
the original SPR resource id, frame count, order, FPS, full canvas, and logical width and height. Do not add in-between
frames or normalize a sequence to individual visible bounds.

## Source and output contract

- Treat `mm9/extracted/` as immutable source evidence. The pixel-preserving PNGs and decoded source mip artifacts under
  `assets_dev/engine/effects/mm9/import/textures/` are inspection inputs, not restoration masters.
- Retain every generated return, mask, review image, rejection and accepted master in a new resumable MM9-FXF-specific
  job ledger. Do not add these jobs to the frozen MM6–MM8 `restoration_jobs` queue.
- Use one complete animation family per sheet. Related color variants may share a call only when every sequence remains
  separately identifiable and keeps its own phase order. Never mix unrelated smoke, flame, ring and character-like art.
- Require a master sampled at least 2× in each axis and export a true RGBA PNG at 2× the native canvas. The descriptor's
  logical dimensions remain native, so increased storage resolution must not change world size or placement.
- Installation must be an explicit accepted-restoration overlay in the MM9 FX importer. Never hand-edit generated
  runtime PNGs without provenance: a normal import from DTX must not silently overwrite accepted artwork.

## Appearance and alpha rules

Use the existing soft-effect principles, but only within this scope. Inspect full-resolution masters, dark and light
composites, and animation playback. Reject visible enlarged source pixels, blur presented as reconstruction, unstable
silhouettes, crawling centers, invented particles, phase reordering and changing canvas registration.

These textures are alpha-sensitive. Preserve soft falloff, detached specks, quiet frames and approximate integrated
color/opacity energy across the sequence. Do not infer additive blending from a filename, force every nonzero pixel
opaque, or use the hard-silhouette cleanup intended for solid props. Delivered RGBA alpha is preferred; an opaque
return requires a reviewed companion mask and premultiplied-alpha-safe resizing.

The ten `skull` frames currently contain preserved RGB with zero alpha. Keep that family blocked until its original
blend/alpha semantics are resolved. Do not invent opacity merely because the hidden RGB depicts a visible skull.
Likewise, a completely empty native frame is evidence to preserve, not permission to invent a transition.

## Family-specific review

- Flames, breath and smoke: preserve motion direction, density, flame base or emission origin, and fading exhaust.
  Review the complete loop; a good still with discontinuous playback fails.
- Spirit, skull, feather and flies: preserve recognizable identity, center/attachment point, relative scale and motion.
  Tiny flies must not become unrelated insects or acquire a painted background.
- Rings, stars, flares, washes and dots: preserve radial symmetry where present, small dim stages, hue, falloff and
  empty space. Prefer deterministic reconstruction over generative redraw when the source is essentially analytic.
- Long sequences such as `oval` and the torch flames: split only with an accepted overlapping phase reference. Review
  the join as part of the full playback.

Suggested first pilot is `spirit.spr`: eight 64×64 frames, a supported one-shot runtime effect and a short coherent
sequence. Validate it before the longer Column-of-Fire torch families. Single-frame blurred stars are low priority;
increasing resolution alone does not justify changing already smooth analytic art.

## Runtime acceptance

Before accepting an installed family:

1. Verify descriptor id, frame order, FPS and logical dimensions against the binding manifest.
2. Verify the restored PNG dimensions are the declared integer scale of the logical canvas and all frames retain the
   same registration.
3. Compare native and restored variants in the same effect, transform, camera and update rate. World bounds and timing
   must match exactly.
4. Check both alpha and additive recipes that reuse the resource; a texture is not allowed to encode one recipe's
   blend assumption into all consumers.
5. Inspect motion at normal speed and frame-by-frame, on light and dark backgrounds, near and at distance.
6. Record texture memory and overdraw diagnostics. Higher resolution may increase texture storage and sampling cost,
   but it must not change particle count, draw count or logical quad area.
7. Retain the native DTX-derived PNG as a selectable comparison/fallback asset; never destroy source evidence.

This guide owns artwork preparation and review for the listed FXF resources only. Changes to FX simulation, blending,
attachments, looping, models or projectile behavior are separate engine work and must not be hidden in restored images.
