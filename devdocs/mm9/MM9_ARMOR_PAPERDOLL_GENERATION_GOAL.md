# MM9 Armor Paperdoll Generation Goal

## Status

Goal definition complete. Asset generation has not started under this goal and must begin from the beginning when the
goal is activated for implementation.

Earlier Broderick's Hauberk and Arming Doublet experiments are reference material only. They were invalidated when the
body-armor coverage rule was corrected: body armor must never replace or paint over the doll's footwear, feet, claws,
or hooves. `tools/mm9_import_discovery/mm9_armor_generated_art.yml` is the authoritative acceptance manifest and must
remain empty until a newly generated variant passes every gate in this document.

The scope is 35 MM9 body armors with ten paperdoll variants each, for a total of 350 reviewed runtime sprites.

## Objective

Generate a complete MM6-MM8-style paperdoll sprite set for every imported MM9 body armor. Each result must preserve the
recognizable MM9 design while looking intentionally tailored to the exact OpenYAMM doll and arm pose. The result must
not resemble a stretched inventory icon.

The inventory icon and original MM9 PCX own the item's identity. Existing MM6-MM8 equipment and OpenYAMM tables provide
pose, placement, scale, layering, and useful garment-geometry references. They do not authorize copying an unrelated
armor design, and a mapped legacy alpha silhouette is not automatically correct for the MM9 garment.

All generated art remains owned by the MM9 world package. Do not modify or replace the base MMerge/OpenYAMM armor
assets under `assets_dev/engine/`.

## Required Output

Each MM9 armor must provide these ten files:

| Doll type | Right-hand weapon pose | No-right-hand-weapon pose |
| --- | --- | --- |
| 0 | `v1` | `v1a` |
| 1 | `v2` | `v2a` |
| 2 | `v3` | `v3a` |
| 3 | `v4` | `v4a` |
| 4 | `v5` | `v5a` |

Type 5 is the non-equippable dragon paperdoll and has no armor variant. Generate all ten files for every armor even if
its current class restriction makes one doll uncommon or unreachable. Visual completeness must not depend on current
class-balance rules.

Accepted runtime files use this naming and ownership:

```text
assets_dev/worlds/mm9/icons/mm9_item_<global-item-id><suffix>.png
```

Reviewed source and fitted assets are registered through:

```text
tools/mm9_import_discovery/mm9_armor_generated_art.yml
tools/mm9_import_discovery/generated_armor_art/
tools/mm9_import_discovery/generated_armor_art/sources/
```

Do not promote a review candidate by copying it directly into the active icon directory. The manifest and generator
are the sole promotion path.

## Binding Source Inputs

Every variant generation request uses all four inputs defined in `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md`:

1. a rendered preview of the exact doll type and requested arm pose;
2. the promoted transparent MM9 inventory icon;
3. the audited target paperdoll silhouette for the exact suffix; and
4. the original 64x64 MM9 PCX, losslessly converted and enlarged with nearest-neighbor sampling.

The original PCX is mandatory. The output must remain visibly based on the MM9 icon while adopting the painted,
late-1990s MM6-MM8 paperdoll style.

Use local references in this order:

1. imported MM9 item data and its recorded original PCX;
2. the promoted MM9 inventory icon;
3. the actual OpenYAMM doll, layer order, offsets, and native equipment renders;
4. `reference/OpenEnroth-git/` for behavior or format understanding when needed; and
5. `/home/pjasicek/github/OpenMM9` and `/home/pjasicek/github/GodotMM9` as MM9 format, asset, and presentation
   cross-checks.

Do not copy code or artwork from OpenEnroth, OpenMM9, GodotMM9, or mm_mapview2.

## Non-Negotiable Coverage Rules

### Body armor is not footwear

Body armor must leave the doll's own boots, shoes, feet, claws, and hooves visible. This applies to every armor, doll
type, and pose. Item 878, Plate Armor, as rendered in `test_img/1195.png`, is a useful visual reference: its armor layer
ends before the male human's boots. The same principle applies to female humans, minotaurs, trolls, and dwarves.

