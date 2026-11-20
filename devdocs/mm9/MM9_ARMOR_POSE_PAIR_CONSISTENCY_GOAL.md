# MM9 Armor Pose-Pair Consistency Goal

## Status

Completed on 2026-08-25: 35/35 armor families and 175/175 weapon/empty-hand pose pairs are reviewed, promoted,
hash-locked, and verified.

The implementation is `tools/mm9_import_discovery/audit_mm9_armor_pose_pairs.py`, with focused coverage in
`tools/mm9_import_discovery/test_audit_mm9_armor_pose_pairs.py`. The initial production audit found all 175 pairs
inconsistent: 166 had common-region structural/RGBA drift and nine had transparency-only drift. Deterministic
canonical-pixel transfer and native-pair-derived weapon-arm masks repaired every pair without an AI redraw. Final
acceptance proves zero RGBA differences outside the allowed arm masks, exact common-region equality, exact target
alpha, and atomic promotion for all 35 ten-file armor families.

AI visual validation covered all seven full equipped-family catalogues, four enlarged seam catalogues, and four exact
difference catalogues. Fresh MM9-client evidence records Dark Plate and Broderick's Hauberk on a female human with an
empty main hand and with an Iron Longsword. The capture used a temporary item-specific eligibility bypass solely
because a level-1 debug character lacks the production skills/class eligibility; that hook was removed before the
final build. Representative MM7 Noble Plate and MM8 Dark Knight Plate previews pass in both hand states for all five
doll types. The six-module equipment suite passes all 64 tests, both equipment verifiers pass, and the normal OpenYAMM
build succeeds after removal of the capture-only hook.

The earlier equipment-generation goal produced and promoted all 350 MM9 armor sprites, but it reviewed each suffix
independently. That allowed the weapon and empty-hand variants of one armor to become different designs. Existing
per-variant `reviewed` states remain useful evidence for fit, alpha, and source identity, but they do not satisfy this
goal until the corresponding pose pair passes the new pair-level gates.

The initial confirmed failure is Dark Plate, global item 10115. In `test_img/1201.png` and `test_img/1202.png`, its
weapon and empty-hand variants change the breastplate, chest ornament, abdomen, waist, skirt, leg plates, and opposite
shoulder. Native MM7/MM8 armor does not behave this way.

This goal covers all 35 MM9 body armors, five doll types, and 175 pose pairs. It repairs the existing 350 runtime
sprites where needed. Helmets, boots, belts, inventory icons, item stats, and equipment eligibility are out of scope.

## Objective

Make every MM9 armor's weapon and empty-hand sprites look like the same physical armor on the same doll. Only the
doll's right-hand weapon-side armor geometry may change between the two poses. This is normally the arm visible on the
left side of the rendered paperdoll and may include its shoulder transition, sleeve or upper-arm plate, elbow,
forearm, cuff, or gauntlet where those parts belong to the armor.

All shared regions must retain one design:

- neck opening and collar;
- chest and breastplate construction;
- symbols, ornaments, trim, rivets, and closures;
- abdomen, waist, and integrated armor belt structure;
- skirt, fauld, coat tails, mail, and lower panels;
- both legs and their armor coverage;
- the non-weapon-side shoulder, sleeve, and arm armor;
- materials, palette, lighting, texture scale, and highlight placement; and
- the same recognizable identity derived from the promoted MM9 inventory icon and original PCX.

Do not merely make both poses generally similar. Where their audited geometry is shared, use the same accepted pixels
or a deterministic transfer from one canonical design. A newly invented chest, alternate ornament layout, different
waist, or independently redesigned lower body is a failure even if each isolated sprite looks attractive.

All results remain owned by the MM9 world package. Do not modify the native MM6/MM7/MM8 assets under
`assets_dev/engine/`.

## Native MM7/MM8 Behavior

Treat native MM7/MM8 armor pairs as the behavioral and visual reference for pose changes.

The exact MM7 Noble Plate Armor family mapped to MM9 Dark Plate is:

```text
assets_dev/engine/icons/7item078v1.bmp   weapon pose
assets_dev/engine/icons/7item078v1a.bmp  empty-hand pose
...
assets_dev/engine/icons/7item078v5.bmp   weapon pose
assets_dev/engine/icons/7item078v5a.bmp  empty-hand pose
```

