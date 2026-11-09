# Town exterior detail completion inventory

Status: **exterior environment accepted**. Local reviews and repeated whole-town game views are consolidated in
[the final context review](../review/town_context_v1/final_context_review.json).
This supplements the premises/venue inventory; an authored building shell does not complete its working court.
Furniture intended inside deferred BLVs or dialogue interiors is kept as planning data, not moved into the street.

| Premises | Existing exterior treatment | Exterior acceptance evidence | Deferred interior or gameplay detail |
| --- | --- | --- | --- |
| Guild | Lower main hall, membership wing and public notice | Notice and open forecourt locally reviewed; included in final town overviews | Membership desk, resident dialogue; Nool's public contact remains unpopulated |
| Forge | Flue, open stock bay, anvil, ore bin, two stock groups | Working yard/passage locally reviewed in town_context_v1; included in final town overviews | Functional smith service |
| Training | Institutional hall, hood, basin, bench and two inert targets | Targets, ordinary gap passage, retreat/reload and pool/step locally reviewed; included in final town overviews | Training/Swimming services |
| Jail | Fortified piers and barred entrance | Street/parapet and skyline locally reviewed in town_context_v1 | Cells, bed and Jasper; no outdoor bed |
| Northern chapterhouse | Low shared hall | Northern doorway/street locally reviewed; retain the existing shared meditation garden and accepted final town context | Two study stations/books and residents |
| Southern chapterhouse | Smaller shared hall; new source-owned bench and unequal masonry bed edges; 12 composed plant anchors | Local native planting, fitted props, ordinary approach, click and reload reviewed; included in final town overviews | Two study stations and residents |
| Bank | Shared roof and two separate venue doors | Fountain/bench/bank and adjacent street locally reviewed from east and south in town_working_details_v4 | Ledger/accounts desks and services |
| Tavern | Unequal guest/entrance halls, stock and bench | Unequal joined halls, stock, bench and clear passage locally reviewed in town_context_v1 | Common-room tables and Tanya/Gloria seats |
| Lodging | Modest long hall | Installed lodging click/reload and western town overview establish frontage, garden/barrel and neighboring court context | Two rented rooms |
| Mapmakers | Joined three-venue workshop, stock and three named chart plaques | Named frontage and full joined hall/side-street context locally reviewed in town_context_v1 | Interior desks/racks; three distinct contacts |
| Mayor | Office/editorial wing and civic notice; nearby public bench outside southern curtain | Frontage and exterior roadside bench locally reviewed in town_context_v1 | Editorial desk and NPCs |
| Hiring office | Compact hall/canopy, stock and hiring notice | Notice/access and native repair setting locally reviewed; included in final town overviews | Jojosh's dialogue |
| Joe | Timber stall, displayed merchandise, new absence notice | Local native sign/street, real click and reload reviewed; included in final town overviews | Fraud, trade and absence schedule |
| Ranger | Compact lodge; woodcraft table, axe/block/stock and five native garden plants | Local native detail, planted context, ordinary approach, named click and reload reviewed; included in final town overviews | Teaching/dialogue |
| Herbalist | Cottage, lower shed and drying rack; planted garden | Planted rack/passage context locally reviewed in town_context_v1; included in final town overviews | Resident and services |
| Nadia | Worn cottage | Native storage and ordinary curtain-side passage/retreat/reload locally reviewed | Personal inventory/rewards |
| Diviners | Shared study house | Oorla steps, shared approach and back-court well/bench/barrel locally reviewed in town_context_v1 | Orb discussion table and two speakers |
| Gremlin court | Fortified audience annex | Wider normal forecourt/road, northern orchard and civilian neighbor reviewed in town_context_v1; guard staging stays empty | Throne, guard actors and reward |
| Ellinger | Distinct tall polygonal tower and entrance | Complete shaft/roof hierarchy above fountain court locally reviewed; entrance has earlier native click evidence | Wizard, key/boots clues and interior |
| Temple | Nave/apse, MOK identity and two source benches | South approach and rear waiting/rest benches locally reviewed in town_context_v1; temple skyline included in final town views | Healing service and Imble |
| Tailor/cobbler | Shared roof, unequal hoods, distinct doors, bench and two suspended trade signs | Signs and representative cobbler access/click/reload locally reviewed; stock and whole-town context reviewed | Interior tools/services |
| Workers | Modest shared house and source bench | Grounded leaning tools and rear-wall/passage context locally reviewed | Shared beds and residents |
| Keeper | Cottage, kennel and bench | Native workbench, cottage-side yard and separate kennel/stock context locally reviewed | Residents and dog-catching logic |
| Storehouse | Broad low hall, roof gutter treatment and stock | Broad low entrance hall and two higher puzzle-bay roofs locally reviewed in town_context_v1 | Two nine-chest puzzle bays, moving treasure and Dyson's desk |

## Historical native court observations (288-model checkpoint)

The 288-model camp-corrected checkpoint was inspected from actual game viewpoints:

- [Fountain court](../review/gameplay/mm5_fountain_court_context_v2.png): basin, planting and nearby architecture read
  clearly. Its surrounding circulation and seating still need the complete court pass; the fountain alone is not that pass.
- [Chapterhouse doorway](../review/gameplay/mm5_meditation_court_context_v1.png) was too close to show the garden.
  [The repeated road approach](../review/gameplay/mm5_meditation_court_context_v2.png) shows the actual 12-plant group,
  road fork, chapterhouse and training hall together. Plants stand as a loose patch on undifferentiated dirt.

The historical meditation reservation at (-1,904,-1,008), extent 1,152×700, overlaps the snapped road fork. Current
garden anchors occupy the northern side, approximately X=-2,504…-1,608 and Y=-800…-440. The subsequent southern court revision below finishes that usable side with
one fitted bench and unequal masonry edges. Keep a direct southern approach
to the chapterhouse at (-2,154,154), and retain both fork branches. Do not fence or furnish the historical rectangle
without testing it against the native road layout. Four future lesson stations remain inside their two shared venues;
they do not require four exterior benches or four new doors.

Reference use follows [outdoor decoration calibration](../../../OUTDOOR_DECORATION_CALIBRATION.md): settlement planting
and working props express use, while the open street and court remain useful space. Additional furniture needs explicit
ownership, actual native grounding and a repeated player-height view. This inventory is not permission to scatter every
interior prop outdoors or to populate NPCs.

## Southern court revision

`author_chapter_court.py` now owns one plain timber bench west of the doorway and partial masonry edging for two
unequal planted pockets. Five plants occupy the western pocket and seven the eastern pocket, retaining all twelve
existing decoration identities and their original native artwork. `prepare_scenery.py` checks these explicit anchors
against actual solids and roads; it cannot silently move a rejected court plant elsewhere.

The unfurnished approach is X=-2,300…-2,050, Y=-1,120…154. The bench faces south into the shared court. Its feet
and each stone course extend sixteen units below native terrain; the nearest edging is 104 units from a snapped road
centerline. Existing terrain, door, road, water and lesson-station ownership remains intact.

The initial source renders used green fortress stone, which looked out of place. Repeated
[oblique](../review/chapter_court_v1/blender_revised/court_oblique.png) and
[approach](../review/chapter_court_v1/blender_revised/court_approach.png) renders use the chapterhouse's brown masonry.
These Blender views omit native plant billboards. The subsequent 310-model native build now has inspected planted
context, ordinary approach, named click and return/reload evidence. See
[native review](../review/chapter_court_v1/native_review.json) and [current checkpoint](../review/chapter_court_v1/checkpoint.json).
