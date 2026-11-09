# MM5 world recreation in OpenYAMM: feasibility and proposed arrangement

**Assessment: feasible, with a credible existing geometry pipeline. Start from six surface regions formed from 2×2
groups of MM5 outdoor squares. Preserve the story, named places, route relationships and access conditions; author
new MM6–MM8-scale geometry around them.** A uniform enlargement of MM5 cells would produce the wrong town scale and
would break several dungeon and quest relationships.

This is a feasibility study, not an approved production layout or a runtime implementation. No game maps, world
registrations, quests or gameplay code were changed. The baseline is **Darkside of Xeen only**. The 17 World of Xeen
bonus logical maps in DARK.CC are inventoried but excluded. MM4 has not been surveyed here.

Open the **[interactive world atlas](atlas.html)**. The complete [logical map list](MAP_INVENTORY.md),
[interaction-site CSV](sites.csv), [travel CSV](travel.csv), [regional seam CSV](region_boundaries.csv) and
[machine-readable inventory](inventory.json) make the proposal inspectable.

The subsequent **[surface world layout](world_layout/README.md)** adds a
[joined terrain overview and foot-travel diagram](world_layout/index.html), equal-size region crops, native material
references and the SW first-map recommendation. It finds terrain-supported examples for all seven regional links:
four roads and three proposed off-road approaches. That follow-up refines the terrain uncertainty below; dynamic
access rules and native map generation remain future work.

## 1. What the original world actually contains

| Source layer | Logical maps | Arrangement |
| --- | ---: | --- |
| Surface | 24 | Six columns A–F, four rows 1–4; each square is 16×16 cells |
| Skyroads | 24 | A separate 6×4 layer, spatially related to the surface |
| Elemental planes | 4 | Fire, Air, Earth and Water; each a separate map |
| Towns | 5 | Castleview, Sandcaster, Lakeside, Necropolis and Olympus |
| Other interiors | 55 | Sewers, castle/tower floors, dungeons, mines, holes and two escape pods |
| **MM5 baseline** | **112** | **147 stored 16×16 DAT blocks** |
| Excluded WoX bonus | 17 | 36 further stored blocks; not part of this baseline |

The complete DARK initial archive has **183 blocks but 129 logical maps**. Its **54 extra blocks are continuation
quadrants**, not unused maps. The first extraction gallery called these unnamed/template maps; that label was wrong.
The study reconstructs ownership and positions from the cardinal neighbor fields. Every block has exactly one owner.
For example, Castleview is **32×32**, assembled from 29, 130, 131 and 132. Sandcaster is 31, 136, 137 and 138.
The escape pods are **32×16**. The full [chunk ownership table](chunks.csv) records every assembly.

Source direction decoding was also checked against the runtime's actual WALL_SHIFTS table: indoor north/east/south/west
occupy bits 12/8/4/0. The extractor and its derived JSON/previews were corrected; original resource bytes are unchanged.
This is a shared format correction, not an MM4 content survey.

Named world anchors come directly from `darkmirr.txt`, map titles and event coordinates. This avoids relying on occasional
map-coordinate mistakes in printed prose. For example, the supplied game places Castleview's gate in **A4**, not A3.

## 2. Recommended surface map list

The following names are **proposed region labels**, assembled from original landmarks. The square assignments are exact.
The original world remains geographically recognizable:

| North → south / west → east | A–B | C–D | E–F |
| --- | --- | --- | --- |
| Rows 1–2 | **NW: Alamar and Necropolis** | **NC: Desert of Doom and Northern Highlands** | **NE: Blackfang and Lakeside** |
| Rows 3–4 | **SW: Castleview and Kalindra** | **SC: Sprite Forest and Southern Tower** | **SE: Sandcaster and Eastern Forest** |

