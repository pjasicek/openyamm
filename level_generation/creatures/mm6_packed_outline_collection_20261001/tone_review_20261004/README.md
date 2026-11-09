# MM6 family tone review — 2026-10-04

The user approved the 16 recommended reductions on 2026-10-04. They are now recorded in
[the authoritative MM6 adaptations recipe](../../../../assets_source/creatures/mm6/adaptations.json) and the main
reviewer's saved colour controls. The proposal and neutral baseline below are retained as historical review evidence;
final atlas export and GPU installation are still pending.

The selected 60-family collection and saved manual placement were reviewed for broad brightness changes. This proposes mild darkening for **16 families**, keeps **39 families** neutral, and records **5 optional 4% trials** with neutral defaults. These are tone proposals, not new acceptance or runtime installation records.

Open the [isolated tone reviewer](http://127.0.0.1:8768/#mm6_goblin). Recommended families start with the proposed brightness; toggle **Preview color** to compare their current restoration. Your reviewed scale, offsets, guides and landmarks are copied unchanged. The [main reviewer](http://127.0.0.1:8767/) retains its original state. The isolated preview has no new acceptance decisions.

The proposal is [tone_modifiers.json](tone_modifiers.json). Each selected family has one RGB multiplier for all animations, stored views, palettes and unused art. Saturation stays at 1 and alpha/masks remain unchanged. Use the existing decoded-RGB brightness operation after palette recolouring. During future export, apply once to the highest-resolution retained restored material before the final resampling and GPU cook. Optional trials stay at 100% in the preview; their suggested trial is recorded separately.

All 3,486 selected frames and their palettes were examined numerically (10,170 frame/palette pairs, including two empty Cactus endpoints). These numbers screened brightness and did not determine the factors. Visual comparisons covered every family in every native palette at a primary pose plus two other poses in the base palette. All 21 recommended/optional families were then compared at three poses in every palette. Goblin, Earth Elemental, Spider and Rat received additional 1:1 physical-pixel comparisons on dark and light backdrops. This is a material/tone review; final in-game lighting is still to be checked during deployment.

Fine restored details naturally raise average brightness compared with low-resolution native art. The goal is a small adjustment to broad material weight, not forcing native luminance ratios to 1.0. Strong reductions would suppress the useful new texture.

## Per-family decisions

| Family | Proposal | Brightness | Reason |
| --- | --- | ---: | --- |
| Archer | Darken | 92% | Boots, leather and skin are lifted across palettes; a modest reduction restores some tonal weight. |
| Barbarian | Keep | 100% | Bright armour and skin are already present in the native art; the restored dark areas remain balanced. |
| Bat | Keep; optional trial | 100% (optional 96%) | Wing membranes are a little bright in blue/red variants, but the body is already dark; neutral is also reasonable. |
| Beholder | Darken | 92% | The face and horn surfaces are consistently pale and bright; retain the readable eye and texture. |
| Bloodsucker | Keep | 100% | Already dark and readable; further darkening would reduce material separation. |
| Cleric | Keep | 100% | Cloth and cape retain suitable tonal weight; concentrated metal highlights are appropriate. |
| Cobra | Keep | 100% | Natural scale highlights with balanced body shadows. |
| Cockatrice | Darken | 94% | Bronze feather surfaces and talons are conspicuously bright across palettes. |
| Flying Demon | Keep | 100% | Body and wing materials already have deep shadows and useful detail. |
| Demon | Keep | 100% | Skin remains dark; bright claws are appropriate and consistent with native materials. |
| Cave Dragon | Keep | 100% | Good body shadow and horn contrast; avoid reducing readable scale detail. |
| Flying Dragon | Keep | 100% | Gold ridges and bright belly are native design features; current shadows remain balanced. |
| Land Dragon | Keep | 100% | Vibrant belly and small highlights fit the native dragon design. |
| Dragon Cover | Keep | 100% | Bright wing and crest surfaces are present in the native art; no broad correction is needed. |
| Druidess | Keep | 100% | Cloth and skin are already close in overall tonal weight. |
| Dwarf | Keep | 100% | Leather detail is brighter but beard, clothing and metal remain balanced. |
| Air Elemental | Keep | 100% | Luminous wisps and lightning are intentional; a family-wide reduction would weaken them. |
| Earth Elemental | Darken | 90% | Broad rock faces are considerably lighter, especially the green and grey palettes. |
| Fire Elemental | Keep | 100% | Emissive flame is intentional and the restored art is already slightly darker overall. |
| Water Elemental | Keep | 100% | Water body and white foam are balanced; retain luminous foam detail. |
| Chain Fighter | Keep; optional trial | 100% (optional 96%) | Slightly shinier mail and cloth; a small reduction is optional rather than necessary. |
| Leather Fighter | Darken | 92% | Leather and skin have a strong overall brightness lift across the animation. |
| Gargoyle | Darken | 94% | Body and wing stone are consistently lighter than the surrounding native material impression. |
| Genie | Keep | 100% | Luminous colour and small bright highlights are intentional; preserve the native magical character. |
| Ghost | Keep | 100% | White spectral cloth is intentional and already balanced against its dark interior. |
| Goblin | Darken | 90% | Skin, clothing, leather and brass look excessively sunlit across all three palettes. |
| Guard | Darken | 92% | Chainmail, cloth and skin have a broad brightness lift rather than only brighter metal highlights. |
| Harpy | Darken | 95% | Feathers and talons are somewhat too bright; a small reduction retains the dark body detail. |
| Hydra | Keep | 100% | Native ventral surfaces are bright; dark necks need their present visibility. |
| Jackalman | Keep | 100% | Gold ornament and blue cloth have appropriate highlights against a dark body. |
| Plate Knight | Keep | 100% | Concentrated metal reflections are convincing while most armour stays dark. |
| Lich | Keep | 100% | Bright bones and ornament are native features; torso and boots retain shadow. |
| Lizard Archer | Darken | 94% | Green skin, orange cloth and armour are brighter overall; use the same modest setting throughout. |
| Medusa | Darken | 96% | Skin and snake highlights are slightly too pale in several poses; only a very small reduction. |
| Merchant | Keep | 100% | Clothing and flesh are balanced; several palettes already have dark cloth. |
| Minotaur | Keep; optional trial | 100% (optional 96%) | Fur and trouser highlights are somewhat brighter, but their current material contrast is convincing. |
| Monk | Keep | 100% | Robes are already dark; bright magic and small highlights are intentional. |
| Nobleman | Darken | 96% | Coloured silk and ornament are slightly too luminous across palettes; preserve the polished appearance. |
| Ooze | Keep | 100% | Wet specular highlights are appropriate; additional darkening would flatten translucent material detail. |
| Ogre | Keep | 100% | Restored material weight is close to the native impression. |
| female peasant 1 | Keep | 100% | Cream cloth and natural warm skin are balanced; bright dress areas are intentional. |
| female peasant 2 | Keep | 100% | Brown clothing, apron and skin are already balanced. |
| female peasant 3 | Keep | 100% | Blouse and skirt colours have suitable material shadows; no broad brightness correction is needed. |
| female peasant 4 | Darken | 94% | Skin and ornaments have a consistent brightness lift across all native dress palettes. |
| male peasant 1 | Keep | 100% | Light trousers are intentional and clothing and skin remain balanced. |
| male peasant 2 / town mage | Keep | 100% | Dark robe/armour and bright palette-specific accents retain appropriate contrast. |
| male peasant 3 | Keep | 100% | White cloak is a native design feature with suitable restored shadow. |
| male peasant 4 | Darken | 92% | Skin and hair have a strong lift across all palettes; retain restored texture rather than matching the native darkness. |
| Rat | Keep; optional trial | 100% (optional 96%) | Some fur palettes are brighter, but extra fur visibility is useful; prefer neutral unless the preview reads too light. |
| Robot | Keep | 100% | Metal already has deep shadows and comparable overall brightness; retain glowing eyes. |
| Sea Serpent | Keep | 100% | Bright ventral scales are native features; head and spines remain dark. |
| Skeleton | Keep | 100% | Restored bone is already darker overall, especially in coloured palettes. |
| Sorcerer | Keep | 100% | Robes remain dark; increased brightness is mostly readable piping and facial detail. |
| Spider | Darken | 94% | Legs and armour highlights are markedly brighter, especially the blue and red palettes; preserve the dark body. |
| Thief | Keep | 100% | Cloak retains dark folds; brighter face and leather detail do not require a family reduction. |
| Titan | Keep | 100% | Bright lightning and concentrated metal reflections are intentional; retain armour shadows. |
| Werewolf | Keep; optional trial | 100% (optional 96%) | Shoulder fur is slightly brighter; the current coat remains dark and detailed, so neutral is a valid choice. |
| Demon Queen | Darken | 94% | Large surrounding rock surfaces look overly illuminated; retain the original character and cavern contrast. |
| Reactor | Keep | 100% | Overall tone already matches the native impression and the central light is intentional. |
| Cactus | Keep | 100% | Foliage and pale tips are close to native tonal weight, with deep central shadow. |

## Static comparisons

Native/current contacts: `current_palettes_01.png` through `current_palettes_10.png`, with matching `current_poses_*.png`. Rows follow the collection ordering.

Current/proposed contact rows retain a common crop, magnification and saved placement. Each group has three pose pages, and every page shows all palettes. The five optional trials appear here at 96% but remain neutral in the isolated reviewer.

| Group | Families | Primary pose | Other view | Other action |
| --- | --- | --- | --- | --- |
| 1 | Archer, Bat, Beholder, Cockatrice, Earth Elemental, Chain Fighter | [Compare](proposed_01_pose_1.png) | [Compare](proposed_01_pose_2.png) | [Compare](proposed_01_pose_3.png) |
| 2 | Leather Fighter, Gargoyle, Goblin, Guard, Harpy, Lizard Archer | [Compare](proposed_02_pose_1.png) | [Compare](proposed_02_pose_2.png) | [Compare](proposed_02_pose_3.png) |
| 3 | Medusa, Minotaur, Nobleman, female peasant 4, male peasant 4, Rat | [Compare](proposed_03_pose_1.png) | [Compare](proposed_03_pose_2.png) | [Compare](proposed_03_pose_3.png) |
| 4 | Spider, Werewolf, Demon Queen | [Compare](proposed_04_pose_1.png) | [Compare](proposed_04_pose_2.png) | [Compare](proposed_04_pose_3.png) |

Detail panels: [Goblin dark](detail_goblin_dark.png), [Goblin light](detail_goblin_light.png), [Earth dark](detail_ert_dark.png), [Earth light](detail_ert_light.png), [Spider dark](detail_spi1_dark.png), [Spider light](detail_spi1_light.png), [Rat dark](detail_rat_dark.png), [Rat light](detail_rat_light.png).

Snapshot/provenance: `reviewed_fixups_snapshot.json` is the unchanged reviewed baseline; `preview_state/frame_fixups.json` is a selected-art-only copy with the 16 proposed family settings. `audit.json` contains per-palette statistics and the pinned collection/manifest hashes. Source projects, accepted sheets, atlases, main review decisions and runtime assets are unchanged.

Restart the same shared reviewer from the repository root if needed:

```sh
python3 -B level_generation/creatures/mm6_remaining/acceptance_viewer/serve.py \
  --collection level_generation/creatures/mm6_packed_outline_collection_20261001/collection.json \
  --state-dir level_generation/creatures/mm6_packed_outline_collection_20261001/tone_review_20261004/preview_state \
  --port 8768
```
