# MM6–MM8 static texture restoration: 2× and 4×

Generate fresh, faithful artwork while preserving the map's material scale, layouts and joins. A large PNG with
enlarged raster grain is a failed result. Generate shared materials once, then build related textures from those
same materials and independently restored foreground artwork.

Use the current imagegen skill and its built-in tool workflow. Save exact prompts, input roles and unchanged
returns in the project. Do not switch to CLI/API generation for size control without the user's authorization.

This playbook covers static BLV face textures and ODM BModel face textures: dungeon walls/floors/ceilings, building
facades, timber, doors, trim and artwork. The art workflow is shared; the geometry, visibility and runtime capture
paths differ. Outdoor terrain transition masks have their own [terrain handoff](TERRAIN_RESTORATION_HANDOFF.md).
Sprites use the [sprite restoration workflow](../sprites/restoration_jobs/README.md).

**Status, 2026-10-08:** working rules from the [Abandoned Temple study](mm6_abandoned_temple_textures/README.md)
and the user's subsequent quality review. Shared-background compositing is the requested default. The complete
2× study is retained as comparison evidence; it is not blanket visual approval. The larger-section trial failed
the coarse-grain check. The subsequent [focused 4× demos](mm6_abandoned_temple_textures/review/x4/index.html) cover
12 candidates and 48 matching native captures. They validate shared composite backgrounds and source/export sizes;
the later [complete 4× pack](mm6_abandoned_temple_textures/review/full_x4/index.html) covers all 62 static textures,
with 21 camera poses in both lighting modes. Generation/export coverage and visual approval remain separate.

## What the trials actually established

| Finding | Evidence and consequence |
| --- | --- |
| Alpha must be requested and checked | Padded trim/chest returns have actual RGBA transparency. Keep raw alpha; distinguish transparent authoring padding from an opaque wall export. |
| One master improves connected-piece consistency | Chest cap/body pieces were cut from common front/back/lid masters. Shared cuts preserve the source connection; they still need native mapping and repeat checks. |
| Canvas size is not usable artwork size | A 1774-wide extended trim had only a roughly 545-wide selected body. It could support 2×, but not a 1024-wide 4× body. |
| A requested resolution is not a guarantee | Requests for 2048 returned 1254-square or 1774×887 / 887×1774 images in this run. Inspect every actual returned size and crop. These observations are not a universal tool limit. |
| Noisy references can contaminate newly generated art | Native nearest-neighbour section guides plus coarse restored material references produced stippled plaster, carpet and tapestry despite negative prompt instructions. Those outputs are rejected. |
| Cleaner material direction helps | A fresh plaster sample with no noisy raster reference and native-only carpet layout reference produced smoother surfaces/continuous ornament. These are style samples, not approved registration/seam proofs. |
| Re-generating the whole decorated wall changes its background | The focused 4× tapestry/windows reuse the exact shared wall base, verified outside native artwork bounds and captured in game. A colour/style reference alone is insufficient. |
| Large output does not require an equally large single return | The full 4× wall repeats a new 1024-square plaster body; the 2048-square stained floor repeats the exact new checkerboard and adds an independently generated alpha light footprint. No component is enlarged. |
| Separate sections can drift at their shared cut | Two carpet halves had different border row heights and a split medallion. A new centre repair plus common ornament bands corrected the assembly; the mirrored bands are recorded explicitly. |
| A seamless prompt is only the first attempt | Paving, pale stone and irregular masonry needed half-period offset guides and imagegen repairs at the centre cross. Check the inverse-shifted repeat again. |
| A stone field can include a finite panel edge | The [MM6 granite-panel check](mm6_textures_x4/review/third_batch/index.html) found a uniform one-native-pixel outer joint plus a two-pixel mitered bevel. Keeping only the flat joint lost the panel relief; a fresh complete panel restored it. Inspect several native edge rows before classifying a material as unjointed. |
| Finite stones can be cut along their real grout | The slate/rose diamond floor repeats complete stones cut from a new master, with the original one-pixel outer joint retained. This avoids mismatched arbitrary cuts through the mineral body. The cut geometry and both source budgets are recorded; rejected alpha returns supplied no artwork. |
| A texture listed on a face may be hidden | Goblinwatch's marble back face is behind a different front panel. Those captures cannot approve marble; use the unobstructed ceiling in `6t1.blv`. Verify actual visible geometry before choosing a comparison location. |
| Small finite variants can share a generation sheet | The [four-panel granite batch](mm6_textures_x4/review/fourth_batch/index.html) cuts separate bodies from fresh returns, each with more source pixels than its final placement. Measure the native joint width before judging brightness: an overly narrow generated joint changes the full-tile average. Select individual crops; reject brighter/darker siblings independently. |
| A material sampler has a narrower acceptance scope | The four-panel sampler keeps BLV bytes and UVs unchanged and labels every temporary texture-key alias. It verifies generated finish, brightness and native logical period in normal/Torch Light, but does not approve the original occluded room assignments or their joins. Keep those original-placement checks pending before installation. |
| A complete-panel style reference can dominate a variant | In the [remaining granite trial](mm6_textures_x4/review/fifth_batch/index.html), it introduced dark teal clouds into pale stone and a silver bevel into a dark brown panel. Use an unframed fresh body crop for finish guidance, keep the variant's geometry/palette authoritative, and inspect the actual result. Requested numeric colour corrections also overshot; measured export brightness and native views decide selection. |
| A selected seam repair can retain the original dim body | The [cave wall/floor comparison](mm6_textures_x4/review/sixth_batch/index.html) uses only recorded centre-cross strips from the imagegen repairs. Exact cuts, inverse offset and one direct reduction passed raw boundary, x4 repeat and original-map normal/Torch checks. The brighter complete repair returns remain unused. Hard crop boundaries still require visual review; this is not automatic seam acceptance. |
| A registered component can still fail material acceptance | The [unselected grating study](mm6_textures_x4/review/seventh_batch/index.html) separates the rigid recess and plants over the exact plain wall. Its source sizes and fresh detail pass, but original-map recess brightness remains about 16.5% higher and whole-face samples about 33% higher. Numeric darkening also shifted rusty iron to charcoal. Keep these returns unselected; registration alone does not approve brightness or native recess appearance. |
| Real alpha can contain faint stray edge pixels | The same grating study has genuine zero-alpha gaps but a few alpha-1 pixels reach the left/right/bottom tile bands. Validate the intended empty bands as well as channel extrema and the visible silhouette. Its family continuity remains unapproved; do not claim identical exposed edge bands from the presence of an alpha channel alone. |

