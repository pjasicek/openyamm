# Terrain Tile Inventory

Generated from the active OpenYAMM terrain descriptor tables under `assets_dev/engine/data_tables/`.

## Source Mapping

| World | Table | Runtime selection |
|---|---|---|
| MM6 | `terrain_tile_data_3.txt` | `TerrainTileData.cpp` selects this for world id `mm6`. |
| MM7 | `terrain_tile_data_2.txt` | `TerrainTileData.cpp` selects this for world id `mm7`. |
| MM8 | `terrain_tile_data.txt` | Default table for world id `mm8` and fallback. |

Rows below are descriptor table row indexes. Outdoor maps still build their 256 runtime tile descriptors through the map master-tile and tileset lookup indirection in `TerrainTileData.cpp`.

## Flag Legend

| Bit | Meaning in OpenYAMM | Runtime use |
|---:|---|---|
| `0x0001` | Burn | Applied to outdoor movement attributes. |
| `0x0002` | Water | Applied to outdoor movement attributes and terrain water rendering. |
| `0x0040` | Unused/Pending | Present on pending placeholder rows. |
| `0x0100` | Shore | Used as terrain material metadata. |
| `0x0200` | Transition | Used for terrain transition/overlay material handling. |

## Summary

| World | Rows | Texture Rows | Unique Textures | Pending Rows | Blank Rows | Flag Distribution |
|---|---:|---:|---:|---:|---:|---|
| MM6 | 882 | 495 | 291 | 78 | 309 | 0x0000: 418<br>0x0002: 12<br>0x0040: 65<br>0x0100: 12<br>0x0200: 363<br>0x0300: 12 |
| MM7 | 882 | 431 | 108 | 78 | 373 | 0x0000: 458<br>0x0002: 24<br>0x0040: 65<br>0x0100: 24<br>0x0200: 287<br>0x0300: 24 |
| MM8 | 882 | 528 | 272 | 78 | 276 | 0x0000: 421<br>0x0002: 48<br>0x0003: 24<br>0x0040: 65<br>0x0100: 24<br>0x0200: 228<br>0x0300: 72 |

## Current Asset Placement Check

This is a case-insensitive stem check against image files under `assets_dev/engine` and `assets_dev/worlds/mm*`.
It is included to guide the terrain/textures split; the terrain descriptor tables remain the authoritative source.

| World | Unique Terrain Textures | In `terrain/` | In `terrain_x4/` | In `textures/` | In `textures_x4/` | Missing From Base `terrain/` + `textures/` |
|---|---:|---:|---:|---:|---:|---:|
| MM6 | 291 | 0 | 0 | 145 | 145 | 146 |
| MM7 | 108 | 0 | 1 | 108 | 10 | 0 |
| MM8 | 272 | 0 | 50 | 272 | 272 | 0 |

Findings:

- `terrain/` has no base-resolution terrain tiles yet.
- `terrain_x4/` is partial and currently only covers MM7/MM8 names.
- MM8 terrain is fully present in `textures/` and `textures_x4/`.
- MM7 terrain is fully present in base `textures/`, but mostly not in `textures_x4/`.
- MM6 terrain has only 145 of 291 names present in the current checked base/x4 texture roots, so MM6 needs a separate pass before moving terrain assets.

## MM6

Source: `assets_dev/engine/data_tables/terrain_tile_data_3.txt`

- Rows: 882
- Texture rows: 495
- Unique texture names: 291
- Pending placeholder rows: 78 (`0, 13-89`)
- Blank texture rows: 309 (`114-125, 150-161, 186-197, 222-233, 258-269, 294-305, 330-341, 366-377, 402-413, 437-449, 473-485, 509-521, 545-557, 581-593, 617-629, 653-665, 689-701, 717-737, 753-773, 797-809, 825-845, 861-881`)

### MM6 Tileset Summary

| Tileset | Count | Rows | Nonblank Textures | Flags |
|---:|---:|---|---:|---|
| 0 | 113 | 13-125 | 13 | 0x0000 None<br>0x0040 Unused/Pending<br>0x0200 Transition |
| 1 | 36 | 342-377 | 13 | 0x0000 None<br>0x0200 Transition |
| 2 | 36 | 234-269 | 13 | 0x0000 None<br>0x0200 Transition |
| 3 | 36 | 198-233 | 13 | 0x0000 None<br>0x0200 Transition |
| 4 | 12 | 1-12 | 1 | 0x0000 None |
| 5 | 36 | 126-161 | 13 | 0x0002 Water<br>0x0100 Shore<br>0x0300 Shore, Transition |
| 6 | 36 | 162-197 | 13 | 0x0000 None<br>0x0200 Transition |
| 7 | 36 | 270-305 | 13 | 0x0000 None<br>0x0200 Transition |
| 8 | 36 | 306-341 | 13 | 0x0000 None<br>0x0200 Transition |
| 9 | 36 | 378-413 | 13 | 0x0000 None<br>0x0200 Transition |
| 10 | 36 | 414-449 | 16 | 0x0000 None<br>0x0200 Transition |
| 11 | 36 | 450-485 | 15 | 0x0000 None<br>0x0200 Transition |
| 12 | 36 | 486-521 | 16 | 0x0000 None<br>0x0200 Transition |
| 13 | 36 | 522-557 | 16 | 0x0000 None<br>0x0200 Transition |
| 16 | 44 | 558-593, 609-616 | 16 | 0x0000 None<br>0x0200 Transition |
| 17 | 28 | 594-608, 617-629 | 15 | 0x0000 None<br>0x0200 Transition |
| 22 | 36 | 774-809 | 23 | 0x0000 None<br>0x0200 Transition |
| 23 | 36 | 810-845 | 15 | 0x0000 None<br>0x0200 Transition |
| 24 | 36 | 702-737 | 15 | 0x0000 None<br>0x0200 Transition |
| 25 | 36 | 738-773 | 1 | 0x0000 None<br>0x0200 Transition |
| 26 | 44 | 630-665, 681-688 | 16 | 0x0000 None<br>0x0200 Transition |
| 27 | 28 | 666-680, 689-701 | 15 | 0x0000 None<br>0x0200 Transition |
| 28 | 36 | 846-881 | 15 | 0x0000 None<br>0x0200 Transition |
| 255 | 1 | 0 | 0 | 0x0040 Unused/Pending |

### MM6 Unique Terrain Textures

