# MM9 Armor Paperdoll AI Generation

This document defines the AI-assisted workflow for turning a promoted MM9 inventory armor image into fitted
OpenYAMM paperdoll artwork. It supplements the deterministic fitted-geometry workflow in
`MM9_ITEM_ADDON_INTEGRATION_GOAL.md`; it does not change item statistics, equip rules, table ownership, or offsets.

The Broderick's Hauberk female-human experiment established the process below. The important distinction is:

- the original MM9 PCX and promoted inventory image own the design;
- the selected MM6-MM8 fitted variant owns the target pose and placement and provides a candidate garment silhouette;
- an audited body-armor coverage mask removes footwear, feet, hooves, and any reference-only coverage that does not
  belong to the MM9 garment;
- AI redraws a coherent wearable garment inside that geometry; and
- deterministic post-processing and rendered review decide whether the result is usable.

Do not stretch the inventory icon across the paperdoll. Do not let an AI-generated alpha channel redefine the fitted
silhouette. Body armor is not footwear: it must leave the doll's boots, shoes, feet, claws, or hooves visible. This
rule applies to every doll type and both arm poses, even when the selected legacy armor reference happens to include
integrated leggings or boots.

## Legacy-Variant Placeholder Mode

Before commissioning an AI redraw, a usable placeholder may be made from an existing MM6-MM8 armor family. Use
`tools/mm9_import_discovery/generate_mm9_armor_legacy_placeholders.py` and its reviewed selections in
`tools/mm9_import_discovery/mm9_armor_legacy_placeholders.yml`.

Candidate ranking considers armor skill, normalized treasure tier, source-world preference, inventory-color distance,
accent hue, and inventory silhouette aspect. Ranking is advisory: visually audit the highest candidates on every doll
because an inventory-level match may still contain integrated trousers, footwear, an unsuitable sleeve layout, or an
overly distinctive artifact silhouette.

The selected legacy family owns the fitted geometry, alpha, material construction, shading, and ornaments. Apply the
normal garment-coverage and foot-exclusion masks, then conservatively recolor only existing trim toward the MM9 icon's
dominant accent. Do not project, stretch, or tile MM9 RGB over the legacy sprite. Preserve waist metal so circular hue
interpolation cannot turn gold fittings green. Render all ten suffixes through the table-driven previewer before using
the placeholder. This mode is intentionally source-derived placeholder art, not a final MM9-faithful redraw.

## Required Variants

Armor requires ten fitted files per promoted runtime item:

| Doll type | Weapon pose | No-right-hand-weapon pose |
| --- | --- | --- |
| 0 | `v1` | `v1a` |
| 1 | `v2` | `v2a` |
| 2 | `v3` | `v3a` |
| 3 | `v4` | `v4a` |
| 4 | `v5` | `v5a` |

Generate and review one suffix at a time. The non-`a` and `a` files are separate poses, not interchangeable aliases.
Type 5 is the non-equippable dragon paperdoll and has no armor variant.

## Required Inputs

Prepare these four images before invoking image generation. Keep this order so the canonical prompt remains accurate
and the image generator treats the mask—not the inventory icon—as the edit target.

1. **Audited target mask guide:** a two-color image derived from the deterministic `mm9_item_<id>v*.png` for the
   requested suffix after its coverage has been reviewed against the actual MM9 garment and the doll's
   body/footwear boundary. Gray is permitted armor coverage and exact `#FF00FF` is forbidden background. Its canvas,
   alpha-derived silhouette, pose, openings, and outer boundary are authoritative. Do not provide the stretched RGB
   placeholder as the geometry reference because it encourages the generator to reproduce that projection.
   Reject the target and correct its reference mapping or coverage mask before generation if it paints over feet,
   shoes, boots, claws, or hooves, or if a short garment is represented as an unrelated full-body suit.
2. **Rendered doll reference:** a preview or in-game screenshot of the current fitted candidate on the exact doll type
   and arm pose. This shows the body, layer placement, scale, and visible failure mode. It is context, not an edit
   target.
3. **Promoted inventory image:** the current transparent `mm9_item_<id>.png`. This is the primary readable design,
   palette, trim, and material reference.
4. **Original MM9 PCX:** convert the binding 64x64 PCX losslessly to PNG and enlarge it with nearest-neighbor sampling
   for visibility. This preserves the historical source design and prevents drift from the MM9 item.

Example PCX preparation:

```sh
convert path/to/SOURCE.pcx -filter point -resize 512x512 /tmp/mm9-armor-source.png
```