| Proposed ODM | Original squares / IDs | Settlement and landmark anchors | Interior and quest relationships |
| --- | --- | --- | --- |
| **SW — Castleview and Kalindra** | A3, A4, B3, B4 / 3, 4, 7, 8 | Castleview gate A4(14,10); Castle Kalindra A4(5,14); Western Tower A3(4,9); Dark Grove A3; Acid Pond B3; four gemsmiths split across A3/B3; Yog, Dreyfus, Kramer, Vespar, Luna, Justine and Nibbler | Castleview + sewer + Ellinger's Tower; Kalindra's phased restoration; Western Tower; mine and troll-hole entrances; direct Dark Grove sky access; the starter quest network and repeated return hub |
| **SC — Sprite Forest and Southern Tower** | C3, C4, D3, D4 / 11, 12, 15, 16 | Gemstone Range C3; Sharla and Temple of Bark C4(2,8); Ogre Pass/Graalg D3; Southern Tower D4(2,7); forest fruit sites | Temple rescue → Energy Disks; ogre negotiation; multiple mine/shaft entrances; Southern Tower and its sky exit; mostly wilderness rather than a new invented town |
| **SE — Sandcaster and Eastern Forest** | E3, E4, F3, F4 / 19, 20, 23, 24 | Sandcaster gate E3(4,12); Crossroads E3 with six merchants; Aging Forest and Cornelius E4; Eastern Tower F3(10,9); Venom Pond, Thaddeus and Celia/Derek F4 | Sandcaster's sewer and hostile wizard quarter; Vespar's staff/pass quest; Natasha's bridle enchantment; Eastern Tower/Jewel of Ages; southern forest exploration |
| **NC — Desert of Doom and Northern Highlands** | C1, C2, D1, D2 / 9, 10, 13, 14 | Quivering Forest C1; Desert of Doom C2; Northern Tower D1(2,10); Bosco and Gurodel D1; Parabolic Barrier D1; Great Pyramid D2(0,5); Perishing Sands D2 | Great Pyramid/Dragon Pharaoh; Northern Tower; giant negotiation and Energy Disks; a remote Sandcaster sewer exit at D2(12,2); desert and mountain traversal |
| **NE — Blackfang and Lakeside** | E1, E2, F1, F2 / 17, 18, 21, 22 | Magic Mountain and two wizards E1; Ector/Forest of Peril E2; Castle Blackfang F1(9,11); Snow River Rapids F1; Lakeside gate F2(3,15); Octopod Lake and Isle of Lost Souls F2 | Ambrose's gated Blackfang entry and the Queen rescue; Lakeside + sewer; Lost Souls entrance F2(6,10); Songbird of Serenity; water/island travel |
| **NW — Alamar and Necropolis** | A1, A2, B1, B2 / 1, 2, 5, 6 | Castle Alamar A1(10,4); Griffin Pass/Ambrose B1; Necropolis gate B2(8,12); Forbidden Zone B2; escape pod entrances B1(2,9) and B2(3,8); A2/B2 mines | Final Alamar/Sheltem route; Corak's escape pod; Necropolis + sewer; the griffin/bridle quest begins here well before the final assault; lava/mountain danger |

Each region has four original outdoor squares, but their design loads differ. From the static event survey, the six
surface groups contain respectively **60, 29, 61, 29, 56 and 37 event-bearing outdoor cells** in the table's order.
These include signs, effects and conditional interactions; they are **not** counts of houses, quests or encounters.
They exclude the separate town/interior maps. The atlas lists the underlying coordinates instead of treating these
totals as production quotas.

Six is a strong first baseline, not a rigid requirement. It preserves the 3×2 regional arrangement and supports
substantial regions without stretching every original screen into an empty landscape. A later split to seven or eight
surface ODMs is reasonable if the Castleview/Kalindra layout cannot retain good pacing and clear approaches at native
building scale. A 24-ODM surface is technically possible but would require much more invented countryside or frequent
short-map transitions. Combining all 24 squares into one ODM would severely compress distinct landscapes and progression.

## 3. Do the towns contain enough houses and services?

**Yes for the main hubs; the towns deliberately have different roles.** The source does not provide an MM6-style
physical-house registry. The most useful initial comparison is distinct interaction sites, followed by an authored
building/entrance census. Counts below exclude out-of-map helper-script coordinates.