| Texture | Count | Rows | Tilesets | Flags |
|---|---:|---|---|---|
| `6dirttyl` | 12 | 1-12 | 4 | 0x0000 None |
| `6drsrcros` | 1 | 774 | 22 | 0x0200 Transition |
| `6drsrecap` | 1 | 786 | 22 | 0x0200 Transition |
| `6drsrew` | 1 | 776 | 22 | 0x0200 Transition |
| `6drsrew_n` | 1 | 783 | 22 | 0x0200 Transition |
| `6drsrew_s` | 1 | 784 | 22 | 0x0200 Transition |
| `6drsrn_e` | 1 | 777 | 22 | 0x0200 Transition |
| `6drsrn_w` | 1 | 778 | 22 | 0x0200 Transition |
| `6drsrncap` | 1 | 785 | 22 | 0x0200 Transition |
| `6drsrns` | 1 | 775 | 22 | 0x0200 Transition |
| `6drsrns_e` | 1 | 781 | 22 | 0x0200 Transition |
| `6drsrns_w` | 1 | 782 | 22 | 0x0200 Transition |
| `6drsrs_e` | 1 | 779 | 22 | 0x0200 Transition |
| `6drsrs_w` | 1 | 780 | 22 | 0x0200 Transition |
| `6drsrscap` | 1 | 787 | 22 | 0x0200 Transition |
| `6drsrwcap` | 1 | 788 | 22 | 0x0200 Transition |
| `6grastyl` | 20 | 90-101, 429-436 | 0, 10 | 0x0000 None<br>0x0200 Transition |
| `6grdrte` | 1 | 106 | 0 | 0x0200 Transition |
| `6grdrtn` | 1 | 108 | 0 | 0x0200 Transition |
| `6grdrtne` | 1 | 102 | 0 | 0x0200 Transition |
| `6grdrtnw` | 1 | 104 | 0 | 0x0200 Transition |
| `6grdrts` | 1 | 109 | 0 | 0x0200 Transition |
| `6grdrtse` | 1 | 103 | 0 | 0x0200 Transition |
| `6grdrtsw` | 1 | 105 | 0 | 0x0200 Transition |
| `6grdrtw` | 1 | 107 | 0 | 0x0200 Transition |
| `6grdrtxne` | 1 | 110 | 0 | 0x0200 Transition |
| `6grdrtxnw` | 1 | 112 | 0 | 0x0200 Transition |
| `6grdrtxse` | 1 | 111 | 0 | 0x0200 Transition |
| `6grdrtxsw` | 1 | 113 | 0 | 0x0200 Transition |
| `6sandtyl` | 20 | 234-245, 537-544 | 2, 13 | 0x0000 None<br>0x0200 Transition |
| `6sndrte` | 1 | 250 | 2 | 0x0200 Transition |
| `6sndrtn` | 1 | 252 | 2 | 0x0200 Transition |
| `6sndrtne` | 1 | 246 | 2 | 0x0200 Transition |
| `6sndrtnw` | 1 | 248 | 2 | 0x0200 Transition |
| `6sndrts` | 1 | 253 | 2 | 0x0200 Transition |
| `6sndrtse` | 1 | 247 | 2 | 0x0200 Transition |
| `6sndrtsw` | 1 | 249 | 2 | 0x0200 Transition |
| `6sndrtw` | 1 | 251 | 2 | 0x0200 Transition |
| `6sndrtxne` | 1 | 254 | 2 | 0x0200 Transition |
| `6sndrtxnw` | 1 | 256 | 2 | 0x0200 Transition |
| `6sndrtxse` | 1 | 255 | 2 | 0x0200 Transition |
| `6sndrtxsw` | 1 | 257 | 2 | 0x0200 Transition |
| `6voltyl` | 28 | 198-209, 573-580, 609-616 | 3, 16 | 0x0000 None<br>0x0200 Transition |
| `6wtrdre` | 1 | 142 | 5 | 0x0300 Shore, Transition |
| `6wtrdrn` | 1 | 144 | 5 | 0x0300 Shore, Transition |
| `6wtrdrne` | 1 | 138 | 5 | 0x0300 Shore, Transition |
| `6wtrdrnw` | 1 | 140 | 5 | 0x0300 Shore, Transition |
| `6wtrdrs` | 1 | 145 | 5 | 0x0300 Shore, Transition |
| `6wtrdrse` | 1 | 139 | 5 | 0x0300 Shore, Transition |
| `6wtrdrsw` | 1 | 141 | 5 | 0x0300 Shore, Transition |
| `6wtrdrw` | 1 | 143 | 5 | 0x0300 Shore, Transition |
| `6wtrdrxne` | 1 | 146 | 5 | 0x0300 Shore, Transition |
| `6wtrdrxnw` | 1 | 148 | 5 | 0x0300 Shore, Transition |
| `6wtrdrxse` | 1 | 147 | 5 | 0x0300 Shore, Transition |
| `6wtrdrxsw` | 1 | 149 | 5 | 0x0300 Shore, Transition |
| `6wtrtyl` | 12 | 126-137 | 5 | 0x0002 Water |
| `7drsrcros1` | 1 | 789 | 22 | 0x0200 Transition |
| `7drsrcros2` | 1 | 790 | 22 | 0x0200 Transition |
| `7drsrcros3` | 1 | 791 | 22 | 0x0200 Transition |
| `7drsrcros4` | 1 | 792 | 22 | 0x0200 Transition |
| `7drsrne1` | 1 | 793 | 22 | 0x0200 Transition |
| `7drsrne2` | 1 | 794 | 22 | 0x0200 Transition |
| `7drsrnw1` | 1 | 795 | 22 | 0x0200 Transition |
| `7drsrnw2` | 1 | 796 | 22 | 0x0200 Transition |
| `crkdrte` | 1 | 178 | 6 | 0x0200 Transition |
| `crkdrtn` | 1 | 180 | 6 | 0x0200 Transition |
| `crkdrtne` | 1 | 174 | 6 | 0x0200 Transition |
| `crkdrtnw` | 1 | 176 | 6 | 0x0200 Transition |
| `crkdrts` | 1 | 181 | 6 | 0x0200 Transition |
| `crkdrtse` | 1 | 175 | 6 | 0x0200 Transition |
| `crkdrtsw` | 1 | 177 | 6 | 0x0200 Transition |
| `crkdrtw` | 1 | 179 | 6 | 0x0200 Transition |
| `crkdrtxne` | 1 | 182 | 6 | 0x0200 Transition |
| `crkdrtxnw` | 1 | 184 | 6 | 0x0200 Transition |
| `crkdrtxse` | 1 | 183 | 6 | 0x0200 Transition |
| `crkdrtxsw` | 1 | 185 | 6 | 0x0200 Transition |
| `crktyl` | 12 | 162-173 | 6 | 0x0000 None |
| `csdre` | 1 | 394 | 9 | 0x0200 Transition |
| `csdrn` | 1 | 396 | 9 | 0x0200 Transition |
| `csdrne` | 1 | 390 | 9 | 0x0200 Transition |
| `csdrnw` | 1 | 392 | 9 | 0x0200 Transition |
| `csdrs` | 1 | 397 | 9 | 0x0200 Transition |
| `csdrse` | 1 | 391 | 9 | 0x0200 Transition |
| `csdrsw` | 1 | 393 | 9 | 0x0200 Transition |
| `csdrw` | 1 | 395 | 9 | 0x0200 Transition |
| `csdrxne` | 1 | 398 | 9 | 0x0200 Transition |
| `csdrxnw` | 1 | 400 | 9 | 0x0200 Transition |
| `csdrxse` | 1 | 399 | 9 | 0x0200 Transition |
| `csdrxsw` | 1 | 401 | 9 | 0x0200 Transition |
| `csrcros` | 2 | 702, 846 | 24, 28 | 0x0200 Transition |
| `csrecap` | 2 | 714, 858 | 24, 28 | 0x0200 Transition |
| `csrew` | 2 | 704, 848 | 24, 28 | 0x0200 Transition |
| `csrew_n` | 2 | 711, 855 | 24, 28 | 0x0200 Transition |
| `csrew_s` | 2 | 712, 856 | 24, 28 | 0x0200 Transition |
| `csrn_e` | 2 | 705, 849 | 24, 28 | 0x0200 Transition |
| `csrn_w` | 2 | 706, 850 | 24, 28 | 0x0200 Transition |
| `csrncap` | 2 | 713, 857 | 24, 28 | 0x0200 Transition |
| `csrns` | 2 | 703, 847 | 24, 28 | 0x0200 Transition |
| `csrns_e` | 2 | 709, 853 | 24, 28 | 0x0200 Transition |
| `csrns_w` | 2 | 710, 854 | 24, 28 | 0x0200 Transition |
| `csrs_e` | 2 | 707, 851 | 24, 28 | 0x0200 Transition |
| `csrs_w` | 2 | 708, 852 | 24, 28 | 0x0200 Transition |
| `csrscap` | 2 | 715, 859 | 24, 28 | 0x0200 Transition |
| `csrwcap` | 2 | 716, 860 | 24, 28 | 0x0200 Transition |
| `cstyl` | 12 | 378-389 | 9 | 0x0000 None |
| `drrdcros` | 1 | 810 | 23 | 0x0200 Transition |
| `drrdecap` | 1 | 822 | 23 | 0x0200 Transition |
| `drrdew` | 1 | 812 | 23 | 0x0200 Transition |
| `drrdew_n` | 1 | 819 | 23 | 0x0200 Transition |
| `drrdew_s` | 1 | 820 | 23 | 0x0200 Transition |
| `drrdn_e` | 1 | 813 | 23 | 0x0200 Transition |
| `drrdn_w` | 1 | 814 | 23 | 0x0200 Transition |
| `drrdncap` | 1 | 821 | 23 | 0x0200 Transition |
| `drrdns` | 1 | 811 | 23 | 0x0200 Transition |
| `drrdns_e` | 1 | 817 | 23 | 0x0200 Transition |
| `drrdns_w` | 1 | 818 | 23 | 0x0200 Transition |
| `drrds_e` | 1 | 815 | 23 | 0x0200 Transition |
| `drrds_w` | 1 | 816 | 23 | 0x0200 Transition |
| `drrdscap` | 1 | 823 | 23 | 0x0200 Transition |
| `drrdwcap` | 1 | 824 | 23 | 0x0200 Transition |
| `grrdcros` | 9 | 450, 465-472 | 11 | 0x0200 Transition |
| `grrdecap` | 1 | 462 | 11 | 0x0200 Transition |
| `grrdew` | 1 | 452 | 11 | 0x0200 Transition |
| `grrdew_n` | 1 | 459 | 11 | 0x0200 Transition |
| `grrdew_s` | 1 | 460 | 11 | 0x0200 Transition |
| `grrdn_e` | 1 | 453 | 11 | 0x0200 Transition |
| `grrdn_w` | 1 | 454 | 11 | 0x0200 Transition |
| `grrdncap` | 1 | 461 | 11 | 0x0200 Transition |
| `grrdns` | 1 | 451 | 11 | 0x0200 Transition |
| `grrdns_e` | 1 | 457 | 11 | 0x0200 Transition |
| `grrdns_w` | 1 | 458 | 11 | 0x0200 Transition |
| `grrds_e` | 1 | 455 | 11 | 0x0200 Transition |
| `grrds_w` | 1 | 456 | 11 | 0x0200 Transition |
| `grrdscap` | 1 | 463 | 11 | 0x0200 Transition |
| `grrdwcap` | 1 | 464 | 11 | 0x0200 Transition |
| `grsrcros` | 1 | 414 | 10 | 0x0200 Transition |
| `grsrecap` | 1 | 426 | 10 | 0x0200 Transition |
| `grsrew` | 1 | 416 | 10 | 0x0200 Transition |
| `grsrew_n` | 1 | 423 | 10 | 0x0200 Transition |
| `grsrew_s` | 1 | 424 | 10 | 0x0200 Transition |
| `grsrn_e` | 1 | 417 | 10 | 0x0200 Transition |
| `grsrn_w` | 1 | 418 | 10 | 0x0200 Transition |
| `grsrncap` | 1 | 425 | 10 | 0x0200 Transition |
| `grsrns` | 1 | 415 | 10 | 0x0200 Transition |
| `grsrns_e` | 1 | 421 | 10 | 0x0200 Transition |
| `grsrns_w` | 1 | 422 | 10 | 0x0200 Transition |
| `grsrs_e` | 1 | 419 | 10 | 0x0200 Transition |
| `grsrs_w` | 1 | 420 | 10 | 0x0200 Transition |
| `grsrscap` | 1 | 427 | 10 | 0x0200 Transition |
| `grsrwcap` | 1 | 428 | 10 | 0x0200 Transition |
| `sndrcros` | 1 | 522 | 13 | 0x0200 Transition |
| `sndrecap` | 1 | 534 | 13 | 0x0200 Transition |
| `sndrew` | 1 | 524 | 13 | 0x0200 Transition |
| `sndrew_n` | 1 | 531 | 13 | 0x0200 Transition |
| `sndrew_s` | 1 | 532 | 13 | 0x0200 Transition |
| `sndrn_e` | 1 | 525 | 13 | 0x0200 Transition |
| `sndrn_w` | 1 | 526 | 13 | 0x0200 Transition |
| `sndrncap` | 1 | 533 | 13 | 0x0200 Transition |
| `sndrns` | 1 | 523 | 13 | 0x0200 Transition |
| `sndrns_e` | 1 | 529 | 13 | 0x0200 Transition |
| `sndrns_w` | 1 | 530 | 13 | 0x0200 Transition |
| `sndrs_e` | 1 | 527 | 13 | 0x0200 Transition |
| `sndrs_w` | 1 | 528 | 13 | 0x0200 Transition |
| `sndrscap` | 1 | 535 | 13 | 0x0200 Transition |
| `sndrwcap` | 1 | 536 | 13 | 0x0200 Transition |
| `snodre` | 1 | 358 | 1 | 0x0200 Transition |
| `snodrn` | 1 | 360 | 1 | 0x0200 Transition |
| `snodrne` | 1 | 354 | 1 | 0x0200 Transition |
| `snodrnw` | 1 | 356 | 1 | 0x0200 Transition |
| `snodrs` | 1 | 361 | 1 | 0x0200 Transition |
| `snodrse` | 1 | 355 | 1 | 0x0200 Transition |
| `snodrsw` | 1 | 357 | 1 | 0x0200 Transition |
| `snodrw` | 1 | 359 | 1 | 0x0200 Transition |
| `snodrxne` | 1 | 362 | 1 | 0x0200 Transition |
| `snodrxnw` | 1 | 364 | 1 | 0x0200 Transition |
| `snodrxse` | 1 | 363 | 1 | 0x0200 Transition |
| `snodrxsw` | 1 | 365 | 1 | 0x0200 Transition |
| `snotyl` | 20 | 342-353, 501-508 | 1, 12 | 0x0000 None<br>0x0200 Transition |
| `snsrcros` | 1 | 486 | 12 | 0x0200 Transition |
| `snsrecap` | 1 | 498 | 12 | 0x0200 Transition |
| `snsrew` | 1 | 488 | 12 | 0x0200 Transition |
| `snsrew_n` | 1 | 495 | 12 | 0x0200 Transition |
| `snsrew_s` | 1 | 496 | 12 | 0x0200 Transition |
| `snsrn_e` | 1 | 489 | 12 | 0x0200 Transition |
| `snsrn_w` | 1 | 490 | 12 | 0x0200 Transition |
| `snsrncap` | 1 | 497 | 12 | 0x0200 Transition |
| `snsrns` | 1 | 487 | 12 | 0x0200 Transition |
| `snsrns_e` | 1 | 493 | 12 | 0x0200 Transition |
| `snsrns_w` | 1 | 494 | 12 | 0x0200 Transition |
| `snsrs_e` | 1 | 491 | 12 | 0x0200 Transition |
| `snsrs_w` | 1 | 492 | 12 | 0x0200 Transition |
| `snsrscap` | 1 | 499 | 12 | 0x0200 Transition |
| `snsrwcap` | 1 | 500 | 12 | 0x0200 Transition |
| `swmdre` | 1 | 286 | 7 | 0x0200 Transition |
| `swmdrn` | 1 | 288 | 7 | 0x0200 Transition |
| `swmdrne` | 1 | 282 | 7 | 0x0200 Transition |
| `swmdrnw` | 1 | 284 | 7 | 0x0200 Transition |
| `swmdrs` | 1 | 289 | 7 | 0x0200 Transition |
| `swmdrse` | 1 | 283 | 7 | 0x0200 Transition |
| `swmdrsw` | 1 | 285 | 7 | 0x0200 Transition |
| `swmdrw` | 1 | 287 | 7 | 0x0200 Transition |
| `swmdrxne` | 1 | 290 | 7 | 0x0200 Transition |
| `swmdrxnw` | 1 | 292 | 7 | 0x0200 Transition |
| `swmdrxse` | 1 | 291 | 7 | 0x0200 Transition |
| `swmdrxsw` | 1 | 293 | 7 | 0x0200 Transition |
| `swmtyl` | 12 | 270-281 | 7 | 0x0000 None |
| `tropcros` | 1 | 666 | 27 | 0x0200 Transition |
| `trope` | 1 | 322 | 8 | 0x0200 Transition |
| `tropecap` | 1 | 678 | 27 | 0x0200 Transition |
| `tropew` | 1 | 668 | 27 | 0x0200 Transition |
| `tropew_n` | 1 | 675 | 27 | 0x0200 Transition |
| `tropew_s` | 1 | 676 | 27 | 0x0200 Transition |
| `tropn` | 1 | 324 | 8 | 0x0200 Transition |
| `tropn_e` | 1 | 669 | 27 | 0x0200 Transition |
| `tropn_w` | 1 | 670 | 27 | 0x0200 Transition |
| `tropncap` | 1 | 677 | 27 | 0x0200 Transition |
| `tropne` | 1 | 318 | 8 | 0x0200 Transition |
| `tropns` | 1 | 667 | 27 | 0x0200 Transition |
| `tropns_e` | 1 | 673 | 27 | 0x0200 Transition |
| `tropns_w` | 1 | 674 | 27 | 0x0200 Transition |
| `tropnw` | 1 | 320 | 8 | 0x0200 Transition |
| `trops` | 1 | 325 | 8 | 0x0200 Transition |
| `trops_e` | 1 | 671 | 27 | 0x0200 Transition |
| `trops_w` | 1 | 672 | 27 | 0x0200 Transition |
| `tropscap` | 1 | 679 | 27 | 0x0200 Transition |
| `tropse` | 1 | 319 | 8 | 0x0200 Transition |
| `tropsw` | 1 | 321 | 8 | 0x0200 Transition |
| `troptyl` | 43 | 306-317, 645-652, 681-688, 738-752 | 8, 25-26 | 0x0000 None<br>0x0200 Transition |
| `tropw` | 1 | 323 | 8 | 0x0200 Transition |
| `tropwcap` | 1 | 680 | 27 | 0x0200 Transition |
| `tropxne` | 1 | 326 | 8 | 0x0200 Transition |
| `tropxnw` | 1 | 328 | 8 | 0x0200 Transition |
| `tropxse` | 1 | 327 | 8 | 0x0200 Transition |
| `tropxsw` | 1 | 329 | 8 | 0x0200 Transition |
| `trsrcros` | 1 | 630 | 26 | 0x0200 Transition |
| `trsrecap` | 1 | 642 | 26 | 0x0200 Transition |
| `trsrew` | 1 | 632 | 26 | 0x0200 Transition |
| `trsrew_n` | 1 | 639 | 26 | 0x0200 Transition |
| `trsrew_s` | 1 | 640 | 26 | 0x0200 Transition |
| `trsrn_e` | 1 | 633 | 26 | 0x0200 Transition |
| `trsrn_w` | 1 | 634 | 26 | 0x0200 Transition |
| `trsrncap` | 1 | 641 | 26 | 0x0200 Transition |
| `trsrns` | 1 | 631 | 26 | 0x0200 Transition |
| `trsrns_e` | 1 | 637 | 26 | 0x0200 Transition |
| `trsrns_w` | 1 | 638 | 26 | 0x0200 Transition |
| `trsrs_e` | 1 | 635 | 26 | 0x0200 Transition |
| `trsrs_w` | 1 | 636 | 26 | 0x0200 Transition |
| `trsrscap` | 1 | 643 | 26 | 0x0200 Transition |
| `trsrwcap` | 1 | 644 | 26 | 0x0200 Transition |
| `vldrcros` | 1 | 594 | 17 | 0x0200 Transition |
| `vldrecap` | 1 | 606 | 17 | 0x0200 Transition |
| `vldrew` | 1 | 596 | 17 | 0x0200 Transition |
| `vldrew_n` | 1 | 603 | 17 | 0x0200 Transition |
| `vldrew_s` | 1 | 604 | 17 | 0x0200 Transition |
| `vldrn_e` | 1 | 597 | 17 | 0x0200 Transition |
| `vldrn_w` | 1 | 598 | 17 | 0x0200 Transition |
| `vldrncap` | 1 | 605 | 17 | 0x0200 Transition |
| `vldrns` | 1 | 595 | 17 | 0x0200 Transition |
| `vldrns_e` | 1 | 601 | 17 | 0x0200 Transition |
| `vldrns_w` | 1 | 602 | 17 | 0x0200 Transition |
| `vldrs_e` | 1 | 599 | 17 | 0x0200 Transition |
| `vldrs_w` | 1 | 600 | 17 | 0x0200 Transition |
| `vldrscap` | 1 | 607 | 17 | 0x0200 Transition |
| `vldrwcap` | 1 | 608 | 17 | 0x0200 Transition |
| `vlsrcros` | 1 | 558 | 16 | 0x0200 Transition |
| `vlsrecap` | 1 | 570 | 16 | 0x0200 Transition |
| `vlsrew` | 1 | 560 | 16 | 0x0200 Transition |
| `vlsrew_n` | 1 | 567 | 16 | 0x0200 Transition |
| `vlsrew_s` | 1 | 568 | 16 | 0x0200 Transition |
| `vlsrn_e` | 1 | 561 | 16 | 0x0200 Transition |
| `vlsrn_w` | 1 | 562 | 16 | 0x0200 Transition |
| `vlsrncap` | 1 | 569 | 16 | 0x0200 Transition |
| `vlsrns` | 1 | 559 | 16 | 0x0200 Transition |
| `vlsrns_e` | 1 | 565 | 16 | 0x0200 Transition |
| `vlsrns_w` | 1 | 566 | 16 | 0x0200 Transition |
| `vlsrs_e` | 1 | 563 | 16 | 0x0200 Transition |
| `vlsrs_w` | 1 | 564 | 16 | 0x0200 Transition |
| `vlsrscap` | 1 | 571 | 16 | 0x0200 Transition |
| `vlsrwcap` | 1 | 572 | 16 | 0x0200 Transition |
| `voldrte` | 1 | 214 | 3 | 0x0200 Transition |
| `voldrtn` | 1 | 216 | 3 | 0x0200 Transition |
| `voldrtne` | 1 | 210 | 3 | 0x0200 Transition |
| `voldrtnw` | 1 | 212 | 3 | 0x0200 Transition |
| `voldrts` | 1 | 217 | 3 | 0x0200 Transition |
| `voldrtse` | 1 | 211 | 3 | 0x0200 Transition |
| `voldrtsw` | 1 | 213 | 3 | 0x0200 Transition |
| `voldrtw` | 1 | 215 | 3 | 0x0200 Transition |
| `voldrtxne` | 1 | 218 | 3 | 0x0200 Transition |
| `voldrtxnw` | 1 | 220 | 3 | 0x0200 Transition |
| `voldrtxse` | 1 | 219 | 3 | 0x0200 Transition |
| `voldrtxsw` | 1 | 221 | 3 | 0x0200 Transition |