Keep the [rejected trial prompts](mm6_abandoned_temple_textures/x4_detail_jobs.json),
[cleaner sample prompts](mm6_abandoned_temple_textures/x4_clean_jobs.json) and
[unscaled crop comparison](mm6_abandoned_temple_textures/review/x4/quality_comparison.png) as calibration.
The quoted `carpt01_x4_section1_v1` prompt is a failed example, not a recipe to repeat.

## 1. Inventory native usage before generating

Decode the map's texture names, dimensions, visible face uses and U/V offsets. Include event-switched names where
applicable. Group related textures by material and original edge relationships; inspect other maps using the same
keys before replacing them. A texture shared by several maps cannot be validated from one room alone.

Retain native references, current runtime references and a few in-game locations. Record native width/height,
world/package, target scale, wrap axes, artwork bounds, base material, related pieces and original transparency.
Use half-open pixel rectangles `[left, top, right, bottom]` in the manifest, with a stated origin and orientation.

| Texture role | Authoring approach | Main check |
| --- | --- | --- |
| Repeating plaster, stone, timber, floor | One material master for each native family | Correct world scale and wrap phase on required axes |
| End/body/end trim or connected chest pieces | One registered continuous master, then cut native pieces | Cap/body joins and separately the body's repeat |
| Painting, tapestry, window frame, plaque on a wall | Shared wall template plus true-alpha foreground | Identical exposed background and native foreground placement |
| Stain, marking or ornament over a repeated floor | Shared floor plus true-alpha marking | Tile grid continues under/around the marking |
| Finite carpet, complete painted panel or door illustration | One complete artwork; preserve original bounds | Motifs, border proportions and original edge contacts |
| Originally cutout material | Preserve meaningful native opacity | Correct silhouette and no colour-key halo |

