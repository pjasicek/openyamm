# MM9 Equipment Legacy Base Mappings

## Purpose

This table assigns every imported MM9 armor, helmet, boot, and belt to the closest usable fitted MM7/MM8 equipment
family. It is the input catalogue for the placeholder generation/fix-up pipeline, not an instruction to replace the
MM9 item's identity with legacy art.

Run the complete generation and acceptance workflow from `MM9_EQUIPMENT_PAPERDOLL_GENERATION_GOAL.md`.

The machine-readable authority is
`tools/mm9_import_discovery/mm9_equipment_legacy_base_mappings.yml`. That file also records the exact visual features
which must be transferred from each MM9 icon. This document is the compact human review view.

## Selection Rules

1. The original MM9 PCX/promoted inventory icon owns item identity, material, palette, ornament, and recognizable
   design.
2. The MM7/MM8 reference owns fitted per-doll pose, placement, perspective, and starting alpha geometry.
3. Prefer the same equipment category, armor skill/material, and normalized treasure tier.
4. When those disagree, correct silhouette and body coverage outrank tier. Every such exception is marked in the
   `Selection` column rather than being hidden.
5. `geometry_profile` is binding. It may crop or constrain the reference before design transfer; for example, a short
   cuirass must not inherit a full skirt, and Fuzzy Slippers must not inherit boot shafts.
6. References are MM7/MM8 only. No MM6 fitted art is used in this mapping.
7. Armor generates ten normal/weapon-pose variants. Helmets and boots generate the four supported non-minotaur doll
   variants. Belts generate all five doll variants. Unsupported doll/category combinations are not synthesized.
8. A mapping is ready to enter generation, but is not final until its equipped composites pass the task-specific AI
   fit review and deterministic artifact/alpha checks.

## Coverage

| Category | MM9 items | Required fitted variants per item |
| --- | ---: | ---: |
| Armor | 35 | 10 |
| Helm | 16 | 4 |
| Boots | 11 | 4 |
| Belt | 6 | 5 |
| **Total** | **68** | **488** |

## Armor