## MM7

Source: `assets_dev/engine/data_tables/terrain_tile_data_2.txt`

- Rows: 882
- Texture rows: 431
- Unique texture names: 108
- Pending placeholder rows: 78 (`0, 13-89`)
- Blank texture rows: 373 (`114-125, 150-161, 186-197, 222-233, 258-269, 294-305, 330-341, 366-377, 402-413, 437-449, 465-485, 501-521, 537-557, 573-593, 609-629, 645-665, 681-701, 717-737, 753-773, 789-809, 825-845, 861-881`)

### MM7 Tileset Summary

| Tileset | Count | Rows | Nonblank Textures | Flags |
|---:|---:|---|---:|---|
| 0 | 113 | 13-125 | 13 | 0x0000 None<br>0x0040 Unused/Pending<br>0x0200 Transition |
| 1 | 36 | 342-377 | 13 | 0x0000 None<br>0x0200 Transition |
| 2 | 36 | 234-269 | 13 | 0x0000 None<br>0x0200 Transition |
| 3 | 36 | 198-233 | 13 | 0x0000 None<br>0x0200 Transition |
| 4 | 12 | 1-12 | 3 | 0x0000 None |
| 5 | 36 | 126-161 | 13 | 0x0002 Water<br>0x0100 Shore<br>0x0300 Shore, Transition |
| 6 | 36 | 162-197 | 13 | 0x0000 None<br>0x0200 Transition |
| 7 | 36 | 270-305 | 15 | 0x0000 None<br>0x0200 Transition |
| 8 | 36 | 306-341 | 13 | 0x0000 None<br>0x0200 Transition |
| 9 | 36 | 378-413 | 13 | 0x0002 Water<br>0x0100 Shore<br>0x0300 Shore, Transition |
| 10 | 36 | 414-449 | 23 | 0x0000 None<br>0x0200 Transition |
| 11 | 36 | 450-485 | 1 | 0x0000 None<br>0x0200 Transition |
| 12 | 36 | 486-521 | 1 | 0x0000 None<br>0x0200 Transition |
| 13 | 36 | 522-557 | 1 | 0x0000 None<br>0x0200 Transition |
| 16 | 36 | 558-593 | 1 | 0x0000 None<br>0x0200 Transition |
| 17 | 36 | 594-629 | 1 | 0x0000 None<br>0x0200 Transition |
| 22 | 36 | 774-809 | 1 | 0x0000 None<br>0x0200 Transition |
| 23 | 36 | 810-845 | 1 | 0x0000 None<br>0x0200 Transition |
| 24 | 36 | 702-737 | 1 | 0x0000 None<br>0x0200 Transition |
| 25 | 36 | 738-773 | 1 | 0x0000 None<br>0x0200 Transition |
| 26 | 36 | 630-665 | 1 | 0x0000 None<br>0x0200 Transition |
| 27 | 36 | 666-701 | 1 | 0x0000 None<br>0x0200 Transition |
| 28 | 36 | 846-881 | 1 | 0x0000 None<br>0x0200 Transition |
| 255 | 1 | 0 | 0 | 0x0040 Unused/Pending |