Do not force a finite carpet to tile. Do not put a cap inside a repeated body. Water and other renderer-owned
animated materials require their own material/animation treatment; an opaque static repaint is insufficient.

## 2. Choose the master pixel budget from the final crop

2×/4× means twice/four times **each native dimension**, with unchanged logical dimensions in the map.

| Native | 2× export | 4× export |
| --- | --- | --- |
| 256×256 | 512×512 | 1024×1024 |
| 256×512 | 512×1024 | 1024×2048 |
| 512×256 | 1024×512 | 2048×1024 |
| 512×512 | 1024×1024 | 2048×2048 |
| 256×32 strip | 512×64 | 1024×128 |

Check both dimensions **after** cropping padding, extracting a body and applying any rotation. A 2048-wide
canvas containing a 500-wide useful panel is not a 4× master for a 256-wide native texture. Every generated
component must provide enough actual source pixels for its final placement, including thin trim height.

Prefer one sufficiently large master; derive both tiers by reduction. Never enlarge a 2× export, stretch a
smaller crop, sharpen it or add synthetic noise to claim 4× detail. Keep any enlarged native layout guide labelled
as a guide, outside accepted artwork. It supplies geometry, not new texture detail.

For narrow `<====>` masters, budget the repeated body first. Give it most of the useful width; reserve enough
room for the attached ends. Three repeats plus caps can consume the source pixel budget before export.

If the built-in generator returns insufficient size, do not silently change generation providers or resize up.
Try a better allocation of the canvas, or a registered multi-section experiment as described below. Retain the
undersized result with its rejection reason.

When the native material really repeats, assemble the large export from native-detail body tiles and separate
caps or overlays. Preserve the original period and world scale: repeating a 512-pixel body twice is valid only if
that body represents the corresponding native half, not a reduced version of the whole texture. A finite carpet
still needs its complete composition. Budget and review the joins of registered sections independently.

For wrap repair, roll a fresh tile by half its width/height so its outer joins become the central cross. Ask
imagegen to reconnect that cross while preserving the outer context, reduce directly to the target tier and
reverse the roll. This is another artwork edit, not an automatic guarantee: repeat proofs must catch displaced
stones, colour bands or newly introduced seams. Do not blur, sharpen or procedurally paint over a failed join.

## 3. Establish one base for every material family

Start with a representative plain material, not a composite wall containing a painting. Use native material
identity, broad colour, courses/grain and scale; regenerate fine surface detail. Describe the physical surface
directly: matte lime plaster, continuous oak fibres, worn limestone, painted glass or fine cloth.

For plain plaster, the no-raster-reference sample avoided importing the original gold-like speckle. For patterned
stone/wood, retain structural guidance: mortar boundaries, course heights, plank spacing and orientation matter.
Use a clean outline/region guide where possible, or explicitly label native art as layout-only. A previously
generated image becomes a material reference only after it passes the 1:1 check. Do not feed a rejected grainy
result back into the family as an "approved style".

Use restrained, even diffuse colour. Preserve the game's material identity and palette without baking in bright
directional highlights, deep relief shadows or a new lighting gradient. The game supplies lighting; colour-only
art does not create a new normal/roughness response. Fine detail should support the material, not cover it in
confetti, faceted pebbles or bright grain.

Review a 3×3 repeat at its actual export scale and the raw master at 1:1 before multiplying variants. A low average
edge difference is a diagnostic, not proof of a seamless tile. Inspect courses, mortar, grain and colour phase.

## 4. Build composite textures from a shared background and separate alpha artwork

For plaster + wood dado + tapestry/window/painting, build the **plain complete wall template first**. It contains
the accepted plaster and, where required, the same wooden dado at the measured native height. Reuse that exact
template in each family member. A composite should not ask imagegen to invent its own surrounding plaster.

```text
accepted plaster master + accepted dado/trim at native coordinates
                              ↓
                    one plain wall template
                              ↓
             copy + true-alpha tapestry/frame overlay
                              ↓
                  opaque composite wall export
```