| MM9 raw | Global | MM9 item | Skill | Tier | Base | Base tier | Geometry | Selection |
| ---: | ---: | --- | --- | ---: | --- | ---: | --- | --- |
| 86 | 10086 | Arming Doublet | Leather | 1 | MM8 84 Leather Jerkin | 1 | hip_length | same_type_same_tier_wrap_tunic |
| 87 | 10087 | Padded Leather | Leather | 1 | MM8 84 Leather Jerkin | 1 | hip_length | same_type_same_tier_long_tunic |
| 88 | 10088 | Hardened Leather | Leather | 2 | MM8 85 Hardened Leather Vest | 2 | short_torso | same_type_same_tier_fitted_vest |
| 89 | 10089 | Beldonian Hard Leather | Leather | 2 | MM8 85 Hardened Leather Vest | 2 | short_torso | same_type_same_tier_fitted_vest |
| 90 | 10090 | Scaled Leather | Leather | 3 | MM7 870 Officer's Leather | 3 | short_torso | same_type_same_tier_segmented_torso |
| 91 | 10091 | Imperial Scale | Leather | 3 | MM8 86 Caravaner's Leather | 3 | hip_length | same_type_same_tier_shoulder_construction |
| 92 | 10092 | Brigandine | Leather | 4 | MM8 87 Regnan Leather | 4 | hip_length | same_type_same_tier_long_fitted_leather |
| 93 | 10093 | Combat Brigandine | Leather | 4 | MM8 88 Alvarian Leather | 5 | thigh_length | same_type_near_tier_long_coat_silhouette |
| 94 | 10094 | Brigan der Combit | Leather | 5 | MM8 88 Alvarian Leather | 5 | thigh_length | same_type_same_tier_long_coat |
| 95 | 10095 | Aklean Bouila | Leather | 5 | MM7 872 Royal Leather | 5 | hip_length | same_type_same_tier_ornate_cuirass |
| 96 | 10096 | Butted Chain | Chain | 3 | MM7 875 Fine Chain Mail | 3 | hip_length | same_type_same_tier_mail_skirt |
| 97 | 10097 | Rivited Chain | Chain | 3 | MM8 91 Minotaur Chainmail | 3 | thigh_length | same_type_same_tier_long_mail |
| 98 | 10098 | Iron Chain | Chain | 3 | MM8 91 Minotaur Chainmail | 3 | thigh_length | same_type_same_tier_long_mail |
| 99 | 10099 | Steel Chain | Chain | 3 | MM8 91 Minotaur Chainmail | 3 | thigh_length | same_type_same_tier_long_mail |
| 100 | 10100 | Chain Haubergeon | Chain | 4 | MM7 876 Resplendent Chain Mail | 4 | short_torso | same_type_same_tier_cropped_mail |
| 101 | 10101 | Chain Hauberk | Chain | 4 | MM8 92 Siertal Chainmail | 4 | thigh_length | same_type_same_tier_full_hauberk |
| 102 | 10102 | Chedian Chain | Chain | 4 | MM7 876 Resplendent Chain Mail | 4 | thigh_length | same_type_same_tier_tabard_mail |
| 103 | 10103 | Chain Harness | Chain | 5 | MM8 93 Erudine Chainmail | 5 | short_torso | same_type_same_tier_cropped_harness |
| 104 | 10104 | Lachmon Hauberk | Chain | 5 | MM7 877 Golden Chain Mail | 5 | thigh_length | same_type_same_tier_full_mail |
| 105 | 10105 | Trigvanian Mail | Chain | 5 | MM7 877 Golden Chain Mail | 5 | thigh_length | same_type_same_tier_ornate_full_mail |
| 108 | 10108 | Ronenguard Plate | Plate | 3 | MM8 96 Minotaur Plate | 3 | short_torso | same_type_same_tier_cropped_breastplate |
| 109 | 10109 | Field Plate | Plate | 3 | MM8 96 Minotaur Plate | 3 | short_torso | same_type_same_tier_cropped_breastplate |
| 110 | 10110 | Full Plate | Plate | 3 | MM7 878 Plate Armor | 3 | full_harness | same_type_same_tier_full_harness |
| 111 | 10111 | Paladin's Plate | Plate | 4 | MM7 879 Splendid Plate Armor | 4 | full_harness | same_type_same_tier_ornate_harness |
| 112 | 10112 | Heavy Plate | Plate | 4 | MM7 879 Splendid Plate Armor | 4 | full_harness | same_type_same_tier_heavy_harness |
| 113 | 10113 | Thjoradric Plate | Plate | 4 | MM7 879 Splendid Plate Armor | 4 | full_harness | same_type_same_tier_heavy_harness |
| 114 | 10114 | Imperial Harness | Plate | 5 | MM7 880 Noble Plate Armor | 5 | full_harness | same_type_same_tier_ornate_harness |
| 115 | 10115 | Dark Plate | Plate | 5 | MM7 880 Noble Plate Armor | 5 | full_harness | same_type_same_tier_ornate_harness |
| 200 | 10200 | Igdrasine | Leather | 7 | MM7 870 Officer's Leather | 3 | hip_length | same_type_sleeveless_geometry_over_tier |
| 201 | 10201 | Poltergeist | Chain | 7 | MM7 1335 Elven Chainmail | 7 | short_torso | same_type_same_tier_unique_mail |
| 202 | 10202 | Swordsbane | Plate | 7 | MM8 515 Supreme Plate | 7 | full_harness | same_type_same_tier_unique_plate |
| 220 | 10220 | Prize Plate | Plate | 7 | MM8 95 Banded Plate | 2 | short_torso | silhouette_override_unique_tier |
| 225 | 10225 | Broderick's Hauberk | Chain | 7 | MM7 1335 Elven Chainmail | 7 | hip_length | same_type_same_tier_unique_mail |
| 230 | 10230 | Death Cuirass | Leather | 7 | MM7 870 Officer's Leather | 3 | short_torso | same_type_sleeveless_geometry_over_tier |
| 367 | 10367 | Quilted Armor | Leather | 0 | MM7 868 Crude Leather Armor | 1 | short_torso | same_type_nearest_tier_plain_vest |

## Helmets

| MM9 raw | Global | MM9 item | Tier | Base | Base tier | Geometry | Selection |
| ---: | ---: | --- | ---: | --- | ---: | --- | --- |
| 116 | 10116 | Coif | 1 | MM7 893 Elven Helm | 3 | chain_hood | coverage_override_chain_coif |
| 117 | 10117 | Plain Helm | 2 | MM8 109 Helm | 1 | open_nasal_helm | silhouette_override_near_tier |
| 119 | 10119 | Barbute Helm | 2 | MM8 111 Full Helm | 3 | closed_face_helm | silhouette_override_near_tier |
| 120 | 10120 | Loaf Helm | 3 | MM7 893 Elven Helm | 3 | closed_conical_helm | same_type_same_tier_conical_helm |
| 121 | 10121 | Bascinet | 3 | MM8 111 Full Helm | 3 | closed_face_helm | same_type_same_tier_closed_helm |
| 122 | 10122 | Sallet | 4 | MM7 892 Conscript's Helm | 2 | open_round_helm | silhouette_override_simple_sallet |
| 123 | 10123 | Dragon Helm | 4 | MM8 111 Full Helm | 3 | closed_face_helm | silhouette_override_near_tier |
| 124 | 10124 | Imperial Helm | 5 | MM8 111 Full Helm | 3 | closed_face_helm | silhouette_override_closed_helm |
| 125 | 10125 | Jarl's Helm | 5 | MM8 111 Full Helm | 3 | closed_face_helm | silhouette_override_closed_helm |
| 203 | 10203 | Witchbane | 7 | MM8 520 Drogg's Helm | 7 | unique_face_mask | same_type_same_tier_unique_mask |
| 204 | 10204 | Brongnoker | 7 | MM8 109 Helm | 1 | open_nasal_helm | exact_icon_silhouette_override_unique_tier |
| 221 | 10221 | Prize Skullcap | 7 | MM7 893 Elven Helm | 3 | conical_helm | silhouette_override_unique_tier |
| 226 | 10226 | Broderick's Helm | 7 | MM8 111 Full Helm | 3 | closed_face_helm | silhouette_override_unique_tier |
| 231 | 10231 | Death Cap | 7 | MM8 520 Drogg's Helm | 7 | unique_face_mask | same_type_same_tier_unique_mask |
| 236 | 10236 | Fre's Helm | 7 | MM7 895 Mogred Helm | 5 | open_round_helm | silhouette_override_unique_tier |
| 364 | 10364 | Fur Cap | 0 | MM7 1324 Scholar's Cap | 7 | soft_cap | exact_soft_cap_coverage_override_tier |