Use the exact source PCX recorded by the MM9 item import. Do not substitute a similar item. Select the fitted legacy
base from `tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml`; take placement offsets from the selected
reference's active `complex_item_pictures.txt` row. Until the armor generator consumes that table directly, first
synchronize the matching row in `mm9_item_body_equipment_visuals.yml`.

## Canonical Generation Prompt

Replace every angle-bracket placeholder. Keep all other constraints. For inputs to a generation tool, explicitly
label the four images by the roles above.

```text
Use case: precise-object-edit
Asset type: transparent paperdoll equipment-layer sprite for an MM6-MM8-style RPG

Primary request: Reconstruct <ITEM_NAME> as an aesthetically constructed, <DOLL_DESCRIPTION>-fitted wearable armor
overlay for paperdoll suffix <SUFFIX>. Paint a real garment into the supplied mask instead of stretching or projecting
the flat inventory icon onto it.

Input images:
- Image 1 is the audited two-color mask and the explicit edit target. Replace gray with coherent armor while
  preserving exact `#FF00FF` background. It owns the exact canvas, silhouette, arm pose, coverage, alignment,
  openings, and outer boundary, and it must end before the doll's footwear, feet, claws, or hooves.
- Image 2 is the current rendered <DOLL_DESCRIPTION> paperdoll and shows the exact body pose, placement context, and
  any current fitting defects. Use it only as pose and fit context; do not render the person into the output.
- Image 3 is the promoted inventory icon and is the primary readable design, color, material, panel, and trim
  reference.
- Image 4 is the original 64x64 MM9 PCX enlarged with nearest-neighbor sampling and is the binding historical design
  reference.

Subject: Armor layer only. Preserve <ITEM_NAME>'s recognizable materials, colors, trim, closures, panels, ornaments,
and other distinctive features from Images 2 and 4. Reconstruct those features as a real wearable garment fitted to
the body and pose in Images 1 and 2. Do not invent unrelated insignia or change the item's identity.

Style/medium: Hand-painted late-1990s MM6-MM8 paperdoll sprite; crisp low-resolution game-art
readability; coherent material rendering; subtle pixel texture after downsampling. Match the established OpenYAMM
MM6-MM8 paperdoll equipment style, not modern glossy 3D rendering or photographic realism.

Construction: Redraw the armor as intentionally tailored equipment. Construct the neck opening, left shoulder and
sleeve, right shoulder and sleeve, torso, waist, hem, and any lower panels as separate anatomical regions. Each sleeve
opening and seam must follow the actual arm direction in Image 1; never paste symmetric front-facing inventory sleeves
onto a different pose. Shape the armor coherently around the chest, waist, hips, arms, thighs, knees, and lower legs
only where those regions belong to the garment in Images 3 and 4 and exist in the audited Image 1 mask. End hems,
greaves, leggings, or skirts cleanly before the doll's footwear, feet, claws, or hooves; never paint body armor over
them. Use consistent material scale and perspective. Define sensible seams, hems, openings, belts, closures, panels,
and trim. A chainmail item must use consistent ring scale and direction instead of repeating or enlarging a flat
inventory texture.

Composition/framing: Front-facing armor layer in the exact paperdoll pose and elongated <WIDTH>x<HEIGHT> proportions
of Image 1. Keep the item upright. Fill every intended opaque region of Image 1 with coherent armor artwork. Preserve
the neck opening, arm openings, waist, leg separation, limb pose, and all exterior contours. Do not move, rotate,
shorten, widen, or exchange limbs.

Lighting/mood: Neutral frontal game-sprite lighting, slightly brighter from the upper left, with modest painted
highlights and shadows matching MM6-MM8 equipment layers. Avoid bright white rim lighting.

Scene/backdrop: One perfectly uniform solid `#FF00FF` magenta field. Do not draw transparency checkerboard tiles,
texture, gradient, cast shadow, or any other background. Magenta is a technical chroma key and must not occur in the
armor itself.

Constraints: Output only wearable body-armor pixels. No person, face, hair, skin, hands, feet, footwear, claws, hooves,
mannequin, weapon, shield, UI,
pedestal, environment, text, border, cast shadow, glow, or watermark. Keep all visible art inside Image 1's coverage
mask. Cover the complete intended mask; do not leave unpainted wedges that would require old stretched artwork as a
fallback. The result must look newly tailored and painted, not geometrically warped.