Generate only the foreground, including its frame, with `transparent_background: true`. Request no surrounding
wall or floor. Keep intentional opacity inside the painting/window scene; a dark painted background is not a hole.
Keep real transparency outside its silhouette and in actual gaps. Validate the PNG channel, not its displayed
checkerboard: RGBA and some zero-alpha pixels are necessary, but also inspect the alpha geometry and edge colours.

Place the foreground deterministically using the native rectangle/mask and a recorded crop/rotation. For an
origin at the tile's top-left, a native placement `[x0,y0,x1,y1]` becomes `[s*x0,s*y0,s*x1,s*y1]` at scale `s`.
Fit accepted foreground detail by reduction only. If it cannot cover that rectangle without enlargement, regenerate.
Do not compensate for an incorrect frame layout by distorting a painting, moving the native border or cropping a
subject away. Preserve source overlays and placement metadata separately from the flattened result.

Where overlay alpha is zero, the composite must retain the base pixels exactly. For a decoration clear of the
tile boundary, the exposed edge bands should be identical to the plain wall template. Also inspect the soft
alpha transition; a hidden white/black RGB fringe can still produce a halo after filtering. Filter transparent
layers with premultiplied alpha, then use the compositing convention consistently.

If adjoining native textures need a phase offset, sample the **same** base master at that recorded phase; do not
generate another wall or merely colour-match it. Identical background pixels only solve the art side of a join:
existing face U/V offsets, projection and native family borders still need inspection. Keep originally different
material families distinct rather than assigning one plaster to every building.

Flatten these layers into the ordinary texture PNG for the existing renderer. Authoring layers do not require a
new gameplay decal, shader, extra runtime sampler or transparent wall. The original opaque wall/floor stays opaque;
original cutout textures retain their own meaningful opacity. Do not key out dark pixels from opaque artwork.

Apply the same method outdoors: facade + sign, masonry + doorway/frame, roof/wood panel + ornament. A complete
carpet is finite artwork in its own right; it does not need an unrelated wall behind it.

## 5. Connected pieces and larger sections

For native cap/body/cap families, generate the whole connected construction once. Mark cuts from measured native
proportions, preserve course/grain continuity and export the existing names. The body must also repeat with matching
boundary phase; shared cap cuts alone cannot establish that. Do not hide a bad join with blur or colour grading.

For a finite artwork larger than one returned image, registered sections are an **experiment**, not an accepted
default. Each section needs enough core pixels, surrounding context, exact native coordinates and a consistent
composition reference. Use neighbouring accepted sections as continuation references, not independently generated
versions of the same wall background.

The first Abandoned Temple attempt used a 256×256-native core with 16-native-pixel context on every side:
288×288 total, core fraction `1/18..17/18`. A 1254-square return provides roughly 1114-square core pixels, sufficient
by size for a 1024-square export. That calculation did **not** prove quality, registration or section continuity.
The carpet/plaster/tapestry candidates were rejected for coarse stippling; the full assembly was not accepted.

Prefer sections of the foreground only over a shared base. Check the generated content against the guide: the
model can move a frame or remove context even when the prompt asks it not to. Inspect joins at 1:1 and full scale;
regenerate a mismatched section or use an explicitly reviewed imagegen correction. Overlap is context, not permission
to conceal a wrong motif using broad feathering. Never stretch a short section to fill the remaining master.

## 6. Prompt patterns

These are starting briefs, not guarantees. Supply exact dimensions, role and native bounds for the current asset.
The positive material direction matters; a long "no pixelation" list did not rescue the failed noisy references.

**Plain material**

```text
Use case: photorealistic-natural.
Asset: a flat repeating game albedo tile of [native material].
Create new, clean high-definition material artwork. Preserve [courses/grain direction/native scale].
Surface: [matte continuous plaster / fine oak fibres / worn limestone], restrained [native palette],
subtle broad wear and fine unobtrusive detail, even diffuse illumination.
Opposite [U/V/both] edges must continue the material naturally. Full bleed opaque.
No perspective, vignette, baked highlights/cast shadows, text or watermark.
Avoid enlarged raster grit, faceted grains, stippled noise, sharpening halos and pixel-art.
```

**Foreground for a composite**