Across all five pairs, Noble Plate preserves the torso, ornament, waist, fauld, legs, opposite arm, palette, and
lighting. Only the weapon-side arm armor changes pose. For the `v1`/`v1a` pair, the changed pixels are localized to
that arm; the shared armor is byte-identical.

Other native patterns are also valid:

- MM7 armor without weapon-side sleeve or plate coverage may use identical `vN` and `vNa` files. Crude Leather
  (`7item066`) and Disheveled Chain Mail (`7item071`) are examples.
- MM7 armor with weapon-side coverage changes only that shoulder, sleeve, arm plate, forearm, or gauntlet. Plate Armor
  (`7item076`) and Noble Plate Armor (`7item078`) are examples.
- MM8 pairs preserve the same design and usually change only a small weapon-side shoulder or arm region. Some source
  BMP pairs contain minor palette or dithering noise outside that region, but this is not a license for structural or
  ornamental drift. Rusty Breastplate (`item094`) is an identical pair; Banded Plate (`item095`) and Dark Knight Plate
  (`item097`) retain the same torso and lower construction.

New MM9 PNGs do not need to reproduce historical BMP palette noise. Their common regions should be deterministically
identical.

## Required Pose Pairs

Every armor owns five atomic pairs:

| Doll type | Weapon pose | Empty-right-hand pose |
| ---: | --- | --- |
| 0 | `v1` | `v1a` |
| 1 | `v2` | `v2a` |
| 2 | `v3` | `v3a` |
| 3 | `v4` | `v4a` |
| 4 | `v5` | `v5a` |

A pair is the smallest promotable unit. Never promote or mark only one member reviewed under this goal.

## Authoritative Inputs And Ownership

Use these inputs in this order:

1. `tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml` owns the selected MM7/MM8 family and geometry
   profile.
2. The selected native `vN`/`vNa` pair owns the intended difference between the two arm poses.
3. The exact promoted MM9 inventory PNG and original 64x64 MM9 PCX own item identity, palette, material, and ornament.
4. The existing audited target masks own permitted coverage and exact runtime alpha for each suffix.
5. The actual paperdoll render owns placement, pose, visibility, and layer-order truth.
6. `MM9_EQUIPMENT_PAPERDOLL_GENERATION_GOAL.md` and `MM9_ARMOR_PAPERDOLL_AI_GENERATION.md` remain binding for fitting,
   foot exclusion, chroma key, visual style, review, and provenance where this goal does not override them.

`tools/mm9_import_discovery/mm9_equipment_generated_art.yml` remains the sole generated-equipment acceptance manifest.
Extend it with pair-level provenance and review state; do not introduce another manifest that duplicates ownership.

## Pair-Audit Tooling

Implement a focused, deterministic pose-pair auditor under `tools/mm9_import_discovery/`. Keep image-comparison logic
separate from report rendering so it has unit coverage. It must consume the mapping table, generated-art manifest,
target masks, selected native pair, and promoted MM9 pair.

For every pair, compute and preserve:

1. the two exact audited target alpha masks;
2. their alpha symmetric difference;
3. the selected native pair's materially changed pixels, ignoring minor MM8 palette/dither noise;
4. a conservative pose-change mask containing only the weapon-side arm region;
5. the common-region mask outside the pose-change mask where both MM9 variants have armor coverage;
6. an RGBA difference image for the promoted MM9 pair;
7. changed-pixel counts inside and outside the allowed pose-change mask; and
8. native-scale and nearest-neighbor pair-review images.

The pose-change mask must be auditable and reproducible. Derive it from the exact native pair, target-alpha symmetric
difference, and doll pose. Retain only components connected to or required by the weapon-side arm, then use a small,
documented dilation sufficient for antialiasing and seams. It must not reach the center chest, abdomen, waist, lower
panels, legs, opposite shoulder, or opposite arm merely to make a failing image pass.

If automatic derivation is ambiguous, add a narrow authored override for that mapped family and doll type. Record why
the override is necessary. Do not use a broad rectangle, whole-torso mask, high color tolerance, or per-item exception
that hides design drift.

