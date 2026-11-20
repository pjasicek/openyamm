# Garrote Gorge building and resident catalogue

[Searchable visual catalogue](index.html) · [House contact sheet](images/contact_houses.jpg) · [Walls/keep sheet](images/contact_walls_keep.jpg) · [Material roles](images/texture_roles.png) · [Complete face/UV/occupancy data](catalogue.json) · [MM5 mapping](../../projects/mm5_castleview_kalindra/GARROTE_STYLE_MAPPING.md)

All 56 native BModels are inventoried and partitioned into physical assemblies. Original geometry is used only for reference views; new MM5 geometry must be authored independently.

## Assemblies and occupants

| Assembly | BModels | Dimensions XYZ | Occupants / proprietor | Actual house destinations |
| --- | --- | --- | --- | --- |
| Dragon Cave entrance | 0, 1 | 992 × 1408 × 512 | inside Ishton's Cave: Jerin Flame-eye, Ishton, Bazalath; inside Ithilgore's Cave: Erthint, Ithilgore; inside Scarwing's Cave: Balion Tearwing, Klain Scarwing; inside Dragon Leader's Cavern : Deftclaw Redreaver | d17.blv |
| Eastern chest 1 | 2 | 64 × 96 × 80 | No fixed house NPC; see entry/prop records | — |
| Eastern chest 2 | 3 | 64 × 96 × 80 | No fixed house NPC; see entry/prop records | — |
| Grand Temple of Eep entrance | 4 | 1107 × 5634 × 512 | No fixed house NPC; see entry/prop records | d44.blv |
| Obelisk | 5 | 128 × 128 × 1280 | No fixed house NPC; see entry/prop records | — |
| Training tents A | 6 | 1312 × 1416 × 304 | No fixed house NPC; see entry/prop records | — |
| Training tent B | 7 | 992 × 624 × 432 | No fixed house NPC; see entry/prop records | — |
| Training tents C | 8 | 1992 × 2024 × 432 | No fixed house NPC; see entry/prop records | — |
| Dragon Hunter Camp walls and gate | 9, 10, 11, 12 | 7642 × 6834 × 1280 | No fixed house NPC; see entry/prop records | — |
| Dragon Hunter Camp keep | 13, 14, 15 | 2816 × 2560 × 960 | inside Charles Quixote's House: Sir Charles Quixote | d16.blv |
| Wards and Pendants | 16 | 790 × 640 × 464 | Korxius (proprietor) | 79 |
| Sacred Steel | 17 | 1024 × 896 × 640 | Laudra (proprietor) | 306 |
| Guild Caravans | 18 | 1056 × 640 × 384 | Dalas (proprietor) | 455 |
| Lance’s Spears | 19 | 928 × 592 × 384 | Lance (proprietor) | 4 |
| Plated Protection | 20 | 832 × 768 × 480 | Balfour (proprietor) | 39 |
| Dragon’s Blood Inn | 21, 22 | 1152 × 1408 × 672 | Melody (proprietor) | 232 |
| Camp well | 23 | 256 × 256 × 216 | No fixed house NPC; see entry/prop records | — |
| Ironfist Residence | 24 | 640 × 960 × 704 | Sethine Ironfist; Chadric Benson | 541 |
| Foestryke Residence | 25 | 832 × 704 × 384 | Zelim; Herald Foestryke | 540 |
| Village well A | 26 | 256 × 256 × 216 | No fixed house NPC; see entry/prop records | — |
| Calandril’s Residence | 27 | 704 × 832 × 384 | Calindril | 566 |
| Maker Residence | 28 | 960 × 640 × 704 | Tessa Maker | 567 |
| Kern Residence | 29 | 576 × 448 × 384 | Bethold Kern | 569 |
| Village well B | 30 | 256 × 256 × 216 | No fixed house NPC; see entry/prop records | — |
| Morningstar Residence | 31 | 576 × 448 × 384 | Robert Morningstar; Isram Delver | 539 |
| Reaverston Residence | 32 | 960 × 640 × 704 | Peryn Reaverston | 542 |
| River bridge | 33, 34 | 3584 × 864 × 720 | No fixed house NPC; see entry/prop records | — |
| Otterton Residence | 35, 36 | 1088 × 1408 × 464 | Kenneth Otterton | 565 |
| Arin Residence | 37, 38 | 1408 × 1088 × 464 | Tugor Arin | 563 |
| Weldrick’s Home | 39, 40 | 1088 × 1408 × 464 | Weldrik Falconeye | 571 |
| Slayer Residence | 41 | 896 × 768 × 448 | Norbert Slayer | 568 |
| Nelix’s House | 42 | 768 × 896 × 448 | Nelix Uriel | 699 |
| Jeni Residence | 43 | 960 × 512 × 384 | Quick Jeni | 570 |
| Tempus’ House | 44 | 512 × 960 × 384 | Tempus | 700 |
| Avalon’s Residence | 45 | 512 × 960 × 384 | Avalon | 562 |
| Stormlance Residence | 46 | 960 × 512 × 384 | Leane Stormlance; Jaycin Cardron | 538 |
| Lightsworn Residence | 47 | 768 × 896 × 448 | Wanda Lightsworn | 564 |
| Southern chest | 48 | 96 × 64 × 80 | No fixed house NPC; see entry/prop records | — |
| Naga Vault entrance complex | 49, 50, 51, 52, 53 | 3072 × 3840 × 1536 | No fixed house NPC; see entry/prop records | d18.blv |
| Godric’s Gauntlet | 54, 55 | 1536 × 1408 × 832 | Godric (proprietor) | 1567 |

## Important distinctions

- The walled reference is the **Dragon Hunter Camp**, whose keep enters `d16.blv`. The Dragon Cave and Naga Vault are different structures. Kalindra borrows the camp’s construction vocabulary, not its MM8 faction or quests.
- Four two-person homes: Stormlance (Leane/Jaycin), Morningstar (Robert/Isram), Foestryke (Zelim/Herald), Ironfist (Sethine/Chadric). Morningstar is a compact 576×448 cottage: two occupants do not require a rich estate.
- The six services inside the camp are individually modeled. Godric’s training hall stands outside that group and consists of parts54–55. Joined multi-destination blocks in Castleview are new compositions inspired by this kit; they are not a claim that Garrote already uses Ravenshore’s block pattern.
- Parts35–36,37–38,39–40 are paired house wings. Part39 repeats an Otterton hint but belongs geometrically with Weldrick’s actual entrance on40. Count the actual destination once.
- House-table Placeholder is not a named resident. Service proprietors and NPC-table occupants are reported separately.
- Rendered village houses use green-grey masonry and rounded green roof tiles, with different trim and silhouettes; poor/med/rich model names do not establish different wall materials. A shared material family does not mean identical construction quality, footprint or roof height everywhere.
- Exact native face dimensions, texture sizes, UV offsets and entrance normals remain in the JSON. Reference images are independently framed; use measurements for scale.

Rebuild data/docs with `python3 level_generation/scripts/catalogue_garrote.py`; render the recorded views through the parameterized `blender_building_catalogue.py` in a separate study scene, then run `python3 level_generation/scripts/review_garrote_catalogue.py` for contact sheets and source/render checks.