```text
Use case: precise-object-edit.
Asset: [native tapestry/painting/window frame] as a separate true-alpha game texture layer.
Reference 1 defines ONLY its composition, frame proportions, subjects and palette.
Redraw the artwork with continuous fine contours and newly resolved material detail;
ignore the small reference's raster dither and coarse grain.
Render only the artwork and its frame. No surrounding plaster, wall, floor or backdrop.
True PNG alpha outside the silhouette and in real gaps; keep intentional opaque painted interiors.
Flat orthographic view, restrained diffuse colour; no extra border, perspective, letters or watermark.
The usable foreground crop must cover [target pixel width × height] without enlargement.
```

**Connected construction**

```text
Use case: precise-object-edit.
Asset: one continuous [left end + repeating body + right end] master.
Reference 1 is a clean placement guide; cuts are at [registered fractions].
Preserve native proportions, course/grain directions and attached joins. Give the body [pixel budget].
Body left/right boundary phase must match for repetition; caps remain outside that period.
Generate fresh fine material detail with restrained diffuse colour.
True alpha outside the complete construction; opaque material inside. No separators at cuts or new caps.
```

**Finite illustrated artwork**

```text
Use case: stylized-concept.
Asset: freshly illustrated [complete native carpet/painted door/panel].
Use the native image only for subject placement, motif centres, border proportions and palette.
Draw continuous refined contours, legible ornament and subtle fine surface detail from scratch.
Preserve the entire composition and edge contacts. Do not sharpen or reproduce raster grain.
Flat diffuse texture, no invented frame, perspective, embossing, lettering or watermark.
Full bleed [opaque / native meaningful alpha], usable artwork at least [target dimensions].
```

Do not add a style reference merely because one exists. Inspect it first. Exact prompts, input roles and unchanged
raw returns belong in the study alongside candidate status/rejection reasons; tool output outside the project is
not a durable handoff.

## 7. Independent acceptance checks

Pass all checks before selection; failures remain candidates. Generating every name is coverage, not acceptance.

| Check | Required evidence | Reject when |
| --- | --- | --- |
| New artwork | Unscaled source crops plus complete composition | Raster blocks/dither persist, grain is sharpened, or high resolution is filled with coarse stippling |
| Native fidelity | Original beside generated layout at matched logical scale | Changed motifs/subjects, extra frames, shifted courses, wrong border widths or decorative redesign |
| Source budget | Actual return size, useful crop and component placement sizes | Any accepted component needs enlargement to reach 2×/4× |
| Background ownership | Shared base + overlays + recorded placement | A decorated wall contains separately regenerated exposed plaster/masonry |
| Alpha | Channel extrema, silhouette and edge inspection | Painted checkerboard, unwanted opaque wall in an overlay, cut-out dark paint or fringe |
| Continuity | Repetition proofs and connected-family/section joins | Visible bands, displaced mortar/grain, mismatched motifs or a feathered repair concealing drift |
| Runtime scale | Correct mounted tier and unchanged native logical dimensions/U/Vs | Brick size, ornament position or texture repetition changes with tier |
| In-game appearance | Fixed before/after cameras near, medium and farther away | Noise shimmers, details disappear, art is too bright, or wall/foreground joins break under lighting |

For the 1:1 check, inspect material, silhouette and ornament separately. Genuine surface grain can exist, but it
must read as newly resolved material at the intended distance, not a repeated raster grid, crunchy pebble coating
or generic noise overlay. Smooth continuous lines should survive without stair-step blocks and halos. Do not call
a texture good simply because it was generated rather than upscaled; newly generated art can fail the same gate.

Use a small representative batch first: plain material, connected trim and a decorated surface. If the style fails,
fix the references/material direction before continuing the family. Approval of a crop's material finish does not
approve its composition, seams or the rest of the pack.

## 8. Export, stage and compare

Keep masters, true-alpha overlays, composition placements and final exports in the study. Deterministic authoring
may crop, rotate, reduce, repeat an accepted seamless base, alpha-composite accepted layers and assemble review
proofs. Do not procedurally repaint, sharpen, grade unrelated backgrounds into a false match or synthesize detail
to satisfy the source budget. Final exports retain native aspect, canonical filenames and required alpha semantics.