| Town | Complete source dimensions | Named NPC interaction coordinates | Standard service entrances | Unique NPC-or-service coordinates | Intended recreation |
| --- | --- | ---: | ---: | ---: | --- |
| Castleview | 32×32 | 35 | 6 | 41 | Substantial inhabited hub inside SW; retain hostile/quest enclaves and sewer connections |
| Sandcaster | 32×32 | 27 | 5 | 32 | Second substantial hub inside SE; retain the hostile wizard district and infiltration logic |
| Lakeside | 16×16 | 5 | 1 | 6 | Witch-occupied settlement/dungeon, not a normal six-service village |
| Necropolis | 16×16 | 1 | 1 | 2 | Hostile necromantic destination with Sandro and a guild, not an underpopulated city to fill arbitrarily |
| Olympus | 16×16 | 6 | 5 | 11 | Compact elite sky settlement; one coordinate has multiple conditional NPC identities |

“NPC site” means at least one NPC opcode at a real map coordinate. It includes prisoners, enemies, street encounters
and residents. Multiple titles/branches at one coordinate count once. **Do not turn 41 Castleview sites into a claim of
41 original houses.** The six service actions are bank, blacksmith, guild, tavern, temple and training. The supplied
Sandcaster events contain five direct standard-service sites and no bank action; the printed cluebook lists a bank.
That discrepancy remains an explicit source/runtime-audit item rather than an invented sixth service.

The local [house-variety calibration](../../HOUSE_VARIETY.md) measures **59 land house/service destinations in 51 physical
Ravenshore assemblies**, including 44 ordinary houses. Accepted Brackenford has **29 destinations in 28 structures**.
Castleview's 41 and Sandcaster's 32 interaction coordinates are therefore a credible starting content load for towns
in this design language. This is an order-of-magnitude comparison, not an exact metric match: a later door/physical-block
inventory must resolve which NPCs share buildings or stand outside.

Use the existing calibrated kit and spacing, rather than enlarge houses to fill a converted grid:

- Comparable district median building-envelope gaps are about **464–608 native units** in the two measured Ravenshore
  districts; accepted Brackenford is about **735**. The broader 450–950 range is a starting reference, not a universal rule.
- Ordinary building centers in those reference districts are roughly **1,200–1,800 units** apart.
- Native terrain cells are **512 units**. Brackenford's ordinary doors average about **371 units from shared-road cell
  centers**, a different measurement from building gaps or painted road edges.
- Joined service blocks, varied small homes, enclosed lanes, civic spaces and a few landmarks can deliver these counts
  without inventing dozens of filler establishments. Additional buildings need an explicit resident or other purpose.

References: [settlement density](../../SETTLEMENT_DENSITY.md), [frontage](../../FRONTAGE_AND_TILE_CALIBRATION.md),
[accepted outdoor workflow](../../OUTDOOR_CALIBRATION.md).

## 4. World scale and town scale must be chosen independently

The native terrain has 128×128 samples at 512-unit spacing, with 127×127 rendered quads. The measured Ravenshore
travel square is **46,286 units wide** (±23,143); its terrain extends farther for visible scenery. A 2×2 MM5 outdoor
group is **32×32 source cells**. If only its outer dimensions were mapped uniformly to that travel square, a source
cell would span approximately **1,446 native units**, or 2.82 terrain cells.

That ratio is a **planning ruler**, not a conversion rule. A town occupies one symbolic overworld entrance cell in MM5
but contains up to 1,024 town cells behind it. Expanding those local town cells at the world ratio would consume a whole
regional map. Instead, reserve a measured town district—initially perhaps **12,000–20,000 units across** for a large hub,
subject to building-footprint review—and distribute its doors using the existing kit. Fit its approach, Kalindra and
the countryside around that footprint. Those district dimensions are proposed design ranges, not measurements of MM5.

Store original world square/cell and original town cell alongside each new semantic anchor. Author new coordinates for
roads, district entrances and buildings. Preserve relative direction, neighboring locations and route dependencies;
do not require identical geometric distances. A full-scale SW plan is the right experiment to decide whether six
regions are enough. Correct house dimensions, purposeful empty space and walking experience take precedence over a
uniform pixel-to-unit formula.

## 5. Travel arrangement

The proposed surface regions form a 3×2 adjacency grid:

```text
NW (Alamar) ----- NC (Desert) ----- NE (Blackfang)
     |                |                 |
SW (Castleview) - SC (Sprite Forest) - SE (Sandcaster)
```

These lines show **geographic adjacency**, not seven existing roads. The source has road-coded cells crossing four
of these regional links:

| Proposed regional link | Original crossing with road codes on both sides |
| --- | --- |
| SW ↔ SC | B3 east edge ↔ C3 west edge, local Y=3 |
| SC ↔ SE | D3 east edge ↔ E3 west edge, local Y=1 |
| NC ↔ NE | D2 east edge ↔ E2 west edge, local Y=15 |
| NE ↔ SE | F2 south edge ↔ F3 north edge, local X=0 |

The other geographic links need an explicit off-road/pass/water/magic-travel decision. Zero road-coded cells is not
proof that a border is impassable. Mountains, walls, traversal skills and state need further route validation.
Preserve the main southern journey Castleview → forest → Sandcaster and the relevant northern approaches. Do not
automatically pave every border, cave, camp or quest marker.

Use normal OpenYAMM regional travel metadata at the outer boundaries. Internal 16×16 source seams disappear inside
each grouped ODM. Retain separate incoming anchors and headings for each route and meaningful alternative entrances.
The calibrated outer terrain continues beyond travel prompts; no automatic mountain wall or mandatory road bend is
needed. See [regional transition calibration](../../REGIONAL_TRANSITION_CALIBRATION.md).

MM5's borders normally allow continuous step movement; assigning MM6-style travel days changes food, healing and
time-sensitive balance. Choose travel durations deliberately during pacing, rather than inheriting arbitrary MM6
defaults. Preserve separate destinations for mirrors/Town Portal, keyed gates, boats, ropes, tower exits and falls.
The extracted mirror list supplies **32 named geographic destinations plus three cinematic commands**; commands with
destination 0 are not physical places. General fall logic and mirror spells also add routes beyond explicit EVT links.

## 6. Skyroads and elemental planes

Keep the Skyroads as a **separate world layer**, not a second terrain sheet in a surface ODM. A native heightfield
cannot represent two independent heights at the same XY. Separate sky maps with authored static walkways/platforms
are plausible; landing on them, falls, flight, actor movement and loading need one small executed prototype.

For a complete first map manifest, use **six corresponding sky regions**. This keeps tower/castle alignment simple.
Some sky groups are sparse and may later combine into four, or use compact route-focused spaces. They do not need
the same occupied area or town density as the surface.

| Sky region | Original squares | Important vertical/access relationships |
| --- | --- | --- |
| Sky SW | A3, A4, B3, B4 | Western Tower roof A3; Ellinger and Kalindra A4; Dark Grove rope; Lucio's transport route |
| Sky SC | C3, C4, D3, D4 | Southern Tower D4 and east–west sky routes; preserve sparse exposure |
| Sky SE | E3, E4, F3, F4 | Eastern Tower F3; sky merchants E3; lake boatman F4; Earth-plane entrance F4 |
| Sky NC | C1, C2, D1, D2 | Olympus C2; Northern Tower D1; Great Pyramid D2; Lucio's arrivals |
| Sky NE | E1, E2, F1, F2 | Blackfang upper entrance F1; Air-plane entrance F1 |
| Sky NW | A1, A2, B1, B2 | Alamar upper entrance A1; Fire-plane entrance A1; very dangerous approach |

Water-plane access is at Sky A4. Preserve four separate elemental maps: Fire 25, Air 26, Earth 27, Water 28.
They exist in MM5's data, even though the elemental sleeper objectives also matter to the excluded WoX finale.

Thus a complete working baseline is **6 surface + 6 sky + 4 elemental = 16 outdoor-style maps**, with several towns
embedded as districts and interiors beneath/inside them. This is a proposed content partition, not proof that every
sky feature already works. Four sky groups would reduce the baseline to 14; choose after the sky prototype.

## 7. Interior / location list and joining rules

The 60 original town/interior logical maps can be organized into the following **25 authored location groups**.
These are production groups, not a promise of 25 final BLV files. Preserve floor transitions when they help streaming,
pacing, state or navigation. Combining floors into one BLV requires actual vertical architecture and visibility work.

