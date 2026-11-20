# Six source water contacts

Status: all six wells have native geometry and local visual review; representative click/reload review is complete.

The original sprite 54 visibly depicts a roofed stone well with a windlass. The historical `spring` kind in the
layout describes the interaction category; it does not require a natural pond. `prepare_source_wells.py` retains
all six original centers, object identities and future water effects.

| Source cell | Proposed label | Future effect retained |
| --- | --- | --- |
| 3 (2,10) | Western shelf well | +50 spell points |
| 3 (3,3) | Western meadow well | +50 hit points |
| 3 (11,1) | Royal quarter well | Original refreshing-water contact |
| 4 (3,10) | Southwestern well | +10 armor class |
| 4 (9,11) | Might well | +25 Might |
| 8 (2,2) | Fortune well | +100 Luck |

All effects remain deferred. Labels distinguish placeholder contacts without replacing original behavior notes.
The royal-quarter well faces east to retain a usable standing space beside the household. The five countryside
wells face south. Their final environmental settings need deliberate regional composition, without automatic roads
to each reward site. Existing planting near the royal well was refitted to keep its full approach clear.

`author_source_wells.py` creates a 256-unit stone ring, wider rim, supported timber posts, pitched roof with thickness,
windlass/crank, hanging rope and open bucket. Existing `t18b01`, `t05a10`, `t05a05`, `gn_mtl03` and `wtrtyl` provide
the material palette. The water plane stays above the unmodified terrain; no native terrain hole is fabricated.

`render_source_well_study.py` reuses the actual authoring class in a separate owned scene and review output folder.
The [V2 template views](../review/source_well_study_v2/views.json) follow a camera correction to show the whole roof.
The [placement review](../review/source_well_placements_v1/source_review.json) and
[contact sheet](../review/source_well_placements_v1/contact_sheet.jpg) cover all six fits on the actual heightfield.
All 267 active map OBJ hashes remained unchanged during the study. Neutral study ground does not certify native
texture context, scenery, interaction or final region composition.

The [integrated source review](../review/source_wells_v1/source_review.json) retains all 267 prior OBJ hashes and adds
six new models. Four royal-quarter planting records move, with their original identities retained. The first refit
left low plants between the standing point and the well; an explicit full approach corridor corrects that reserve.
The final source refit preserves 698 scenery records and all 55 orchard identities, with fourteen total prior/current
moves and no unresolved placements. Neither geometry nor terrain changed during the approach-reserve correction.

`review_source_wells.py` checks written materials/bindings, buried ring/post feet, the water plane's ground clearance,
upward roof faces and sprite approaches during native build. Its log is `review/source_wells_v1/native_build.log`.
The [native review](../review/source_wells_v1/native_review.json) records all six inspected game views and the royal
well's successful named placeholder click and save/reload. Exposed save fields retain health, gold, food and inventory;
this is not a full stat/QBit comparison. Native water clearance is positive and all six roofs and supports pass readback.
The western shelf view crops the lowest foot at the HUD; source/readback provide its support evidence. Black void rim
and sparse countryside foreground remain explicit landscape defects, not accepted well surroundings.
No global NPC/house/quest rows are needed.