The rule does not prohibit garment-appropriate leggings, greaves, skirts, or a long hauberk. Those elements may cover
part of a lower leg when supported by the MM9 item design, but must end cleanly before the separate foot/footwear region.
Minotaur hooves must always remain the doll's own hooves.

Implement and validate explicit per-doll foot/footwear exclusion masks in paperdoll coordinates. Derive them from the
actual dolls and native equipment boundaries. Native boot sprites and plate-armor renders are useful evidence, but do
not blindly use one armor's complete alpha as every garment's silhouette. The accepted body-armor alpha must have zero
overlap with the exclusion mask.

### Match the actual garment

Audit each armor reference selection in
`tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml` before generating art. The broader table also owns
the pending helmet, boot, and belt selections. `mm9_item_body_equipment_visuals.yml` remains the active armor-generator
overlay until the generator consumes the new table; synchronize its reference and coverage rows before generating an
armor. Choose geometry according to the MM9 icon and description, not merely armor skill or rarity. For example, a
short arming doublet must not inherit a legacy full-body leather suit just because both are leather armor.

Classify the intended coverage before selecting or constructing the target mask:

- short jacket, doublet, jerkin, or cuirass;
- hip- or thigh-length coat, brigandine, mail shirt, haubergeon, or hauberk;
- complete mail or plate harness with separate exposed footwear/feet; or
- exceptional artifact silhouette justified by its source icon and description.

An audited target may be a strict subset of a legacy reference mask. Preserve the exact arm pose and paperdoll
placement, but remove reference-only panels, integrated boots, or full-leg coverage that does not belong to the MM9
item. If no existing reference provides a correct outline, author a deterministic coverage overlay instead of forcing
an unrelated silhouette.

### Armor-only output

The generated layer contains armor pixels only. It must not contain a person, skin, hands, feet, hair, face, weapon,
shield, mannequin, UI, environment, text, cast shadow, glow, or watermark. The item remains upright and follows the
doll pose exactly.

## Reference-Mapping Audit Gate

Before the first AI request for an armor:

1. View the inventory icon, enlarged original PCX, item name, and description.
2. Render the currently mapped reference on all five representative doll types in both arm poses.
3. Compare the proposed coverage with the unarmored doll, native boots, native armor examples, and the item's garment
   semantics.
4. Correct `mm9_equipment_legacy_base_mappings.yml`, synchronize the active armor overlay, or add an explicit audited
   coverage overlay when the mapped geometry is wrong.
5. Generate the ten deterministic target masks.
6. Assert that each target mask is disjoint from its doll's foot/footwear/hoof exclusion mask.
7. Render the empty/design-transfer targets once more and visually approve the boundaries before image generation.

Do not start generation for an armor whose target silhouettes have not passed this gate. A visually attractive result
inside a wrong silhouette is still wrong.

## Image-Generation Contract

Follow the canonical prompt and input order in `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md`. Generate one item, one doll type,
and one arm pose per request; do not ask for contact sheets or multiple runtime assets in one image.

Request one perfectly uniform solid `#FF00FF` magenta background. This is a technical chroma key, not part of the art.
The prompt must explicitly forbid checkerboards, gradients, shadows, scenery, body parts, feet, footwear, claws, and
hooves.

The generated result is a high-resolution design proposal. Never trust its canvas, placement, dimensions, or alpha as
runtime geometry. Never fill missed regions with the previous stretched design-transfer image.

## Deterministic Fitting And Chroma Key

Use `tools/mm9_import_discovery/fit_mm9_ai_armor_variant.py` or its reviewed successor for reproducible fitting:

1. Replace exact `#FF00FF` pixels with full transparency.
2. Correct only anti-aliased edge pixels mathematically mixed with magenta. Keep despill within a narrow edge band;
   preserve intentional purple, silver, and pale item details.
3. Crop the armor proposal without losing its intended vertical extent.
4. Fit torso, skirt/hip panels, sleeves, and legs semantically when a single global transform would distort them.
5. Downsample to the exact target canvas.
6. Apply the audited target alpha, not the raw AI alpha and not an unaudited legacy reference alpha.
7. Assert exact dimensions, exact audited alpha, no magenta residue, no bright checker/white fringe, and zero overlap
   with the doll's foot/footwear/hoof exclusion mask.