Keep the runtime tier honest: a `textures_x4` export has four times each native dimension and resolves to the same
logical size. The existing [scale tier](../../engine/AssetScaleTier.h) and
[map texture loader](../../game/maps/MapAssetLoader.cpp) distinguish physical pixels from logical dimensions for
indoor and BModel textures. Verify the resolved path/tier in the stage; copying an image to the wrong tier changes
its logical scale. Do not change BLV/ODM UVs just to compensate for mislabelled artwork.

Compare 2× and 4× reduced from the same accepted master when measuring resolution benefit. Different redraws are
an art comparison and cannot isolate the effect of 4×. Retain 1:1 crops, 3×3 repeat proofs, shared-family assemblies,
the original master and exact camera positions. Mips/filtering must stay consistent.

For indoor checks use normal lighting and actual Torch Light at matching poses. Inspect close wall/floor detail,
corners, dado height, window/painting surrounds, angled surfaces and distant repetition. For outdoor BModels also
inspect sun and shade, facade joins, roof edges and matching buildings sharing texture names. Keep weather/time
and render settings fixed for before/after. Preserve original U/V phase problems as separate findings rather than
claiming the art restored those joins.

Use the authorized [desktop launcher](../../tools/RUN_GAME.md) and native screenshot tours. Stage only candidates
that passed art checks in isolated mounts; production `assets_dev` and release bundles remain separate. Record
export dimensions/alpha/hashes, selected sources/layers, map uses, capture poses, binary and settings. A short
reproducible export assertion and representative native captures are useful; asset-only changes need no engine
rebuild unless the loader/renderer is changed.

4× has four times the texels of 2×. PNG file size is not GPU residency; compressed mip payloads need an actual
compressed upload path and visual review. [Measured dimensions and calculated Temple memory costs](mm6_abandoned_temple_textures/review/full_texture_cost.json)
are planning evidence, not an FPS benchmark. Keep art acceptance and renderer compression/performance work separate.

## 9. Brightness and material relief

The [2026-10-08 full-pack audit](mm6_abandoned_temple_textures/review/full_x4/brightness_audit.json) confirms
unintended tonal drift. In identical screen patches, masonry-vault wall mean display luma rises from 14.5 to
33.7 without Torch Light and 29.8 to 68.0 with it. Rubble-floor mean rises from 9.3 to 17.5 and 44.8 to 81.7.
These are stored RGB measurements with Rec.709 weights, not multipliers of physical lighting intensity.
The capture pairs use the same binary, map, save per lighting mode and settings except tier/private paths.

Measure native art, current ESRGAN and the redraw separately. The native references are already brighter than
the ESRGAN versions: masonry means are roughly 31–34 versus 19–21, while `crdflr4` is 60 versus 45. The fresh
art still rises to roughly 42–48 and 84 respectively. Removing old painted black crevices without providing
replacement material shading changes the dungeon atmosphere. More source pixels do not require brighter art.
Inspect mean/midtones and dark crevices independently; a globally darkened room or a mean-only texture correction
cannot establish fidelity. Calibrate related bases and decorated variants together, then repeat both light modes.

### What the current renderer can do

Ordinary [indoor surfaces](../../game/shaders/fs_indoor_textured_lit.sc) multiply base RGB by ambient,
vertex-baked RGB and distance-attenuated point light. They have no normal sampler, surface-normal input or
normal/light incidence term. [Outdoor building surfaces](../../game/shaders/outdoor_textured_fog.sh) have
geometric sunlight but no normal-texture detail. Both use the same BModel texture upload profile at all tiers,
with legacy display-space mip averaging; the 4× tier has no separate exposure or colour-space policy.

The engine already has [tangent-normal sampling](../../game/shaders/fs_model.sc) for model materials and
[normal-vector mip filtering](../../engine/ImageMipmaps.cpp). Reuse those capabilities where applicable;
ordinary map surfaces need their own optional material binding and calibrated directional lighting. Existing
baked RGB does not contain the fine incoming direction needed for normal response. A Torch Light pilot is a
small first check; it does not prove relief in an ambient-only room or replace material crevice occlusion.

### Smallest useful trial