| Location group | Source logical maps | Recommended treatment |
| --- | --- | --- |
| Castleview | 29 + continuation blocks | SW outdoor district; preserve jail/Gremlin/quest enclosures separately as needed |
| Castleview Sewer | 30 + continuations | One sewer complex with all five town shafts and the wilderness access |
| Sandcaster | 31 + continuations | SE outdoor district; the hostile wizard enclave needs a preserved sewer-dependent route |
| Sandcaster Sewer | 32 + continuations | One complex; retain town shafts and the remote D2 exit |
| Lakeside | 33 | Compact hostile town/dungeon; a separate BLV enclosure is a sound first implementation |
| Lakeside Sewer | 34 | Separate interior linked to the town's original shafts |
| Necropolis | 35 | Hostile enclosed necromantic location in NW; separate BLV is appropriate |
| Necropolis Sewer | 36 | Separate interior |
| Olympus | 37 | Compact district in Sky NC; Soulbox access must retain its sewer route |
| Olympus Sewer | 38 | Separate interior |
| Castle Kalindra | 41–44 | Three restored floors plus dungeon; preserve staged access |
| Castle Blackfang | 45–48 | Three floors plus dungeon; keep ground and roof access distinct |
| Castle Alamar | 49–52 | Three floors plus dungeon; preserve final progression and upper-entry challenge |
| Ellinger's Tower | 53–56 | One four-floor tower group, connected to Castleview and Sky A4 |
| Western Tower | 57–60 | One four-floor tower group; roof access is part of the key route |
| Southern Tower | 61–64 | One four-floor tower group; D4 ground/sky links |
| Eastern Tower | 65–68 | One four-floor tower group; F3 links, Jewel of Ages |
| Northern Tower | 69–72 | One four-floor tower group; D1 links |
| Temple of Bark | 73–77 | Five-floor dungeon group; final floor is 32×32 |
| Dungeon of Lost Souls | 78, 80, 79, 81, 82 | Five floors in **named floor order**; final floor is 32×32. IDs 79/80 are not floor order |
| Great Pyramid | 83–86 | Three 32×32 levels and a 16×16 summit; stateful puzzles and Pharaoh access |
| Gemstone Mines | 39 + continuations | Several separate caves sharing a source map; preserve which entrances actually connect |
| Troll Holes | 40 + continuations | Several separate pockets sharing a source map; preserve individual falls and returns |
| Escape Pod 1 | 87 + 163 | One 32×16 science-fiction interior; Corak progression |
| Escape Pod 2 | 88 + 164 | Separate 32×16 interior; retain independently rather than joining both spacecraft |

The mines/holes are an important exception to “one source map = one continuous dungeon.” The source has **10 exterior
mine-entry coordinates and 15 exterior troll-hole coordinates**. The official cluebook describes nine mines, including
a through-mine, and fourteen holes; the precise hole count and connectivity require the gameplay audit. Do not join
all these pockets into a new tunnel network and accidentally create shortcuts across several regions.

Embedding Castleview, Sandcaster and Olympus into ODMs leaves **22 interior/location groups**, before any additional
protected town compounds and before splitting individual cave pockets or floors. Much of the project effort will be
these interiors and their events, not the six main landscapes.

### Working BLV target clarified after the feasibility discussion

**Start with one dungeon complex per BLV.** Combine its original floors into continuous authored architecture where
practical: a four-floor MM5 tower can become one BLV with stairs, ramps or shafts between floors. Do not automatically
create one BLV for every original MM5 floor map.

The working content target is therefore **16 ODMs plus roughly 22 or more BLVs**. The 22 groups contain **57 original
town/interior logical maps** (60 minus the three towns embedded outdoors). Those 57 maps describe the source content
to recreate, not a required output-file count.

The two cave collections are the main exception: **Gemstone Mines and Troll Holes each occupy one inventory group but
contain multiple separate cave pockets**. They will likely require several BLVs per group, preserving their original
entrances and actual connections. Large complexes may also split where layout, visibility or performance requires it;
protected town compounds may add further BLVs. Thus 22 is a grouping baseline, not a commitment to exactly 22 files.

## 8. Quest and access relationships to preserve

This is a **key dependency inventory**, not a claim that every quest's complete control flow has been decompiled.
All NPC/service coordinates and associated dialogue text indices are in `sites.csv` / `inventory.json`; complete
numeric event records remain in the extracted source. The rows below identify route-shaping work for the new map plan.