### MM7 Unique Terrain Textures

| Texture | Count | Rows | Tilesets | Flags |
|---|---:|---|---|---|
| `7dirt1` | 1 | 2 | 4 | 0x0000 None |
| `7dirt2` | 1 | 4 | 4 | 0x0000 None |
| `7dirttyl` | 10 | 1, 3, 5-12 | 4 | 0x0000 None |
| `7drsrcros` | 1 | 414 | 10 | 0x0200 Transition |
| `7drsrcros1` | 1 | 429 | 10 | 0x0200 Transition |
| `7drsrcros2` | 1 | 430 | 10 | 0x0200 Transition |
| `7drsrcros3` | 1 | 431 | 10 | 0x0200 Transition |
| `7drsrcros4` | 1 | 432 | 10 | 0x0200 Transition |
| `7drsrecap` | 1 | 426 | 10 | 0x0200 Transition |
| `7drsrew` | 1 | 416 | 10 | 0x0200 Transition |
| `7drsrew_n` | 1 | 423 | 10 | 0x0200 Transition |
| `7drsrew_s` | 1 | 424 | 10 | 0x0200 Transition |
| `7drsrn_e` | 1 | 417 | 10 | 0x0200 Transition |
| `7drsrn_w` | 1 | 418 | 10 | 0x0200 Transition |
| `7drsrncap` | 1 | 425 | 10 | 0x0200 Transition |
| `7drsrne1` | 1 | 433 | 10 | 0x0200 Transition |
| `7drsrne2` | 1 | 434 | 10 | 0x0200 Transition |
| `7drsrns` | 1 | 415 | 10 | 0x0200 Transition |
| `7drsrns_e` | 1 | 421 | 10 | 0x0200 Transition |
| `7drsrns_w` | 1 | 422 | 10 | 0x0200 Transition |
| `7drsrnw1` | 1 | 435 | 10 | 0x0200 Transition |
| `7drsrnw2` | 1 | 436 | 10 | 0x0200 Transition |
| `7drsrs_e` | 1 | 419 | 10 | 0x0200 Transition |
| `7drsrs_w` | 1 | 420 | 10 | 0x0200 Transition |
| `7drsrscap` | 1 | 427 | 10 | 0x0200 Transition |
| `7drsrwcap` | 1 | 428 | 10 | 0x0200 Transition |
| `7grastyl` | 12 | 90-101 | 0 | 0x0000 None |
| `7grdrte` | 1 | 106 | 0 | 0x0200 Transition |
| `7grdrtn` | 1 | 108 | 0 | 0x0200 Transition |
| `7grdrtne` | 1 | 102 | 0 | 0x0200 Transition |
| `7grdrtnw` | 1 | 104 | 0 | 0x0200 Transition |
| `7grdrts` | 1 | 109 | 0 | 0x0200 Transition |
| `7grdrtse` | 1 | 103 | 0 | 0x0200 Transition |
| `7grdrtsw` | 1 | 105 | 0 | 0x0200 Transition |
| `7grdrtw` | 1 | 107 | 0 | 0x0200 Transition |
| `7grdrtxne` | 1 | 110 | 0 | 0x0200 Transition |
| `7grdrtxnw` | 1 | 112 | 0 | 0x0200 Transition |
| `7grdrtxse` | 1 | 111 | 0 | 0x0200 Transition |
| `7grdrtxsw` | 1 | 113 | 0 | 0x0200 Transition |
| `7hwtrdre` | 2 | 142, 394 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrn` | 2 | 144, 396 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrne` | 2 | 138, 390 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrnw` | 2 | 140, 392 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrs` | 2 | 145, 397 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrse` | 2 | 139, 391 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrsw` | 2 | 141, 393 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrw` | 2 | 143, 395 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrxne` | 2 | 146, 398 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrxnw` | 2 | 148, 400 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrxse` | 2 | 147, 399 | 5, 9 | 0x0300 Shore, Transition |
| `7hwtrdrxsw` | 2 | 149, 401 | 5, 9 | 0x0300 Shore, Transition |
| `7sand` | 24 | 162-173, 234-245 | 2, 6 | 0x0000 None |
| `7sddrte` | 2 | 178, 250 | 2, 6 | 0x0200 Transition |
| `7sddrtn` | 2 | 180, 252 | 2, 6 | 0x0200 Transition |
| `7sddrtne` | 2 | 174, 246 | 2, 6 | 0x0200 Transition |
| `7sddrtnw` | 2 | 176, 248 | 2, 6 | 0x0200 Transition |
| `7sddrts` | 2 | 181, 253 | 2, 6 | 0x0200 Transition |
| `7sddrtse` | 2 | 175, 247 | 2, 6 | 0x0200 Transition |
| `7sddrtsw` | 2 | 177, 249 | 2, 6 | 0x0200 Transition |
| `7sddrtw` | 2 | 179, 251 | 2, 6 | 0x0200 Transition |
| `7sddrtxne` | 2 | 182, 254 | 2, 6 | 0x0200 Transition |
| `7sddrtxnw` | 2 | 184, 256 | 2, 6 | 0x0200 Transition |
| `7sddrtxse` | 2 | 183, 255 | 2, 6 | 0x0200 Transition |
| `7sddrtxsw` | 2 | 185, 257 | 2, 6 | 0x0200 Transition |
| `7sndrte` | 2 | 214, 358 | 1, 3 | 0x0200 Transition |
| `7sndrtn` | 2 | 216, 360 | 1, 3 | 0x0200 Transition |
| `7sndrtne` | 2 | 210, 354 | 1, 3 | 0x0200 Transition |
| `7sndrtnw` | 2 | 212, 356 | 1, 3 | 0x0200 Transition |
| `7sndrts` | 2 | 217, 361 | 1, 3 | 0x0200 Transition |
| `7sndrtse` | 2 | 211, 355 | 1, 3 | 0x0200 Transition |
| `7sndrtsw` | 2 | 213, 357 | 1, 3 | 0x0200 Transition |
| `7sndrtw` | 2 | 215, 359 | 1, 3 | 0x0200 Transition |
| `7sndrtxne` | 2 | 218, 362 | 1, 3 | 0x0200 Transition |
| `7sndrtxnw` | 2 | 220, 364 | 1, 3 | 0x0200 Transition |
| `7sndrtxse` | 2 | 219, 363 | 1, 3 | 0x0200 Transition |
| `7sndrtxsw` | 2 | 221, 365 | 1, 3 | 0x0200 Transition |
| `7snow` | 24 | 198-209, 342-353 | 1, 3 | 0x0000 None |
| `7swdrte` | 1 | 286 | 7 | 0x0200 Transition |
| `7swdrtn` | 1 | 288 | 7 | 0x0200 Transition |
| `7swdrtne` | 1 | 282 | 7 | 0x0200 Transition |
| `7swdrtnw` | 1 | 284 | 7 | 0x0200 Transition |
| `7swdrts` | 1 | 289 | 7 | 0x0200 Transition |
| `7swdrtse` | 1 | 283 | 7 | 0x0200 Transition |
| `7swdrtsw` | 1 | 285 | 7 | 0x0200 Transition |
| `7swdrtw` | 1 | 287 | 7 | 0x0200 Transition |
| `7swdrtxne` | 1 | 290 | 7 | 0x0200 Transition |
| `7swdrtxnw` | 1 | 292 | 7 | 0x0200 Transition |
| `7swdrtxse` | 1 | 291 | 7 | 0x0200 Transition |
| `7swdrtxsw` | 1 | 293 | 7 | 0x0200 Transition |
| `7swtyl` | 10 | 270, 273-281 | 7 | 0x0000 None |
| `7swtylv1` | 1 | 271 | 7 | 0x0000 None |
| `7swtylv2` | 1 | 272 | 7 | 0x0000 None |
| `7wastetile` | 12 | 306-317 | 8 | 0x0000 None |
| `7wstdrte` | 1 | 322 | 8 | 0x0200 Transition |
| `7wstdrtn` | 1 | 324 | 8 | 0x0200 Transition |
| `7wstdrtne` | 1 | 318 | 8 | 0x0200 Transition |
| `7wstdrtnw` | 1 | 320 | 8 | 0x0200 Transition |
| `7wstdrts` | 1 | 325 | 8 | 0x0200 Transition |
| `7wstdrtse` | 1 | 319 | 8 | 0x0200 Transition |
| `7wstdrtsw` | 1 | 321 | 8 | 0x0200 Transition |
| `7wstdrtw` | 1 | 323 | 8 | 0x0200 Transition |
| `7wstdrtxne` | 1 | 326 | 8 | 0x0200 Transition |
| `7wstdrtxnw` | 1 | 328 | 8 | 0x0200 Transition |
| `7wstdrtxse` | 1 | 327 | 8 | 0x0200 Transition |
| `7wstdrtxsw` | 1 | 329 | 8 | 0x0200 Transition |
| `7wtrtyl` | 12 | 126-137 | 5 | 0x0002 Water |
| `dirttyl` | 180 | 450-464, 486-500, 522-536, 558-572, 594-608, 630-644, 666-680, 702-716, 738-752, 774-788, 810-824, 846-860 | 11-13, 16-17, 22-28 | 0x0200 Transition |
| `wtrtyl` | 12 | 378-389 | 9 | 0x0002 Water |