1. Calibrate the colour/crevice contrast of `d2wlactr`, `d2wctra` and `crdflr4` in the isolated stage.
2. Author relief/height aligned to those exact bricks, mortar and rubble; derive numerical tangent normals with
   matching boundary wrap and physical scale. Dark pigments, stains and painted shadows are not height. Keep
   exposed shared-wall relief identical beneath composited ornaments; painted mural colours stay flat.
3. Add optional companions through shared BLV/ODM material loading and the existing draw paths. Supply a correct
   surface/UV basis, normal-specific mips, linear sampling and a restrained directional light response. Materials
   without companions retain their existing appearance. Avoid an unrelated renderer or new draw calls.
4. Compare fixed camera/light poses plus a moving Torch Light, rotated/mirrored UVs, repeat joins, doors and distant
   filtering. Measure frame time and GPU residency before extending the trial to all materials or mobile.

Normal mapping changes shading, not silhouettes or collision. Roughness and material occlusion can be later
additions if the trial warrants them; normals alone do not darken ambient crevices. Fully linear/PBR lighting
would require a separate calibration of legacy illumination and grading, not merely switching the sRGB upload flag.
The [Khronos material specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#materials) defines
linear normal/occlusion data separately from sRGB base colour;
[SideFX's comparison](https://www.sidefx.com/docs/houdini/shade/normalmaps.html) explains normal/displacement limits.

For the trial's three independent normal maps, BC5 plus complete mips would use about 0.42 MiB at native 2× or
1.67 MiB at 4×. The theoretical all-62 totals are 11.70/46.79 MiB respectively, versus 46.79 MiB for all 4× BC7
colour or 187.17 MiB for the current uncompressed four-channel 4× colour. These are dimension-based allocations,
not measured residency; aliases, driver overhead and CPU copies are excluded. The ordinary world upload currently
uses uncompressed textures, so BC5/BC7 savings need an actual compressed upload path. Both formats use 16-byte
4×4 blocks; supported formats vary by device ([bgfx texture formats](https://bkaradzic.github.io/bgfx/bgfx.html#textures)).
Expect one extra normal fetch plus lighting arithmetic on mapped pixels. Mips reduce distant bandwidth and
aliasing, but not that arithmetic. No FPS cost has been measured and no normal maps were generated in this audit.


### Material-only correction: completed Temple trial

The [corrected 62-texture study](mm6_abandoned_temple_textures/review/material_correction_x4/index.html) updates
41 exports and retains 21 existing 4× materials, with no renderer or material-map work. The same masonry/rubble
patches now stay within approximately 5% of ESRGAN display luma in both lighting modes. See the
[measurements](mm6_abandoned_temple_textures/review/material_correction_x4/brightness_audit.json).

Treat surface finish and brightness as separate quality checks. A darker texture can still have swollen timber
ridges, blanket stone pits or glittery mineral facets. Reject those returns. When an edit carries the wrong
fine grain forward, regenerate from the native coarse layout and a specific material description, using native
pixels only as placement/palette guidance. The successful warm timber retry used fine straight fibres and
subtle knots; the slab used broad worn planes with restrained mineral variation. Request diffuse material tones,
not a new room lighting treatment. Judge exact exported crops and in-game appearance, not transparent-canvas means.

Calibrate the base and separate pillar/relief pieces together. Preserve the distinct native dark paving and warmer
wood variants instead of aliasing superficially similar layouts. Rebuild dependent composite textures from the
corrected shared base; exposed background pixels must remain identical. Keep connected chest parts cut from one
registered master per connected family. Retain true-alpha source masters and exact crop budgets.

For a repeat repair, offset the accepted body by half its period so the broken join sits in the centre. Ask imagegen
to redraw only that join, then retain only the repaired centre region if the returned surrounding surface changes.
Assemble it over the accepted body and inverse-shift once. Record both sources and the selected rectangle; inspect
the repeated export. This preserved the matte grey trim while repairing its polygon mortar paths. Never call an
entire return accepted when only one registered component is used.

Capture the final pack after the last art/export change. Reuse frozen baselines only when hashes, camera/save,
binary, resolution and lighting settings are validated. Label old comparison stages honestly, including excluded
context assets. Water and sky tier carriers are unchanged context, not genuine 4× restoration. Do not use global
exposure, filtering changes or shader work to compensate for a brighter master in an art-only task.
