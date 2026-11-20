# Calibration and exceptions

## What the preparation checked

The complete inventory and current native frame tables were read. Contact sheets were inspected across MM6–MM8
scenery, props, ground items, projectile/effect families and UI indicators; correctly paletted audit pages are saved
in `audit/`. This is a category/shape audit and native metadata check, **not** an artistic acceptance of future output.
Native references inside each job remain the shape/color authority when a table's descriptive name is vague.

The existing New Sorpigal enhancements establish the look: faithful original masses, much better material detail,
dark natural greens/browns, clean thin outlines, full native logical dimensions. Bigger/smoother alone is insufficient.
The concurrency trial showed why: its apple kept large pixel staircases; its amber/fossil acquired false holes.
The frozen prompts explicitly forbid both. The drafts remain review jobs, separate from the accepted scenery.

## Specific visual rules

Inspect the full-resolution master as well as the final export. Reject large rectangular source-pixel shading
patches and stepped contours: a smaller export can conceal them without fixing the artwork. The red glass
`g00260_v0_s0/attempt_03` is a rejected example; its earlier acceptance was revoked after user review.
Use a targeted `pixel_steps` repair and explicitly identify the failed regions. Keep every previous master.
New acceptance requires a `master_detail` observation; this records human/agent visual evidence, not an automated
pixel-art detector. Older acceptance records do not prove this inspection occurred.

If a repair keeps copying the failed candidate's pixel blocks, try the ordinary native-only `payload` with a brief
explicit reconstruction constraint instead of supplying that candidate again. Archive the exact augmented prompt.
The path marker `g00401_v0_s0/attempt_03` improved with this approach. This is an observed option, not a guarantee:
still inspect identity, material, full-resolution detail and final placement before acceptance.

| Asset | Preserve / check |
| --- | --- |
| Trees/bushes | Species, silhouette, forked trunk and crown gaps; autumn, dead and snow states remain distinct. Keep fine branches. |
| Flowers/cacti | Flower/fruit color, original clumps and spines. Purple petals are real material, not necessarily key spill. |
| Rocks/crystals | Native asymmetry, facets and dark mass; crystal translucency is not a license to cut holes through dark facets. |
| Barrels/furniture/items | Exact angle, proportions, supports, hoops and handles. Small items retain their ground-facing orientation. |
| Fire/cauldrons | Rigid tripod/pot/chain/pole stays coherent. Animate flame/smoke without dissolving the black iron support. |
| Pedestals | Stable shaft/plinth and material; source-colored orb/fire animates. Different pedestal shapes are not interchangeable. |
| Flags | Pole stays fixed; cloth follows source folds and sequence; native colored flag identity stays. |
| Fountains/shore rocks | Solid basin/rock does not change. Waterline, spray and localized footprint remain native. |
| Buoys | Keep native bobbing/swinging and repeated timeline frames; do not "correct" deliberate movement away. |
| Potted living/dead states | Same pot/material; plant state changes. These jobs share an accepted seed dependency. |
| Ships/views | Keep native stored views and runtime mirrors, not invented extra views. Known Sorpigal ship views are already reused. |
| Spell FX | Preserve small quiet stages and detached particles as well as the flash. No cinematic expansion, new halo or extra particles. |
| Solid projectiles | Arrows, blades, bones, boulders and physical cores remain physical. FX table membership does not imply additive blending. |
| Smoke/water/glows | Soft alpha must survive cleanup. Smoke can contain dark material: black-to-transparent is not a universal extractor. |
| UI | Preserve painted panels, symbols, hands, hourglass, borders and negative space. Native canvas/placement, not a feet-on-ground rule. |
| Rain/snow | Preserve full-frame particle field/density, native movement and empty regions; no landscape. These are large 640×400 source frames. |

Known source exceptions: `tree06a` depicts fruit despite its "EmptyFoodTree" descriptor; preserve native state art.
The sword-in-stone/removed-sword pair shares an already accepted boulder with the native bottom alignment.
`7pending` is fully transparent; no art is invented. Some blank group names still resolve real items/scenery.
Native labels such as "Fire Spike" are hints; the actual sprite can look like a solid spiked object.

## Alpha and alignment: quick checks, not a new investigation per image