For native pairs that are identical and target masks that are identical, the allowed change mask is empty and the MM9
pair must be identical. If target alpha changes but the native RGB pair is otherwise identical, allow only the exact
pose-related alpha region plus the minimal seam dilation.

The tool must emit a machine-readable report and contact sheets. At minimum, each row records:

- raw and global item ids, item name, doll type, and suffix pair;
- selected native reference pair and hashes;
- target-mask hashes;
- pose-change-mask path and hash;
- common-region hash;
- changed pixels inside and outside the allowed region;
- whether shared alpha and shared RGBA are exact;
- review-evidence paths and hashes; and
- `pending`, `failed`, or `reviewed` pair status.

## Automated Acceptance Rules

A repaired pair must satisfy all of the following:

1. Both files exist at the expected MM9 world-owned runtime paths.
2. Both retain their exact audited dimensions and target alpha.
3. Every target-alpha difference lies inside the allowed pose-change mask.
4. Every RGBA difference lies inside the allowed pose-change mask.
5. The common-region pixels are exactly identical, not perceptually similar.
6. No changed pixel occurs in the chest, abdomen, waist, lower panels, legs, opposite shoulder, or opposite arm.
7. Neither file overlaps the doll's footwear, foot, claw, or hoof exclusion mask.
8. Neither file contains baked anatomy, another equipment item, magenta residue, checkerboard, white matte, or bright
   fringe.
9. Both render successfully through the runtime-equivalent preview path.
10. The pair-level manifest hashes match the promoted files and all review evidence.

The exact shared-pixel rule applies to new MM9 output even where an MM8 reference pair contains low-level palette
noise. Do not weaken it with a perceptual threshold. A threshold may be used only while deriving the native reference's
semantic arm-change mask.

## Repair Workflow

Process one armor family at a time and all five of its pose pairs atomically.

### 1. Audit

For each pair:

1. Render both currently promoted variants on the same doll with only the right-hand weapon state changed.
2. View the isolated sprites and equipped composites side by side at native scale and nearest-neighbor enlargement.
3. View the generated difference overlay and permitted pose-change mask.
4. Classify the pair as already consistent, repairable from one canonical member, or requiring a new canonical design.
5. Record the decision before changing an asset.

Do not assume every current pair is broken. Preserve a pair that already satisfies the new automated and visual gates.

### 2. Select And Validate The Canonical Design

Choose the better current member as the canonical shared design only when it already passes the existing identity,
coverage, fit, foot-exclusion, edge, and equipped-review requirements. Compare it with the inventory PNG, original PCX,
mapped native family, and the other four doll types.

The canonical choice is per doll type when necessary, but all five dolls must depict the same item. Do not use the
weapon pose by default merely because it is non-`a`, and do not use the empty-hand pose by default merely because it
shows more of the arm.

If neither member has an acceptable torso and lower design, repair one canonical pose first using the established
armor workflow. Accept that canonical design before creating its paired pose.

### 3. Construct The Alternate Pose

Start from the accepted canonical design. Preserve the common region deterministically and replace only the permitted
weapon-side arm region. Prefer, in order:

1. deterministic reuse when the native and target pairs require no armor change;
2. deterministic semantic fitting of the accepted shoulder/sleeve/arm artwork into the alternate target geometry;
3. a tightly masked AI edit of only the weapon-side arm region; or
4. regeneration of only that semantic region when fitting cannot produce a coherent result.

Never send the entire alternate sprite for an unconstrained independent redraw. Never accept an AI result's full
canvas as the alternate pose. After any AI operation, reapply the exact target alpha and overwrite the entire common
region with the accepted canonical RGBA pixels.

Where the two target masks overlap inside the pose-change region, preserve material, trim continuity, ornament scale,
and lighting. The arm may articulate, but it must not become a different armor style.

### 4. Pair-Locked AI Edit Contract

When AI is required, provide:

1. the accepted canonical isolated sprite;
2. its equipped composite;
3. the alternate-pose doll composite;
4. both audited target masks;
5. the selected native `vN`/`vNa` pair;
6. a two-color allowed-edit mask that exposes only the weapon-side arm region;
7. the promoted MM9 inventory icon; and
8. the enlarged original MM9 PCX.

Use this binding prompt core:

```text
Create the alternate arm pose of the same paperdoll armor, not a second interpretation of the item.

The accepted canonical sprite owns every shared pixel, including the collar, chest, breastplate ornament, abdomen,
waist, skirt or fauld, lower panels, legs, opposite shoulder, and opposite arm. Keep all of those regions exactly
unchanged. Edit only the exposed weapon-side shoulder, sleeve or upper-arm plate, elbow, forearm, cuff, or gauntlet
inside the supplied allowed-edit mask so it follows the alternate doll arm pose and the native MM7/MM8 pose-pair
reference.

Preserve the exact armor identity, materials, colors, trim, ornament scale, lighting direction, and MM6-MM8 painted
sprite style. Continue seams and highlights naturally across the shoulder boundary. Do not redesign the torso or
lower armor. Do not add anatomy, a hand, weapon, shield, boots, belt item, background, shadow, glow, text,
checkerboard, or white edge matte. Use a uniform #FF00FF technical background outside the armor proposal.
```

Treat the AI result as a proposal for the allowed arm region only. Any changed pixel outside that region is discarded,
not negotiated into a wider mask.

### 5. Deterministic Assembly

Assemble the final pair reproducibly:

1. chroma-key and despill only the generated arm proposal using the established strict process;
2. fit it only within the allowed pose-change mask;
3. apply the exact alternate target alpha;
4. copy the accepted canonical common-region RGBA into the alternate file;
5. clear RGB under fully transparent pixels;
6. assert zero differences outside the allowed pose-change mask;
7. run all existing armor and equipment verifiers; and
8. generate fresh pair-level review evidence.

Do not fill holes with an older independently generated alternate sprite. Fix the semantic arm region or regenerate it.

## Visual Review Gate

Automated equality is necessary but does not prove that the changed arm is well drawn. Review every repaired pair as a
unit. The packet must show:

- inventory PNG and enlarged original PCX;
- selected native weapon/empty pair;
- isolated MM9 weapon/empty pair;
- both equipped composites on the exact doll;
- a blink or alternating-pose preview aligned to the common body;
- an absolute-difference overlay;
- the allowed pose-change mask; and
- an enlarged shoulder-seam crop.

Verify:

- the common torso and lower body do not flicker or change when alternating poses;
- symbols, ridges, panels, mail links, straps, rivets, and highlights remain registered;
- the weapon-side shoulder connects naturally in both poses;
- sleeve and arm-plate perspective follows the actual arm direction;
- neither pose contains duplicated, detached, shortened, or crossed arm parts;
- the changed arm does not cover the hand incorrectly;
- the opposite arm remains unchanged;
- equipment layering remains correct with and without a right-hand weapon; and
- both poses still satisfy all existing armor fit, foot-exclusion, and edge-quality requirements.

Pair-level AI visual review is mandatory after deterministic assembly. If the common body changes, fix the assembly or
canonical selection. If only the arm is aesthetically wrong, use a tightly masked arm-region fix-up and rerun the full
pair review.

## Manifest And Promotion

Extend each armor entry in `mm9_equipment_generated_art.yml` with five pair records. A record must identify:

- the two suffixes and their current content hashes;
- selected canonical suffix and source hash;
- allowed pose-change mask and hash;
- common-region mask/hash and exact-equality result;
- deterministic assembly description;
- any AI arm-edit source, prompt version, and available tool metadata;
- isolated, equipped, blink, difference, and seam-review evidence with hashes; and
- `review_status: reviewed` only after automated and visual pair acceptance.

Update the existing variant content hashes and provenance whenever a promoted file changes. Promotion is atomic per
armor family: stage and verify all ten files and five pair records, then replace the active MM9 files together. A
failed pair leaves that armor family pending and must not leave a half-promoted runtime set.

Preserve superseded generated sources as provenance where useful. Do not leave runtime lookup pointed at staging
files, and do not overwrite unrelated user changes.

## Work Order

### Phase 1: Dark Plate Pilot

Repair item 10115 first. It is the confirmed failure and maps to MM7 Noble Plate Armor, whose five native pose pairs
provide especially clear localized arm changes.

The pilot is accepted only when:

- all five Dark Plate pose pairs share exact common-region pixels;
- the current chest/waist/skirt/leg redesign between `v1` and `v1a` is eliminated;
- both poses still resemble the MM9 Dark Plate inventory image and original PCX;
- equipped review passes for every doll type; and
- the new automated auditor and its focused tests pass.

