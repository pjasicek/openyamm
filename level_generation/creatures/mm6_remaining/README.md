# MM6 remaining creature restoration

Resumable ledger: [progress.json](progress.json). Status is per family, not per generated sheet.
Current blockers and exact resume steps: [HANDOFF.md](HANDOFF.md).
All MM6 families installed in assets_dev; original BMPs preserved; see installation.json. Reuse all validated MM6 packages.

| ID | Family | Status | Stage |
| --- | --- | --- | --- |
| 475 | BArcher A | insufficient | below 2x generated detail; redo inventory prepared |
| 478 | Barbarian A | insufficient | below 2x generated detail; redo inventory prepared |
| 481 | BBat A | insufficient | below 2x generated detail; redo inventory prepared |
| 484 | BBeholder A | insufficient | below 2x generated detail; redo inventory prepared |
| 487 | Bloodsucker A | insufficient | below 2x generated detail; redo inventory prepared |
| 490 | Cleric A | insufficient | below 2x generated detail; redo inventory prepared |
| 493 | Cobra A | insufficient | below 2x generated detail; redo inventory prepared |
| 496 | Cockatrice A | insufficient | below 2x generated detail; redo inventory prepared |
| 499 | DemonFly A | insufficient | below 2x generated detail; redo inventory prepared |
| 502 | Demon A | insufficient | below 2x generated detail; redo inventory prepared |
| 505 | DragonCave A | insufficient | below 2x generated detail; redo inventory prepared |
| 508 | BDragonFly A | insufficient | below 2x generated detail; redo inventory prepared |
| 511 | DragonLand A | insufficient | below 2x generated detail; redo inventory prepared |
| 514 | DragonCover A | insufficient | below 2x generated detail; redo inventory prepared |
| 517 | Druidess A | insufficient | below 2x generated detail; redo inventory prepared |
| 520 | BDwarf A | insufficient | below 2x generated detail; redo inventory prepared |
| 523 | ElemAir A | insufficient | below 2x generated detail; redo inventory prepared |
| 526 | ElemEarth A | insufficient | below 2x generated detail; redo inventory prepared |
| 529 | ElemFire A | insufficient | below 2x generated detail; redo inventory prepared |
| 532 | ElemWater A | insufficient | below 2x generated detail; redo inventory prepared |
| 535 | FighterChain A | insufficient | below 2x generated detail; redo inventory prepared |
| 538 | FighterLeath A | insufficient | below 2x generated detail; redo inventory prepared |
| 541 | BGargoyle A | insufficient | below 2x generated detail; redo inventory prepared |
| 544 | BGenie A | insufficient | below 2x generated detail; redo inventory prepared |
| 547 | BGhost A | insufficient | below 2x generated detail; redo inventory prepared |
| 550 | BGoblin A | insufficient | below 2x generated detail; redo inventory prepared |
| 553 | Guard A | insufficient | below 2x generated detail; redo inventory prepared |
| 556 | BHarpy A | insufficient | below 2x generated detail; redo inventory prepared |
| 559 | BHydra A | insufficient | below 2x generated detail; redo inventory prepared |
| 562 | Jackalman A | insufficient | below 2x generated detail; redo inventory prepared |
| 565 | KnightPlate A | insufficient | below 2x generated detail; redo inventory prepared |
| 568 | BLich A | insufficient | below 2x generated detail; redo inventory prepared |
| 571 | LizardArch A | insufficient | below 2x generated detail; redo inventory prepared |
| 574 | BMedusa A | insufficient | below 2x generated detail; redo inventory prepared |
| 577 | Merchant A | validated | reused accepted package; coverage and recorded validation checked |
| 580 | BMinotaur A | insufficient | below 2x generated detail; redo inventory prepared |
| 583 | BMonk A | validated | reused accepted package; coverage and recorded validation checked |
| 586 | Nobleman A | insufficient | below 2x generated detail; redo inventory prepared |
| 589 | BOoze A | insufficient | below 2x generated detail; redo inventory prepared |
| 592 | Ogre A | insufficient | below 2x generated detail; redo inventory prepared |
| 595 | PeasantF1 A | insufficient | below 2x generated detail; redo inventory prepared |
| 598 | PeasantF2 A | insufficient | below 2x generated detail; redo inventory prepared |
| 601 | PeasantF3 A | insufficient | below 2x generated detail; redo inventory prepared |
| 604 | PeasantF4 A | insufficient | below 2x generated detail; redo inventory prepared |
| 607 | PeasantM1 A | insufficient | below 2x generated detail; redo inventory prepared |
| 610 | PeasantM2 A | insufficient | below 2x generated detail; redo inventory prepared |
| 613 | PeasantM3 A | insufficient | below 2x generated detail; redo inventory prepared |
| 616 | PeasantM4 A | insufficient | below 2x generated detail; redo inventory prepared |
| 619 | BRat A | validated | reused accepted package; coverage and recorded validation checked |
| 622 | BRobot A | insufficient | below 2x generated detail; redo inventory prepared |
| 625 | SeaSerpent A | insufficient | below 2x generated detail; redo inventory prepared |
| 628 | Skeleton A | insufficient | below 2x generated detail; redo inventory prepared |
| 631 | Sorcerer A | insufficient | below 2x generated detail; redo inventory prepared |
| 634 | BSpider A | validated | reused accepted package; coverage and recorded validation checked |
| 637 | BThief A | insufficient | below 2x generated detail; redo inventory prepared |
| 640 | BTitan A | insufficient | below 2x generated detail; redo inventory prepared |
| 643 | Werewolf A | insufficient | below 2x generated detail; redo inventory prepared |
| 646 | zDemonQueen | insufficient | below 2x generated detail; redo inventory prepared |
| 647 | zReactor | insufficient | below 2x generated detail; redo inventory prepared |
| 649 | Cactus A | insufficient | below 2x generated detail; redo inventory prepared |

Regenerate the native inventory with `python3 level_generation/creatures/inventory_remaining.py`,
then refresh this ledger with `python3 level_generation/creatures/mm6_remaining/prepare.py ledger`.
Only mark new work validated after complete native coverage, variant/animation and visual edge checks.
Preserve raw generations and exact prompts; resume from selected successful sheets.