| Quest / relationship | Places it ties together | Requirement for the recreated geography |
| --- | --- | --- |
| Nadia's Onyx Necklace → Ellinger's Tower | Castleview ↔ sewer ↔ tower | Preserve the sewer objective, return NPC and keyed tower entry |
| Jasper/Jethro/Joe map thread | Castleview jail, mapmakers; Magic Mountain wizards | Prison access and later map/merchant contacts must survive the town redesign |
| Energy Disks → phased Kalindra restoration | Castleview/Gremlins, Temple of Bark, towers, giant/ogre contacts → Ellinger → Kalindra | Preserve staged progression; the story asks for successive groups of 5, 5 and 10 disks |
| Nibbler's Monga Melons → Temple of Bark key | SW fruit/Nibbler ↔ SC temple approach | Retain the visit-and-return structure and Sharla's nearby rescue contact |
| Sharla's captive sprites | Temple of Bark ↔ C4 Sharla | Prisoners and return reward, not just a generic dungeon clear |
| Vespar's staff → Sandcaster pass | B3 Vespar ↔ E3 roadside handle ↔ Sandcaster gate | Main southern journey must remain meaningful before fast travel |
| Sandcaster liberation | Astra, Xenoc/Morgana, wizard quarter and sewer | Outdoor flight/jumping must not silently bypass the intended infiltration |
| Town passes | Justine → Castleview; Vespar → Sandcaster; Geoffrey → Lakeside; Lakeside → Necropolis; Pharaoh → Olympus | Preserve access state at logical district gates/destinations |
| Dimitri/Megan → Songbird of Serenity | Kalindra level 2 ↔ Lost Souls dungeon ↔ Dimitri | Keep the long eastern expedition and return destination |
| Ambrose's bridle | Griffin Pass ↔ Natasha in Sandcaster ↔ Blackfang | Retain two Ambrose contexts and the distinct rescue-capable ground entry |
| Queen Kalindra's crown → Great Pyramid key | Blackfang dungeon ↔ Kalindra level 3 ↔ Queen ↔ Great Pyramid | State and return visits matter more than identical floor rectangles |
| Dragon Pharaoh → Corak → Soulbox → Sheltem | Great Pyramid ↔ escape pod ↔ Olympus/sewer ↔ Corak ↔ Alamar | Preserve endgame access ordering and the sewer-dependent Soulbox route |
| Dreyfus and Western Tower | A3 priest ↔ sky-accessed tower key ↔ lower entrance | Roof and ground entries must remain different routes |
| Luna's three statuettes | SW druid ↔ Western Tower, Lakeside sewer, Necropolis (Southern Tower supplies the sales-record clue) | Cross-region collection/return anchors |
| Thaddeus/Jewel of Ages | F4 fountain keeper ↔ Eastern Tower | Fountain state and Southern Tower key relationship |
| Kramer / Yog / Gurodel / Graalg | Ogre Pass, barbarian/giant camps, named leaders | Avoid turning negotiable groups into indiscriminate hostile spawn areas |
| Local forest and mountain threads | Ector, gemsmiths/mines, Cornelius, rescued Celia/Derek, fruit huts and fountains | Preserve individual interactions and reward state without inventing a village around every NPC |

Modern free movement is the major compatibility issue. Castleview, Sandcaster and Olympus have spaces reached through
sewers, and Blackfang's roof entry does not grant the same access as the rescue route. Use actual enclosed geometry,
small BLV compounds, locked interiors or an explicitly designed local rule where appropriate. Simply building low
walls and enabling normal Fly would change these quests. This study does not prescribe a blanket prohibition on flight.

## 9. Fit with the existing generation pipeline

The [pipeline status](../../PIPELINE_STATUS.md) already demonstrates generated native ODM terrain/BModels, native BLV
rooms and linear mechanisms, house/NPC registrations, Lua events, rewards and packaged playable content. The
[accepted outdoor calibration](../../OUTDOOR_CALIBRATION.md) addresses the exact issues relevant here: native facade
scale, physical assembly counts, settlement spacing, door frontage, useful open spaces and scenery density.