Broad luminance keys are forbidden because they can erase pale cloth and metal highlights. Broad color replacement
that damages legitimate armor colors is also forbidden.

## Rendered Review Loop

Use `tools/mm9_import_discovery/render_paperdoll_equipment_preview.py` to render the candidate through the same table,
suffix, offset, and layer-selection path used by OpenYAMM.

For every suffix, prepare the equipped-composite review packet and suffix-specific prompts with
`tools/mm9_import_discovery/prepare_mm9_armor_ai_review.py`. The final equipped-doll composite—not the isolated sprite
or its alpha—is mandatory AI visual evidence. Give the AI reviewer the composite, fitted candidate, exact two-color
mask, inventory icon, and original PCX. If the composite reveals projected inventory art, incorrect shoulder/sleeve
construction, anatomical misalignment, or any other fitting defect, run the repair prompt, deterministically refit the
new source, rerender it, and repeat the AI review.

For every suffix, inspect both the sprite and the full paperdoll render at native scale and nearest-neighbor
enlargement. Verify:

- recognizable MM9 colors, materials, construction, trim, closures, and ornaments;
- late-1990s MM6-MM8 painted sprite character after downsampling;
- coherent wearable construction rather than stretched or tiled inventory artwork;
- exact neck, shoulder, waist, arm, and leg alignment;
- correct distinction between the weapon and no-right-hand-weapon poses;
- sleeves and shoulder openings constructed around each actual arm direction rather than copied symmetrically from
  the inventory icon;
- garment coverage appropriate to the item name, description, inventory icon, and PCX;
- untouched doll footwear, feet, claws, and hooves;
- clean hems or armor endings above the excluded foot region;
- no swapped/crossed limbs, bridges, holes, or detached panels;
- no white/checkerboard/magenta fringe or transparent holes;
- no body parts or unrelated equipment baked into the sprite; and
- correct runtime placement and occlusion.

Regenerate when identity, construction, pose, or a substantial semantic region is wrong. Use deterministic fitting for
crop, scale, alignment, alpha, and small edge corrections. Reject a result rather than accumulating broad heuristic
fixes.

## Persistence And Provenance

Only a reviewed variant may be added to `mm9_armor_generated_art.yml`. Each entry records:

- raw MM9 item id and global OpenYAMM item id;
- exact suffix;
- accepted fitted asset;
- high-resolution generation source;
- generation tool;
- prompt specification;
- deterministic post-processing description;
- source, target, and output hashes; and
- reviewed status.

`generate_mm9_armor_variants.py` must validate the accepted image against the audited target dimensions and alpha before
copying it into `assets_dev/worlds/mm9/icons/`. Regeneration must preserve accepted authored variants and must fail
visibly on stale mappings, missing sources, hash/provenance errors, alpha mismatch, or foot-mask overlap.

Keep rejected experiments outside the manifest. Old unreferenced files under review or generated-art directories are
not accepted merely because they exist.

## Implementation Work Required Before Regeneration

- Add explicit per-doll foot/footwear/hoof exclusion masks in paperdoll coordinates.
- Make target generation apply and record the audited garment coverage rather than blindly copying reference alpha.
- Change authored-variant validation to compare against the audited target alpha.
- Add tests proving every generated target and accepted variant is disjoint from the exclusion mask.
- Add tests for exact magenta removal and narrow anti-aliased-edge despill without erasing legitimate armor colors.
- Re-audit all 35 reference mappings for garment length and coverage semantics.
- Keep the acceptance manifest empty until the revised target/tooling gates pass.

## Armor Inventory And Progress

All entries begin at zero accepted variants after the restart.