## MM8

Source: `assets_dev/engine/data_tables/terrain_tile_data.txt`

- Rows: 882
- Texture rows: 528
- Unique texture names: 272
- Pending placeholder rows: 78 (`0, 13-89`)
- Blank texture rows: 276 (`114-125, 150-161, 186-197, 222-233, 258-269, 294-305, 330-341, 366-377, 402-413, 437-449, 474-485, 510-521, 545-557, 582-593, 618-629, 654-665, 690-701, 726-737, 762-773, 797-809, 825-845, 870-881`)

### MM8 Tileset Summary

| Tileset | Count | Rows | Nonblank Textures | Flags |
|---:|---:|---|---:|---|
| 0 | 113 | 13-125 | 14 | 0x0000 None<br>0x0040 Unused/Pending<br>0x0200 Transition |
| 1 | 36 | 342-377 | 14 | 0x0000 None<br>0x0200 Transition |
| 2 | 36 | 234-269 | 1 | 0x0000 None<br>0x0200 Transition |
| 3 | 36 | 198-233 | 14 | 0x0000 None<br>0x0200 Transition |
| 4 | 12 | 1-12 | 3 | 0x0000 None |
| 5 | 36 | 126-161 | 13 | 0x0002 Water<br>0x0100 Shore<br>0x0300 Shore, Transition |
| 6 | 36 | 162-197 | 14 | 0x0000 None<br>0x0200 Transition |
| 7 | 36 | 270-305 | 12 | 0x0000 None<br>0x0200 Transition |
| 8 | 36 | 306-341 | 13 | 0x0000 None<br>0x0200 Transition |
| 9 | 36 | 378-413 | 13 | 0x0003 Burn, Water<br>0x0100 Shore<br>0x0300 Shore, Transition |
| 10 | 36 | 414-449 | 23 | 0x0000 None<br>0x0200 Transition |
| 11 | 36 | 450-485 | 1 | 0x0000 None<br>0x0200 Transition |
| 12 | 36 | 486-521 | 14 | 0x0000 None<br>0x0200 Transition |
| 13 | 36 | 522-557 | 23 | 0x0000 None<br>0x0200 Transition |
| 16 | 36 | 558-593 | 13 | 0x0000 None<br>0x0003 Burn, Water<br>0x0300 Shore, Transition |
| 17 | 36 | 594-629 | 14 | 0x0000 None<br>0x0200 Transition |
| 22 | 36 | 774-809 | 23 | 0x0000 None<br>0x0200 Transition |
| 23 | 36 | 810-845 | 1 | 0x0000 None<br>0x0200 Transition |
| 24 | 36 | 702-737 | 14 | 0x0000 None<br>0x0200 Transition |
| 25 | 48 | 666-701, 762-773 | 13 | 0x0000 None<br>0x0002 Water<br>0x0300 Shore, Transition |
| 26 | 36 | 630-665 | 1 | 0x0000 None<br>0x0200 Transition |
| 27 | 24 | 738-761 | 13 | 0x0002 Water<br>0x0300 Shore, Transition |
| 28 | 36 | 846-881 | 13 | 0x0000 None<br>0x0002 Water<br>0x0300 Shore, Transition |
| 255 | 1 | 0 | 0 | 0x0040 Unused/Pending |