Avoid: Stretched or tiled inventory texture; oversized repeated mail rings; pasted flat inventory-icon details;
photorealism; modern glossy 3D; body parts; pose changes; sideways armor; detached pieces; white edge matte; baked
checkerboard; empty canvas around a tiny item.
```

Item-specific facts belong only in `<ITEM_NAME>` and the subject description inferred from the two source images. Do
not add arbitrary decoration. For Broderick's Hauberk, for example, the binding design facts were silver chainmail,
cobalt-blue edging and cloth accents, and restrained gold/brass belt fittings.

## Generation Rules

1. Generate one doll type and one arm pose per request. Do not ask one image to contain a contact sheet or all ten
   variants.
2. Use all four required inputs. The PCX is mandatory even when the promoted inventory image appears clearer.
3. Audit Image 1 before generation. Compare the mapped MM6-MM8 reference, the unarmored doll, a native plate-armor
   render such as item 878, and the MM9 item design. The target must not include the doll's footwear/foot/hoof region,
   and its torso/arm/leg coverage must make semantic sense for the actual garment. Fix the target first if it fails.
4. Treat the generated image as a high-resolution RGB design proposal. Image generators commonly approximate the
   silhouette, output a larger canvas, or bake a checkerboard despite being asked for transparency.
5. Never promote the generator's canvas or alpha directly. Reapply the exact audited target alpha deterministically.
6. Do not use unrelated MM6-MM8 armor RGB as fallback artwork. The fitted reference supplies geometry, not the item
   identity.
7. If the generated pose misses a substantial body region, regenerate or fit torso, skirt, sleeves, and individual
   legs as separate semantic regions. Do not globally stretch the entire design and do not expose the previous warped
   layer underneath it.

## Deterministic Fit And Fix-Up

The post-processing pass must be reproducible and must preserve the target file's dimensions and alpha exactly.

1. Crop the high-resolution result to the armor artwork, preserving its full vertical extent and intended pose.
2. Generate on one uniform `#FF00FF` magenta field and remove that chroma key deterministically before downsampling.
   Exact `#FF00FF` pixels become fully transparent directly. Mathematically unmix/despill only anti-aliased boundary
   pixels whose RGB was blended with the magenta field; do not use semantic background removal or a broad luminance
   key that erases bright metal highlights. Keep this correction in a narrow edge band and preserve intentional purple,
   silver, and pale armor details.
3. Align semantic regions independently when necessary:
   - torso and shoulder openings;
   - skirt, belt, or hip panels;
   - sleeves or arm guards;
   - left leg; and
   - right leg.
4. Downsample using a high-quality filter to the exact fitted canvas size.
5. Copy the authoritative audited alpha channel from Image 1 without modification. The generated alpha is discarded.
   Assert that this alpha does not overlap the configured per-doll footwear/foot/hoof exclusion mask.
6. Fill small missed-mask regions from neighboring newly painted armor pixels or a region-specific redraw. Never fill
   them with the old stretched overlay; the Broderick test showed that this creates white shoulder and leg wedges.
7. Remove only genuine edge matte:
   - inspect neutral near-white pixels adjacent to transparency;
   - replace halo pixels from nearby matching armor colors;
   - keep deliberate silver highlights and colored trim; and
   - scope a wider dehalo to the affected body region instead of darkening the whole item.
8. Ensure fully transparent pixels do not contain a white matte that can bleed through filtered sampling.

At minimum, verify the final geometry and alpha with ImageMagick:

```sh
identify candidate/mm9_item_<id><suffix>.png
compare -metric AE \
  \( target/mm9_item_<id><suffix>.png -alpha extract \) \
  \( candidate/mm9_item_<id><suffix>.png -alpha extract \) null:
```

The dimensions must match the target and the alpha comparison must report `0`.

## Rendered Feedback Loop

Stage candidates outside the active icon directory. Put each candidate under its exact runtime filename in a temporary
icon root, then use the table-driven previewer so placement and suffix selection match the engine.

For one doll type and no right-hand weapon:

```sh
python3 tools/mm9_import_discovery/render_paperdoll_equipment_preview.py \
  --item-id <ITEM_ID> --doll-types <DOLL_TYPE> --mode complete \
  --output /tmp/mm9-armor-no-weapon.png --report /tmp/mm9-armor-no-weapon.json \
  --extra-icon-root /tmp/mm9-armor-candidate
```

For its weapon pose:

```sh
python3 tools/mm9_import_discovery/render_paperdoll_equipment_preview.py \
  --item-id <ITEM_ID> --doll-types <DOLL_TYPE> --mode complete --right-hand-weapon \
  --output /tmp/mm9-armor-weapon.png --report /tmp/mm9-armor-weapon.json \
  --extra-icon-root /tmp/mm9-armor-candidate
```

Before declaring an armor complete, render both poses for all eligible doll types. Use `--character-ids` for any
portrait whose body geometry or placement may differ from the representative doll.