| Raw id | Global id | Armor | Reference audit | Accepted variants | Final render |
| ---: | ---: | --- | --- | ---: | --- |
| 86 | 10086 | Arming Doublet | pending | 0/10 | pending |
| 87 | 10087 | Padded Leather | pending | 0/10 | pending |
| 88 | 10088 | Hardened Leather | pending | 0/10 | pending |
| 89 | 10089 | Beldonian Hard Leather | pending | 0/10 | pending |
| 90 | 10090 | Scaled Leather | pending | 0/10 | pending |
| 91 | 10091 | Imperial Scale | pending | 0/10 | pending |
| 92 | 10092 | Brigandine | pending | 0/10 | pending |
| 93 | 10093 | Combat Brigandine | pending | 0/10 | pending |
| 94 | 10094 | Brigan der Combit | pending | 0/10 | pending |
| 95 | 10095 | Aklean Bouila | pending | 0/10 | pending |
| 96 | 10096 | Butted Chain | pending | 0/10 | pending |
| 97 | 10097 | Rivited Chain | pending | 0/10 | pending |
| 98 | 10098 | Iron Chain | pending | 0/10 | pending |
| 99 | 10099 | Steel Chain | pending | 0/10 | pending |
| 100 | 10100 | Chain Haubergeon | pending | 0/10 | pending |
| 101 | 10101 | Chain Hauberk | pending | 0/10 | pending |
| 102 | 10102 | Chedian Chain | pending | 0/10 | pending |
| 103 | 10103 | Chain Harness | pending | 0/10 | pending |
| 104 | 10104 | Lachmon Hauberk | pending | 0/10 | pending |
| 105 | 10105 | Trigvanian Mail | pending | 0/10 | pending |
| 108 | 10108 | Ronenguard Plate | pending | 0/10 | pending |
| 109 | 10109 | Field Plate | pending | 0/10 | pending |
| 110 | 10110 | Full Plate | pending | 0/10 | pending |
| 111 | 10111 | Paladin's Plate | pending | 0/10 | pending |
| 112 | 10112 | Heavy Plate | pending | 0/10 | pending |
| 113 | 10113 | Thjoradric Plate | pending | 0/10 | pending |
| 114 | 10114 | Imperial Harness | pending | 0/10 | pending |
| 115 | 10115 | Dark Plate | pending | 0/10 | pending |
| 200 | 10200 | Igdrasine | pending | 0/10 | pending |
| 201 | 10201 | Poltergeist | pending | 0/10 | pending |
| 202 | 10202 | Swordsbane | pending | 0/10 | pending |
| 220 | 10220 | Prize Plate | pending | 0/10 | pending |
| 225 | 10225 | Broderick's Hauberk | pending | 0/10 | pending |
| 230 | 10230 | Death Cuirass | pending | 0/10 | pending |
| 367 | 10367 | Quilted Armor | pending | 0/10 | pending |

Update this table only after the corresponding acceptance manifest entries and rendered evidence exist.

## Verification

At minimum, the completed work must pass:

```sh
python3 -m unittest \
  tools.mm9_import_discovery.test_fit_mm9_ai_armor_variant \
  tools.mm9_import_discovery.test_generate_mm9_armor_variants

python3 tools/mm9_import_discovery/generate_mm9_armor_variants.py
```

Also run an automated full-set audit that proves:

- exactly 35 armor definitions exist;
- exactly 350 accepted variants exist;
- every expected filename exists and no suffix is substituted by fallback lookup;
- every accepted file matches its audited dimensions and alpha;
- every accepted alpha is disjoint from its per-doll foot/footwear/hoof exclusion mask;
- every manifest/source/output hash resolves;
- no accepted image contains opaque `#FF00FF`, checkerboard remnants, or unintended bright fringe; and
- all five doll types render successfully in both arm poses for every item.

The automated audit does not replace visual review. Preserve final contact sheets or equivalent review evidence for
all 35 armors and both pose families.

## Completion Criteria

This goal is complete only when:

1. the audited coverage-mask and foot-exclusion tooling is implemented and tested;
2. all 35 reference mappings and garment silhouettes have been reviewed;
3. all 350 variants have been independently generated, fitted, visually reviewed, and registered;
   each registration includes its accepted equipped-composite AI review evidence;
4. the authoritative manifest contains exactly the reviewed set and regeneration reproduces the active MM9 assets;
5. every body armor leaves footwear, feet, claws, and hooves untouched on every supported doll;
6. full-set automated verification and rendered contact-sheet review pass; and
7. the progress table above records 10/10 and a completed final render for every armor.

Partial families, attractive inventory icons, successful asset lookup, or a zero-error alpha comparison against an
unaudited legacy silhouette do not satisfy this goal.