## Boots

| MM9 raw | Global | MM9 item | Tier | Base | Base tier | Geometry | Selection |
| ---: | ---: | --- | ---: | --- | ---: | --- | --- |
| 126 | 10126 | Leather Boots | 1 | MM7 917 Leather Boots | 1 | low_ankle_boots | same_type_same_tier_plain_leather |
| 127 | 10127 | Hardened Boots | 1 | MM8 133 Hardened Leather Boots | 2 | ordinary_boots | same_type_near_tier_hardened_leather |
| 128 | 10128 | Chain Boots | 2 | MM7 917 Leather Boots | 1 | low_ankle_boots | silhouette_override_near_tier_low_chain_footwear |
| 129 | 10129 | Ronenguard Boots | 2 | MM7 918 Steel Plated Boots | 2 | plated_boots | same_type_same_tier_plated_boot |
| 130 | 10130 | Steel Boots | 3 | MM7 918 Steel Plated Boots | 2 | plated_boots | silhouette_override_near_tier |
| 131 | 10131 | Sabaton | 4 | MM7 920 Knight's Boots | 4 | tall_plated_boots | same_type_same_tier_segmented_plate |
| 132 | 10132 | Prote der Fatta | 5 | MM7 921 Paladin Boots | 5 | ornate_plated_boots | same_type_same_tier_ornate_plate |
| 205 | 10205 | Walking Boots | 7 | MM7 1314 Seven League Boots | 7 | unique_leather_boots | same_type_same_tier_unique_leather |
| 233 | 10233 | Death Boots | 7 | MM7 920 Knight's Boots | 4 | tall_plated_boots | silhouette_override_unique_tier |
| 238 | 10238 | Fre's Chain Boots | 7 | MM7 921 Paladin Boots | 5 | ornate_mail_boots | silhouette_override_unique_tier |
| 366 | 10366 | Fuzzy Slippers | 0 | MM7 917 Leather Boots | 1 | ankle_only_footwear | coverage_override_nearest_plain_footwear |

## Belts

| MM9 raw | Global | MM9 item | Tier | Base | Base tier | Geometry | Selection |
| ---: | ---: | --- | ---: | --- | ---: | --- | --- |
| 150 | 10150 | Peasant Belt | 1 | MM7 902 Leather Belt | 1 | narrow_belt | same_type_same_tier_plain_belt |
| 151 | 10151 | Fancy Belt | 2 | MM7 903 Fine Belt | 2 | narrow_belt | same_type_same_tier_fine_belt |
| 152 | 10152 | Soldier's Belt | 3 | MM7 904 Strong Belt | 3 | medium_belt | same_type_same_tier_reinforced_belt |
| 153 | 10153 | Regal Belt | 4 | MM7 905 Silver Belt | 4 | jeweled_belt | same_type_same_tier_ornate_belt |
| 154 | 10154 | Dragon Belt | 5 | MM7 906 Gilded Belt | 5 | jeweled_belt | same_type_same_tier_ornate_belt |
| 208 | 10208 | Hubris | 7 | MM7 1337 Hero's Belt | 7 | unique_medallion_belt | same_type_same_tier_unique_belt |

## Pipeline Use

For each row, the generation task must load:

1. the MM9 source PCX or promoted inventory icon;
2. every supported fitted variant belonging to `reference.item_id`;
3. the unarmored target doll and the equipped composite for fit validation; and
4. the row's `geometry_profile`, `selection_basis`, and `transfer_focus`.

The first generation pass should preserve reference placement and broad silhouette, apply any required geometry-profile
crop, and transfer only the MM9 design. The equipped composite—not the isolated output—is the acceptance image. Any
mapping which repeatedly requires reconstruction rather than a modest design transfer should be returned to this table
for remapping before further generations are accepted.