After each render, inspect at native scale and at a nearest-neighbor enlargement. This is an explicit AI visual-review
call, not merely an alpha/hash check. The reviewing model must see the complete equipped-doll composite together with
the candidate sprite, mask guide, inventory icon, and original PCX. Use
`tools/mm9_import_discovery/prepare_mm9_equipment_ai_review.py` to produce those inputs and the suffix-specific generation
and validation prompts.

The AI reviewer must inspect:

- recognizable source design, palette, material, trim, and rarity/detail level;
- coherent fitted construction rather than a stretched inventory texture;
- neck and shoulder openings aligned without covering skin or hair incorrectly;
- arm pose aligned, including the hand/weapon-side distinction between `v*` and `v*a`;
- waist and belt line aligned with the doll;
- skirt/crotch and leg separation free of bridges, holes, or background wedges;
- knees and any garment-covered lower legs following the correct limbs rather than crossing or swapping sides;
- the doll's own boots, shoes, feet, claws, or hooves remain visible and completely free of body-armor pixels;
- no white/checkerboard pixels, pale edge matte, detached fragments, or transparent holes;
- no pasted person, skin, hand, weapon, UI, text, or shadow;
- no clipping against the canvas; and
- correct placement and occlusion in the actual runtime layer order.

Passing deterministic checks does not imply visual acceptance. In particular, reject a result when it looks like the
inventory icon projected into the mask, even if its alpha matches exactly.

## Equipped-Composite AI Validation And Repair Prompt

Every suffix receives an AI validation result after deterministic fitting and full-doll rendering. If any defect is
found, use the generated `validation_prompt.txt` with these inputs in this exact order:

1. exact two-color mask guide as the edit target;
2. final equipped-doll composite;
3. current fitted armor sprite;
4. promoted inventory icon; and
5. enlarged original MM9 PCX.

The prompt makes the equipped composite authoritative for anatomy and asks for an armor-only corrected source on exact
magenta. It explicitly checks neck alignment, both shoulder joins, each sleeve against its actual arm direction, torso
perspective, belt/waist alignment, hem construction, lower-panel articulation, and the boundary above feet or hooves.
Run the corrected source through deterministic chroma keying and fitting again, rerender it on the doll, and repeat the
AI review. Do not promote a suffix until the AI inspection reports no projection, stretching, clipping, floating seam,
mirrored sleeve, crossed limb, or footwear overlap.

Record the accepted equipped-preview image and AI validation status in provenance. A final source and fitted sprite
without their equipped-preview evidence are incomplete.

Compare the candidate directly beside the previous preview. A JSON `ok` result verifies asset lookup and placement
data; it does not constitute visual approval.

## Choosing The Next Iteration

Use one targeted correction per iteration:

- **Regenerate the design** when identity, garment construction, material, perspective, or overall pose is wrong.
- **Regenerate a semantic region** when a torso, skirt, sleeve, or leg does not cover or follow the fitted geometry.
- **Use deterministic fitting** for crop, scale, exact alpha, component alignment, and canvas-size corrections.
- **Use deterministic dehalo** for a small white/checker edge artifact. Limit it to the affected region and preserve
  intentional metal highlights.
- **Reject and restart** when the result contains body parts, changes item identity, swaps limbs, or is based on an
  unrelated armor design.

A useful follow-up edit prompt is:

```text
Change only <AFFECTED_REGION_AND_DEFECT>. Keep the exact armor identity, colors, materials, fitted pose, silhouette,
openings, lighting, uniform `#FF00FF` chroma-key background, and every accepted region unchanged. Output armor pixels
only. Do not add
body parts, equipment, background, text, glow, or white edge matte.
```

Do not repeatedly rewrite the full prompt when only one region is wrong; targeted feedback reduces design drift.

## Promotion And Persistence

Promote only after both arm poses and every eligible doll type have passed visual review. Copy the accepted file to
`assets_dev/worlds/mm9/icons/<exact-runtime-name>.png`, retain its source-input hashes and generation/post-processing
provenance, and update the authored visual review state rather than editing generated tables.

Do not leave an accepted source only under `test_img/`, `/tmp`, or an image tool's generated-output directory. Those
locations are for review and can disappear or be ignored by version control.

`tools/mm9_import_discovery/generate_mm9_equipment_variants.py` owns staged generation and atomic family promotion
to the active MM9 icon directory. Accepted outputs and provenance live in `mm9_equipment_generated_art.yml`; the
generator validates their hashes and complete suffix sets before copying them, so deterministic staging cannot
overwrite promoted authored artwork.

After promotion, restart the game or reload its assets because an already loaded paperdoll texture may be cached.