Do not continue the batch until the Dark Plate workflow proves that an alternate arm can be repaired without changing
the accepted common armor.

### Phase 2: Remaining Full Harness And Plate

Audit and repair the remaining plate, harness, artifact, relic, and set armor first because their weapon-side sleeves
and arm plates are most likely to require pose-specific artwork.

### Phase 3: Leather, Chain, And Short Armor

Audit the remaining armor families. Expect many sleeveless or short-torso pairs to require identical sprites or only a
small shoulder/sleeve change. Do not generate artificial differences merely because two suffixes exist.

### Phase 4: Complete Audit And Runtime Validation

Run the auditor across all 175 pairs, visually review the complete contact sheets, promote every repaired family, test
representative pairs in a freshly started game, and validate affected MM6/MM7/MM8 paths.

## Progress

All entries began pending pair audit even if their individual variants were previously marked reviewed.

| Raw | Global | Item | Pairs | Status |
| ---: | ---: | --- | ---: | --- |
| 86 | 10086 | Arming Doublet | 5/5 | reviewed and promoted |
| 87 | 10087 | Padded Leather | 5/5 | reviewed and promoted |
| 88 | 10088 | Hardened Leather | 5/5 | reviewed and promoted |
| 89 | 10089 | Beldonian Hard Leather | 5/5 | reviewed and promoted |
| 90 | 10090 | Scaled Leather | 5/5 | reviewed and promoted |
| 91 | 10091 | Imperial Scale | 5/5 | reviewed and promoted |
| 92 | 10092 | Brigandine | 5/5 | reviewed and promoted |
| 93 | 10093 | Combat Brigandine | 5/5 | reviewed and promoted |
| 94 | 10094 | Brigan der Combit | 5/5 | reviewed and promoted |
| 95 | 10095 | Aklean Bouila | 5/5 | reviewed and promoted |
| 96 | 10096 | Butted Chain | 5/5 | reviewed and promoted |
| 97 | 10097 | Rivited Chain | 5/5 | reviewed and promoted |
| 98 | 10098 | Iron Chain | 5/5 | reviewed and promoted |
| 99 | 10099 | Steel Chain | 5/5 | reviewed and promoted |
| 100 | 10100 | Chain Haubergeon | 5/5 | reviewed and promoted |
| 101 | 10101 | Chain Hauberk | 5/5 | reviewed and promoted |
| 102 | 10102 | Chedian Chain | 5/5 | reviewed and promoted |
| 103 | 10103 | Chain Harness | 5/5 | reviewed and promoted |
| 104 | 10104 | Lachmon Hauberk | 5/5 | reviewed and promoted |
| 105 | 10105 | Trigvanian Mail | 5/5 | reviewed and promoted |
| 108 | 10108 | Ronenguard Plate | 5/5 | reviewed and promoted |
| 109 | 10109 | Field Plate | 5/5 | reviewed and promoted |
| 110 | 10110 | Full Plate | 5/5 | reviewed and promoted |
| 111 | 10111 | Paladin's Plate | 5/5 | reviewed and promoted |
| 112 | 10112 | Heavy Plate | 5/5 | reviewed and promoted |
| 113 | 10113 | Thjoradric Plate | 5/5 | reviewed and promoted |
| 114 | 10114 | Imperial Harness | 5/5 | reviewed and promoted |
| 115 | 10115 | Dark Plate | 5/5 | pilot reviewed and promoted |
| 200 | 10200 | Igdrasine | 5/5 | reviewed and promoted |
| 201 | 10201 | Poltergeist | 5/5 | reviewed and promoted |
| 202 | 10202 | Swordsbane | 5/5 | reviewed and promoted |
| 220 | 10220 | Prize Plate | 5/5 | reviewed and promoted |
| 225 | 10225 | Broderick's Hauberk | 5/5 | reviewed and promoted |
| 230 | 10230 | Death Cuirass | 5/5 | reviewed and promoted |
| 367 | 10367 | Quilted Armor | 5/5 | reviewed and promoted |

Update a row only after all listed pair records, promoted hashes, and review evidence exist. The final count is 175/175
reviewed pose pairs across 35/35 atomically complete armor families.