| Area | Feasibility | Main remaining work |
| --- | --- | --- |
| Ordinary surface regions, streets, shops, town houses | High | Authored footprints, biome kits, original NPC/service mapping and visual iteration |
| Caves, towers, castles, sewers | High, using the demonstrated BLV path | Reconstruct route/puzzle graphs; model new rooms rather than extrude all grid cells |
| Shared registries and map travel | Established mechanisms | New namespaced MM5 content and stable aliases; declare IDs/QBit ranges in the flat base architecture |
| Skyroads, void falls, elevated routes | Plausible; needs a focused fixture | Floor collision, actors/projectiles, flight policy, destination/damage and persistence on falling |
| MM5 scripts and quests | Feasible but substantial manual/semantic work | Static opcode indexing is not an event exporter; resolve branches, calls, quest items and state |
| Combat/economy/skills | Adaptation required | MM5's six-character party, step/time behavior, stat rewards and spell economy cannot be copied numerically into MM6–MM8 rules |
| Monsters and special art | Straightforward in concept | Choose MM6–MM8 equivalents and create missing sprites/materials for identifiable MM5 creatures and landmarks |

Keep the new world mounted as content, using shared gameplay and engine/base registries. Raw MM5 IDs remain import
aliases, not new global meanings. Nothing here calls for a separate MM5 engine or duplicating the shared house,
inventory, combat, party or travel systems. The current level-generation package demonstrates a project-specific
build path, not a universal production mod/table merge installer; production packaging still needs scoped integration.

## 10. What should happen before committing to the full world

The right next deliverable is an **SW regional layout study at actual native units**, retaining Castleview's meaningful
NPC/service sites, its sewer shafts, Ellinger, Kalindra, Western Tower and the eastern travel route. Lay out real-size
building footprints and approaches first. This directly answers whether one ODM can hold the intended hub without
oversized houses, empty land or compressed travel. If it cannot, split SW intentionally into a town/castle region and
western frontier; do not shrink the kit to defend the six-region count.

In parallel in the project schedule, a **small sky-route fixture** should prove one walkway, one tower doorway, one
fall-to-surface trigger and normal movement/flight behavior. This is a separate technical question from town density.
Neither prototype was built during this feasibility study.

After those decisions, finalize a semantic world manifest: each original square and logical map has an owner, each
quest/house/POI has a new anchor, and every arrival/return/fast-travel destination is explicit. Only then generate the
full landscapes and interiors. The current evidence is enough to justify that next stage; it does not establish final
performance, balancing, build time or an exact final BLV count.

## Evidence and reproduction

Primary local evidence is the user's extracted GOG data: `raw/dark_initial_state`, `raw/dark`, map-name strings,
`darkmirr.txt`, numeric events and map neighbor links. `provenance.json` records source hashes. The source survey is
reproducible with:

```sh
python3 level_generation/projects/mm5_world_feasibility/analyze.py
python3 level_generation/projects/mm5_world_feasibility/build_atlas.py
```

External interpretation references are the [original NWC MM5 cluebook](https://www.mocagh.org/nwc/mm5-cluebook.pdf)
(towns pp. 5–30; surface pp. 83–109; Skyroads pp. 111–135; mines/holes pp. 147–153; story pp. 246–249;
explicit WoX bonus section p. 251 onward), and ScummVM's
[map loading](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/map.cpp),
[event interpretation](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/scripts.cpp),
[keyed location entrances](https://github.com/scummvm/scummvm/blob/master/engines/mm/xeen/locations.cpp) and
[direction/scenery constants](https://github.com/scummvm/scummvm/blob/master/devtools/create_mm/create_xeen/constants.cpp).
The cluebook is a cross-check; local source coordinates and measured event counts are preserved when they disagree.
New survey code was written for this task; no game runtime/reference implementation was copied.

The atlas's background is a source surface/scenery-class schematic; it does not render original sprite silhouettes,
elevation, animated water, dynamic state or a complete passability map. Doors and other nonzero indoor wall codes are
shown schematically. Branch reachability, general movement/fall rules, dynamic NPCs and semantic quest completion still
need the later gameplay audit. No MM6/MM7/MM8 runtime regression testing was necessary for this read-only study.

## Detailed first-region layout

The [Castleview–Kalindra wireframe](../mm5_castleview_kalindra/index.html) now develops SW into a source-linked regional and town proposal, including all NPC/service sites, measured MM8 shared occupancy, building assemblies, streets, quest access, water, encounters and planting. See its [design notes](../mm5_castleview_kalindra/README.md) for explicit adaptations and remaining implementation decisions.