### MM8 Unique Terrain Textures

| Texture | Count | Rows | Tilesets | Flags |
|---|---:|---|---|---|
| `dirt1` | 1 | 2 | 4 | 0x0000 None |
| `dirt2` | 1 | 4 | 4 | 0x0000 None |
| `dirttyl` | 49 | 1, 3, 5-12, 234-257, 810-824 | 2, 4, 23 | 0x0000 None<br>0x0200 Transition |
| `drsrcros` | 1 | 414 | 10 | 0x0200 Transition |
| `drsrcros1` | 1 | 429 | 10 | 0x0200 Transition |
| `drsrcros2` | 1 | 430 | 10 | 0x0200 Transition |
| `drsrcros3` | 1 | 431 | 10 | 0x0200 Transition |
| `drsrcros4` | 1 | 432 | 10 | 0x0200 Transition |
| `drsrecap` | 1 | 426 | 10 | 0x0200 Transition |
| `drsrew` | 1 | 416 | 10 | 0x0200 Transition |
| `drsrew_n` | 1 | 423 | 10 | 0x0200 Transition |
| `drsrew_s` | 1 | 424 | 10 | 0x0200 Transition |
| `drsrn_e` | 1 | 417 | 10 | 0x0200 Transition |
| `drsrn_w` | 1 | 418 | 10 | 0x0200 Transition |
| `drsrncap` | 1 | 425 | 10 | 0x0200 Transition |
| `drsrne1` | 1 | 433 | 10 | 0x0200 Transition |
| `drsrne2` | 1 | 434 | 10 | 0x0200 Transition |
| `drsrns` | 1 | 415 | 10 | 0x0200 Transition |
| `drsrns_e` | 1 | 421 | 10 | 0x0200 Transition |
| `drsrns_w` | 1 | 422 | 10 | 0x0200 Transition |
| `drsrnw1` | 1 | 435 | 10 | 0x0200 Transition |
| `drsrnw2` | 1 | 436 | 10 | 0x0200 Transition |
| `drsrs_e` | 1 | 419 | 10 | 0x0200 Transition |
| `drsrs_w` | 1 | 420 | 10 | 0x0200 Transition |
| `drsrscap` | 1 | 427 | 10 | 0x0200 Transition |
| `drsrwcap` | 1 | 428 | 10 | 0x0200 Transition |
| `gdrdcros` | 1 | 774 | 22 | 0x0200 Transition |
| `gdrdcros1` | 1 | 789 | 22 | 0x0200 Transition |
| `gdrdcros2` | 1 | 790 | 22 | 0x0200 Transition |
| `gdrdcros3` | 1 | 791 | 22 | 0x0200 Transition |
| `gdrdcros4` | 1 | 792 | 22 | 0x0200 Transition |
| `gdrdecap` | 1 | 786 | 22 | 0x0200 Transition |
| `gdrdew` | 1 | 776 | 22 | 0x0200 Transition |
| `gdrdew_n` | 1 | 783 | 22 | 0x0200 Transition |
| `gdrdew_s` | 1 | 784 | 22 | 0x0200 Transition |
| `gdrdn_e` | 1 | 777 | 22 | 0x0200 Transition |
| `gdrdn_w` | 1 | 778 | 22 | 0x0200 Transition |
| `gdrdncap` | 1 | 785 | 22 | 0x0200 Transition |
| `gdrdne1` | 1 | 793 | 22 | 0x0200 Transition |
| `gdrdne2` | 1 | 794 | 22 | 0x0200 Transition |
| `gdrdns` | 1 | 775 | 22 | 0x0200 Transition |
| `gdrdns_e` | 1 | 781 | 22 | 0x0200 Transition |
| `gdrdns_w` | 1 | 782 | 22 | 0x0200 Transition |
| `gdrdnw1` | 1 | 795 | 22 | 0x0200 Transition |
| `gdrdnw2` | 1 | 796 | 22 | 0x0200 Transition |
| `gdrds_e` | 1 | 779 | 22 | 0x0200 Transition |
| `gdrds_w` | 1 | 780 | 22 | 0x0200 Transition |
| `gdrdscap` | 1 | 787 | 22 | 0x0200 Transition |
| `gdrdwcap` | 1 | 788 | 22 | 0x0200 Transition |
| `gdtyl` | 24 | 630-653 | 26 | 0x0000 None<br>0x0200 Transition |
| `grastyl` | 11 | 90-91, 93-101 | 0 | 0x0000 None |
| `grastyl2` | 1 | 92 | 0 | 0x0000 None |
| `grdrte` | 1 | 106 | 0 | 0x0200 Transition |
| `grdrtn` | 1 | 108 | 0 | 0x0200 Transition |
| `grdrtne` | 1 | 102 | 0 | 0x0200 Transition |
| `grdrtnw` | 1 | 104 | 0 | 0x0200 Transition |
| `grdrts` | 1 | 109 | 0 | 0x0200 Transition |
| `grdrtse` | 1 | 103 | 0 | 0x0200 Transition |
| `grdrtsw` | 1 | 105 | 0 | 0x0200 Transition |
| `grdrtw` | 1 | 107 | 0 | 0x0200 Transition |
| `grdrtxne` | 1 | 110 | 0 | 0x0200 Transition |
| `grdrtxnw` | 1 | 112 | 0 | 0x0200 Transition |
| `grdrtxse` | 1 | 111 | 0 | 0x0200 Transition |
| `grdrtxsw` | 1 | 113 | 0 | 0x0200 Transition |
| `gse` | 1 | 718 | 24 | 0x0200 Transition |
| `gsn` | 1 | 720 | 24 | 0x0200 Transition |
| `gsne` | 1 | 714 | 24 | 0x0200 Transition |
| `gsnw` | 1 | 716 | 24 | 0x0200 Transition |
| `gss` | 1 | 721 | 24 | 0x0200 Transition |
| `gsse` | 1 | 715 | 24 | 0x0200 Transition |
| `gssw` | 1 | 717 | 24 | 0x0200 Transition |
| `gstyl` | 11 | 702, 704-713 | 24 | 0x0000 None |
| `gstylx` | 1 | 703 | 24 | 0x0000 None |
| `gsw` | 1 | 719 | 24 | 0x0200 Transition |
| `gsxne` | 1 | 722 | 24 | 0x0200 Transition |
| `gsxnw` | 1 | 724 | 24 | 0x0200 Transition |
| `gsxse` | 1 | 723 | 24 | 0x0200 Transition |
| `gsxsw` | 1 | 725 | 24 | 0x0200 Transition |
| `hwlvdre` | 1 | 862 | 28 | 0x0300 Shore, Transition |
| `hwlvdrn` | 1 | 864 | 28 | 0x0300 Shore, Transition |
| `hwlvdrne` | 1 | 858 | 28 | 0x0300 Shore, Transition |
| `hwlvdrnw` | 1 | 860 | 28 | 0x0300 Shore, Transition |
| `hwlvdrs` | 1 | 865 | 28 | 0x0300 Shore, Transition |
| `hwlvdrse` | 1 | 859 | 28 | 0x0300 Shore, Transition |
| `hwlvdrsw` | 1 | 861 | 28 | 0x0300 Shore, Transition |
| `hwlvdrw` | 1 | 863 | 28 | 0x0300 Shore, Transition |
| `hwlvdrxne` | 1 | 866 | 28 | 0x0300 Shore, Transition |
| `hwlvdrxnw` | 1 | 868 | 28 | 0x0300 Shore, Transition |
| `hwlvdrxse` | 1 | 867 | 28 | 0x0300 Shore, Transition |
| `hwlvdrxsw` | 1 | 869 | 28 | 0x0300 Shore, Transition |
| `lavtyl` | 24 | 378-389, 558-569 | 9, 16 | 0x0003 Burn, Water |
| `lvdre` | 1 | 394 | 9 | 0x0300 Shore, Transition |
| `lvdrn` | 1 | 396 | 9 | 0x0300 Shore, Transition |
| `lvdrne` | 1 | 390 | 9 | 0x0300 Shore, Transition |
| `lvdrnw` | 1 | 392 | 9 | 0x0300 Shore, Transition |
| `lvdrs` | 1 | 397 | 9 | 0x0300 Shore, Transition |
| `lvdrse` | 1 | 391 | 9 | 0x0300 Shore, Transition |
| `lvdrsw` | 1 | 393 | 9 | 0x0300 Shore, Transition |
| `lvdrw` | 1 | 395 | 9 | 0x0300 Shore, Transition |
| `lvdrxne` | 1 | 398 | 9 | 0x0300 Shore, Transition |
| `lvdrxnw` | 1 | 400 | 9 | 0x0300 Shore, Transition |
| `lvdrxse` | 1 | 399 | 9 | 0x0300 Shore, Transition |
| `lvdrxsw` | 1 | 401 | 9 | 0x0300 Shore, Transition |
| `lve` | 1 | 574 | 16 | 0x0300 Shore, Transition |
| `lvn` | 1 | 576 | 16 | 0x0300 Shore, Transition |
| `lvne` | 1 | 570 | 16 | 0x0300 Shore, Transition |
| `lvnw` | 1 | 572 | 16 | 0x0300 Shore, Transition |
| `lvs` | 1 | 577 | 16 | 0x0300 Shore, Transition |
| `lvse` | 1 | 571 | 16 | 0x0300 Shore, Transition |
| `lvsw` | 1 | 573 | 16 | 0x0300 Shore, Transition |
| `lvw` | 1 | 575 | 16 | 0x0300 Shore, Transition |
| `lvxne` | 1 | 578 | 16 | 0x0300 Shore, Transition |
| `lvxnw` | 1 | 580 | 16 | 0x0300 Shore, Transition |
| `lvxse` | 1 | 579 | 16 | 0x0300 Shore, Transition |
| `lvxsw` | 1 | 581 | 16 | 0x0300 Shore, Transition |
| `plntyl` | 24 | 450-473 | 11 | 0x0000 None<br>0x0200 Transition |
| `plrce` | 1 | 502 | 12 | 0x0200 Transition |
| `plrcn` | 1 | 504 | 12 | 0x0200 Transition |
| `plrcne` | 1 | 498 | 12 | 0x0200 Transition |
| `plrcnw` | 1 | 500 | 12 | 0x0200 Transition |
| `plrcs` | 1 | 505 | 12 | 0x0200 Transition |
| `plrcse` | 1 | 499 | 12 | 0x0200 Transition |
| `plrcsw` | 1 | 501 | 12 | 0x0200 Transition |
| `plrctyl` | 11 | 486-487, 489-497 | 12 | 0x0000 None |
| `plrctylx` | 1 | 488 | 12 | 0x0000 None |
| `plrcw` | 1 | 503 | 12 | 0x0200 Transition |
| `plrcxne` | 1 | 506 | 12 | 0x0200 Transition |
| `plrcxnw` | 1 | 508 | 12 | 0x0200 Transition |
| `plrcxse` | 1 | 507 | 12 | 0x0200 Transition |
| `plrcxsw` | 1 | 509 | 12 | 0x0200 Transition |
| `plrdcros` | 1 | 522 | 13 | 0x0200 Transition |
| `plrdcros1` | 1 | 537 | 13 | 0x0200 Transition |
| `plrdcros2` | 1 | 538 | 13 | 0x0200 Transition |
| `plrdcros3` | 1 | 539 | 13 | 0x0200 Transition |
| `plrdcros4` | 1 | 540 | 13 | 0x0200 Transition |
| `plrdecap` | 1 | 534 | 13 | 0x0200 Transition |
| `plrdew` | 1 | 524 | 13 | 0x0200 Transition |
| `plrdew_n` | 1 | 531 | 13 | 0x0200 Transition |
| `plrdew_s` | 1 | 532 | 13 | 0x0200 Transition |
| `plrdn_e` | 1 | 525 | 13 | 0x0200 Transition |
| `plrdn_w` | 1 | 526 | 13 | 0x0200 Transition |
| `plrdncap` | 1 | 535 | 13 | 0x0200 Transition |
| `plrdne1` | 1 | 541 | 13 | 0x0200 Transition |
| `plrdne2` | 1 | 542 | 13 | 0x0200 Transition |
| `plrdns` | 1 | 523 | 13 | 0x0200 Transition |
| `plrdns_e` | 1 | 529 | 13 | 0x0200 Transition |
| `plrdns_w` | 1 | 530 | 13 | 0x0200 Transition |
| `plrdnw1` | 1 | 543 | 13 | 0x0200 Transition |
| `plrdnw2` | 1 | 544 | 13 | 0x0200 Transition |
| `plrds_e` | 1 | 527 | 13 | 0x0200 Transition |
| `plrds_w` | 1 | 528 | 13 | 0x0200 Transition |
| `plrdscap` | 1 | 533 | 13 | 0x0200 Transition |
| `plrdwcap` | 1 | 536 | 13 | 0x0200 Transition |
| `plsae` | 1 | 610 | 17 | 0x0200 Transition |
| `plsan` | 1 | 612 | 17 | 0x0200 Transition |
| `plsane` | 1 | 606 | 17 | 0x0200 Transition |
| `plsanw` | 1 | 608 | 17 | 0x0200 Transition |
| `plsas` | 1 | 613 | 17 | 0x0200 Transition |
| `plsase` | 1 | 607 | 17 | 0x0200 Transition |
| `plsasw` | 1 | 609 | 17 | 0x0200 Transition |
| `plsatyl` | 11 | 594-595, 597-605 | 17 | 0x0000 None |
| `plsatylx` | 1 | 596 | 17 | 0x0000 None |
| `plsaw` | 1 | 611 | 17 | 0x0200 Transition |
| `plsaxne` | 1 | 614 | 17 | 0x0200 Transition |
| `plsaxnw` | 1 | 616 | 17 | 0x0200 Transition |
| `plsaxse` | 1 | 615 | 17 | 0x0200 Transition |
| `plsaxsw` | 1 | 617 | 17 | 0x0200 Transition |
| `rce` | 1 | 322 | 8 | 0x0200 Transition |
| `rcn` | 1 | 324 | 8 | 0x0200 Transition |
| `rcne` | 1 | 318 | 8 | 0x0200 Transition |
| `rcnw` | 1 | 320 | 8 | 0x0200 Transition |
| `rcs` | 1 | 325 | 8 | 0x0200 Transition |
| `rcse` | 1 | 319 | 8 | 0x0200 Transition |
| `rctyl` | 11 | 306-307, 309-317 | 8 | 0x0000 None |
| `rctylx` | 1 | 308 | 8 | 0x0000 None |
| `rcw` | 2 | 321, 323 | 8 | 0x0200 Transition |
| `rcxne` | 1 | 326 | 8 | 0x0200 Transition |
| `rcxnw` | 1 | 328 | 8 | 0x0200 Transition |
| `rcxse` | 1 | 327 | 8 | 0x0200 Transition |
| `rcxsw` | 1 | 329 | 8 | 0x0200 Transition |
| `rde` | 1 | 178 | 6 | 0x0200 Transition |
| `rdn` | 1 | 180 | 6 | 0x0200 Transition |
| `rdne` | 1 | 174 | 6 | 0x0200 Transition |
| `rdnw` | 1 | 176 | 6 | 0x0200 Transition |
| `rds` | 1 | 181 | 6 | 0x0200 Transition |
| `rdse` | 1 | 175 | 6 | 0x0200 Transition |
| `rdsw` | 1 | 177 | 6 | 0x0200 Transition |
| `rdtyl` | 11 | 162-163, 165-173 | 6 | 0x0000 None |
| `rdtylx` | 1 | 164 | 6 | 0x0000 None |
| `rdw` | 1 | 179 | 6 | 0x0200 Transition |
| `rdxne` | 1 | 182 | 6 | 0x0200 Transition |
| `rdxnw` | 1 | 184 | 6 | 0x0200 Transition |
| `rdxse` | 1 | 183 | 6 | 0x0200 Transition |
| `rdxsw` | 1 | 185 | 6 | 0x0200 Transition |
| `rke` | 1 | 358 | 1 | 0x0200 Transition |
| `rkn` | 1 | 360 | 1 | 0x0200 Transition |
| `rkne` | 1 | 354 | 1 | 0x0200 Transition |
| `rknw` | 1 | 356 | 1 | 0x0200 Transition |
| `rks` | 1 | 361 | 1 | 0x0200 Transition |
| `rkse` | 1 | 355 | 1 | 0x0200 Transition |
| `rksw` | 1 | 357 | 1 | 0x0200 Transition |
| `rktyl` | 11 | 342-343, 345-353 | 1 | 0x0000 None |
| `rktylx` | 1 | 344 | 1 | 0x0000 None |
| `rkw` | 1 | 359 | 1 | 0x0200 Transition |
| `rkxne` | 1 | 362 | 1 | 0x0200 Transition |
| `rkxnw` | 1 | 364 | 1 | 0x0200 Transition |
| `rkxse` | 1 | 363 | 1 | 0x0200 Transition |
| `rkxsw` | 1 | 365 | 1 | 0x0200 Transition |
| `swamptyl` | 12 | 270-281 | 7 | 0x0000 None |
| `swmpe` | 1 | 286 | 7 | 0x0200 Transition |
| `swmpn` | 1 | 288 | 7 | 0x0200 Transition |
| `swmpne` | 1 | 282 | 7 | 0x0200 Transition |
| `swmpnw` | 1 | 284 | 7 | 0x0200 Transition |
| `swmps` | 1 | 289 | 7 | 0x0200 Transition |
| `swmpse` | 1 | 283 | 7 | 0x0200 Transition |
| `swmpw` | 2 | 285, 287 | 7 | 0x0200 Transition |
| `swmpxne` | 1 | 290 | 7 | 0x0200 Transition |
| `swmpxnw` | 1 | 292 | 7 | 0x0200 Transition |
| `swmpxse` | 1 | 291 | 7 | 0x0200 Transition |
| `swmpxsw` | 1 | 293 | 7 | 0x0200 Transition |
| `tartyl` | 24 | 666-677, 846-857 | 25, 28 | 0x0002 Water |
| `tre` | 1 | 682 | 25 | 0x0300 Shore, Transition |
| `trn` | 1 | 684 | 25 | 0x0300 Shore, Transition |
| `trne` | 1 | 678 | 25 | 0x0300 Shore, Transition |
| `trnw` | 1 | 680 | 25 | 0x0300 Shore, Transition |
| `trs` | 1 | 685 | 25 | 0x0300 Shore, Transition |
| `trse` | 1 | 679 | 25 | 0x0300 Shore, Transition |
| `trsw` | 1 | 681 | 25 | 0x0300 Shore, Transition |
| `trw` | 1 | 683 | 25 | 0x0300 Shore, Transition |
| `trxne` | 1 | 686 | 25 | 0x0300 Shore, Transition |
| `trxnw` | 1 | 688 | 25 | 0x0300 Shore, Transition |
| `trxse` | 1 | 687 | 25 | 0x0300 Shore, Transition |
| `trxsw` | 1 | 689 | 25 | 0x0300 Shore, Transition |
| `vole` | 1 | 214 | 3 | 0x0200 Transition |
| `voln` | 1 | 216 | 3 | 0x0200 Transition |
| `volne` | 1 | 210 | 3 | 0x0200 Transition |
| `volnw` | 1 | 212 | 3 | 0x0200 Transition |
| `vols` | 1 | 217 | 3 | 0x0200 Transition |
| `volse` | 1 | 211 | 3 | 0x0200 Transition |
| `volsw` | 1 | 213 | 3 | 0x0200 Transition |
| `voltyl` | 11 | 198, 200-209 | 3 | 0x0000 None |
| `voltylx` | 1 | 199 | 3 | 0x0000 None |
| `volw` | 1 | 215 | 3 | 0x0200 Transition |
| `volxne` | 1 | 218 | 3 | 0x0200 Transition |
| `volxnw` | 1 | 220 | 3 | 0x0200 Transition |
| `volxse` | 1 | 219 | 3 | 0x0200 Transition |
| `volxsw` | 1 | 221 | 3 | 0x0200 Transition |
| `wae` | 1 | 754 | 27 | 0x0300 Shore, Transition |
| `wan` | 1 | 756 | 27 | 0x0300 Shore, Transition |
| `wane` | 1 | 750 | 27 | 0x0300 Shore, Transition |
| `wanw` | 1 | 752 | 27 | 0x0300 Shore, Transition |
| `was` | 1 | 757 | 27 | 0x0300 Shore, Transition |
| `wase` | 1 | 751 | 27 | 0x0300 Shore, Transition |
| `wasw` | 1 | 753 | 27 | 0x0300 Shore, Transition |
| `waw` | 1 | 755 | 27 | 0x0300 Shore, Transition |
| `waxne` | 1 | 758 | 27 | 0x0300 Shore, Transition |
| `waxnw` | 1 | 760 | 27 | 0x0300 Shore, Transition |
| `waxse` | 1 | 759 | 27 | 0x0300 Shore, Transition |
| `waxsw` | 1 | 761 | 27 | 0x0300 Shore, Transition |
| `wtrdre` | 1 | 142 | 5 | 0x0300 Shore, Transition |
| `wtrdrn` | 1 | 144 | 5 | 0x0300 Shore, Transition |
| `wtrdrne` | 1 | 138 | 5 | 0x0300 Shore, Transition |
| `wtrdrnw` | 1 | 140 | 5 | 0x0300 Shore, Transition |
| `wtrdrs` | 1 | 145 | 5 | 0x0300 Shore, Transition |
| `wtrdrse` | 1 | 139 | 5 | 0x0300 Shore, Transition |
| `wtrdrsw` | 1 | 141 | 5 | 0x0300 Shore, Transition |
| `wtrdrw` | 1 | 143 | 5 | 0x0300 Shore, Transition |
| `wtrdrxne` | 1 | 146 | 5 | 0x0300 Shore, Transition |
| `wtrdrxnw` | 1 | 148 | 5 | 0x0300 Shore, Transition |
| `wtrdrxse` | 1 | 147 | 5 | 0x0300 Shore, Transition |
| `wtrdrxsw` | 1 | 149 | 5 | 0x0300 Shore, Transition |
| `wtrtyl` | 24 | 126-137, 738-749 | 5, 27 | 0x0002 Water |