## Required Automated Verification

Add focused tests for:

- suffix pairing and all 175 expected pairs;
- native-pair material-difference and alpha-difference extraction;
- weapon-side connected-component filtering;
- authored-mask override validation;
- rejection of chest, waist, leg, opposite-arm, and broad-mask differences;
- exact common-region RGBA equality;
- exact target-alpha preservation;
- identical-pair handling;
- atomic family promotion and manifest hash updates; and
- stable report/contact-sheet generation.

Run the new focused tests plus all existing equipment tests:

```sh
python3 -m unittest \
  tools.mm9_import_discovery.test_audit_mm9_armor_pose_pairs \
  tools.mm9_import_discovery.test_generate_mm9_equipment_variants \
  tools.mm9_import_discovery.test_fit_mm9_ai_equipment_variant \
  tools.mm9_import_discovery.test_prepare_mm9_equipment_ai_review \
  tools.mm9_import_discovery.test_mm9_equipment_legacy_base_mappings \
  tools.mm9_import_discovery.test_render_paperdoll_equipment_preview

python3 tools/mm9_import_discovery/generate_mm9_equipment_variants.py --verify-only
python3 tools/mm9_import_discovery/audit_mm9_armor_pose_pairs.py --verify-only
```

Use the actual final auditor filename if implementation finds a clearer maintainable name, and update this document and
tests together.

Build after code, table, manifest-loader, or runtime asset changes:

```sh
cmake --build build --target openyamm -j25
```

The final automated report must prove:

- exactly 35 armor families, 350 variants, and 175 pose pairs;
- every expected `vN`/`vNa` pair exists and no suffix is substituted;
- every target-alpha difference is inside its allowed pose-change mask;
- zero promoted RGBA differences outside allowed pose-change masks;
- exact common-region equality for all 175 pairs;
- zero foot/footwear/claw/hoof exclusion overlap;
- all asset, mask, evidence, and manifest hashes resolve;
- all runtime-equivalent previews render without fallback;
- no accepted sprite has magenta/checker/white-edge contamination;
- active MM6/MM7/MM8 icon hashes remain unchanged; and
- verification does not rewrite accepted assets or unrelated files.

## Runtime And Regression Verification

Test at least one repaired armor of each coverage class in a freshly started MM9 game, switching the right-hand weapon
on and off while leaving the rest of the equipment unchanged. Include Dark Plate and Broderick's Hauberk. Preserve the
screenshots under the existing generated-art review hierarchy and record their hashes in the manifest.

Validate that the correct suffix is selected when a weapon is equipped or removed and that hand/arm layering is
correct in both states.

This work must not alter MM6/MM7/MM8 gameplay, assets, equipment rendering, paperdoll selection, save/load behavior,
startup or map-loading time, memory use, or runtime performance. Keep pair auditing and generated review evidence in
development tooling. When MM9 is not mounted, this work must add no meaningful runtime cost.

Render representative native MM7 and MM8 armor pairs after any shared preview, suffix-selection, or layer-order code
change. At minimum include MM7 Noble Plate Armor and MM8 Dark Knight Plate in both right-hand states.

## Completion Criteria

This goal is complete only when:

1. a deterministic pair-audit tool and focused tests define and enforce the native MM7/MM8 pose-pair rule;
2. Dark Plate passes the pilot with one stable design across all five weapon/empty pairs;
3. all 35 MM9 armors and all 175 pose pairs pass exact common-region equality;
4. every necessary repair changes only the permitted weapon-side arm region;
5. all 350 runtime sprites retain correct target alpha, fit, source identity, edge quality, and foot exclusion;
6. all pair-level provenance, hashes, statuses, and review evidence live in the existing generated-art manifest;
7. all repaired armor families are promoted atomically and render correctly in game;
8. native MM7/MM8 assets remain unchanged and their representative pose behavior still renders correctly;
9. all required automated tests, verifier runs, visual reviews, in-game checks, and the OpenYAMM build pass; and
10. the progress table records 175/175 reviewed pairs across 35/35 complete armor families.

Individual suffix approval, attractive isolated art, approximate similarity, perceptual diff tolerance, or successful
runtime lookup does not complete a pair. The same armor design must remain stable when the right-hand weapon state
changes.
