# Castleview's five ground grilles

Status: all five native grilles and local context views reviewed. West Gate's corrected V2 casing passes ordinary
walking in both directions, with real click and reload evidence. Its failed V1 walking test remains historical evidence.
These five features are additional to the 45 premises. The riverside outfall is a separate completed local site.

Each original Castleview contact uses Darkside object sprite 22: a low metal ground grille. The new geometry uses
a 256×192 stone casing, six bars, two crossbars, two hinges and an opaque recessed backing. It uses existing
`t18b01`, `gn_mtl03` and `solid01` artwork at native texel scale. No donor mesh or terrain hole is introduced.

| Original town cell | Contact | Local event | Current center | Future return side |
| --- | --- | --- | --- | --- |
| 29 (1,13) | East Court sewer | 3021 | 1546, 842 | North |
| 29 (2,29) | Guild Quarter sewer | 3022 | 446, −4458 | North |
| 29 (12,30) | South Wall sewer | 3026 | −1568, −4762 | North |
| 29 (26,1) | Northwest sewer | 3029 | −6604, 4942 | North |
| 29 (30,18) | West Gate sewer | 3030 | −8204, 742 | East |

The South Wall casing moves 64 units west and 96 north to clear a curtain corner. All other centers retain their
planned points. The West Gate return faces east because north/south arrivals approach the gate towers too closely.
Original coordinates, objects and distinct map-30 routes remain in each `sourceFeature`/`originalObject` record.
Returns are inactive, 320 units from the contact on real terrain; this milestone does not create the sewer BLV.

`prepare_town_sewers.py` fits four level backings at least four units above the highest footprint ground and buries the
casing below the lowest edge sample. West Gate follows its exact planar road slope (local X 3/16), retaining a backing
4.875 units above ground. Its outer stone lip is approximately 0.875 units above ground and bevels toward the inner rim;
the original flat casing presented a much larger obstacle downhill. Fit checks use the actual native triangle split, building/detail footprints,
curtain, other props and door approach reserves. `author_town_sewers.py` creates one independently authored BModel
per contact and binds its faces to its named status-only handler. The map-local numbers live in
`feature_event_ids.json`; they allocate no global NPC, house or quest rows.

The [source review](../review/town_sewers_v1/source_review.json) records ten inspected renders and unchanged prior
OBJ hashes. The [contact sheet](../review/town_sewers_v1/contact_sheet.jpg) shows all five local ground fits.
`review_town_sewers.py` checks actual native faces, backing/casing contact, sprite access and distinct handlers after
export. The [V1 native review](../review/town_sewers_v1/native_review.json) records the successful click/reload and
failed walking test: the image named `crossed` does not prove a crossing. The
[V2 source review](../review/town_sewers_v2/source_review.json) records the corrected casing and retained coordinates.
Only the West Gate prior OBJ changes. The [V2 native review](../review/town_sewers_v2/native_review.json) records
successful ordinary forward crossings from opposite sides, named status feedback and reload. The equal-duration
backward leg was shorter and is not the evidence used for the reverse crossing. Inspected save values remain unchanged.
The four other grate meshes are unchanged. This local acceptance does not approve the unfinished regional scenery.