Delivered alpha wins. Keyed RGB contains baked edge color before our resizing, so replacing pure magenta alone
is inadequate. Unmix the matte, preserve real material colors, then resize premultiplied color/alpha together.
The helper supports the original magenta method and channel-permuted cyan/yellow. A collision flag invokes the
prepared mask path when the tool returns opaque RGB; it is not permission to erase the conflicting material.
Review masks against the exact RGB output. An AI mask is also an estimate and may need a localized correction.

Soft extraction intentionally has no seven-pixel distance cutoff or forced opaque fringe color clamp. It cannot
uniquely recover arbitrary alpha from one composite; inspect small particles and faint tails against dark/gray,
and smoke against light. Do not automatically convert soft images to additive blending or run hard erosion.

All cells of a sheet use one scale and consistent native canvas placement. `process` reverses that layout and
preserves differing frame dimensions. A scale/translation correction applies to the whole job. A per-frame bbox
fit would normalize genuine movement and make rigid props breathe. A discovered implementation regression did
exactly that despite this instruction; it was removed on 2026-09-10. See [calibration](PLACEMENT_CALIBRATION.md).
Export keeps native size ×2 and metadata; logical world/UI size is unchanged. Center anchoring remains a per-use
table property, with native raw flags retained in `groups.json`, even when two uses share identical artwork.

Registration now uses premultiplied Lanczos resizing over the native rectangle. The previous bicubic EXTENT
transform undersampled fine detail during large reductions and produced speckling despite a good master.
Plants `g00422`/`g00423` demonstrated the defect; old exports are archived in `before_filtered_resize/`.
When a smooth master produces a noisy small export, reprocess a preserved revision before considering imagegen.
Retain recorded masks, layout overrides and common placement adjustments. Previously hand-corrected static
components or tone grades must be reapplied deliberately; do not blindly reprocess every accepted asset.

Warnings flag large coverage/bounds drift and insufficient generated pixels for the 2x target. Look at them:
thin antialiasing changes are expected, lost branches and large holes are not. A low-resolution returned sheet may
need fewer cells; request size is a prompt, not an API-enforced promise. Do not upscale a blurry master and call it detail.
Split only the affected job into explicit additional attempts/child jobs, preserving owner mappings and seed references.

## Palettes and coverage

Current referenced ACT palettes resolve to a single matching world source per ID; there were no conflicting
world ACT byte sets for these jobs. The current runtime tries the active-world ACT then the base path.
The ledger records actual palette files/hashes. **80 appearances** (leaf overlays and rain/snow) use embedded BMP
palettes because referenced ACTs 956/963/964 are absent, matching the runtime's BMP-palette fallback. This is explicit,
not a guessed ACT assignment. A future conflicting world palette stops preparation until world-specific jobs are added.

Image sharing is safe only after native dimensions and paletted RGBA identity match. All group usages, palette IDs
and per-use flags remain mapped; a shared image does not merge gameplay entries. No monster variant shader is
automatically applied to scenery/FX. Renderer blending, mipmaps, atlas packing and global/map installation are future work.

For the 152 unreferenced files, the preparation also searched exact stems in current game/engine code, rendering
and gameplay tables, and MM6–MM8 exported map events. Twelve stems produced matches: six `zapp` entries in the
**icon** frame table, three group/descriptor names (`sta1a`, `i2_fire`, `i6_magic`) rather than direct BMP references,
and generic words (`tower`, `lightmap`, `l1`). The icon copies also exist under `engine/icons`; this is not proof that
the `sprites/` copies are loaded. See [exact hits](audit/triage_exact_reference_hits.json) and
[grouped triage notes](TRIAGE_NOTES.md). No direct active sprite-file usage was established by that search.
Dynamic filename construction/import aliases remain possible. Each triage record includes related names and
exact BMP candidates. Inspect related original sequences once per family, not once per file.

Budget ordinary triage to one focused family lookup/contact review. Use local imports/tables as evidence; no broad web
research. If intended palette or role remains uncertain, retain an explicit unresolved entry and continue the main queue.
Do not casually classify a utility mask/lightmap as decorative art or invent a sequence from lexical filename order.
If a new referenced family is proven, add a small explicit extension with its palette, timeline, prompt, reference and
artifact; do not rebuild/restart the entire frozen queue. `resolve-triage` records the resulting artifact/disposition.
