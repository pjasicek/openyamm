# Natural entrances and clearings: source evidence before construction

The eight remaining natural sites retain their extracted source events in
[natural_site_sources.json](natural_site_sources.json). This record is inactive design evidence, not runtime travel.
It includes outgoing transfers and nearby reverse-destination return candidates; confirm the exact pair before
activating a later route. The current environment goal requires visible, reachable, status-only interaction settings.

| Site | Original identity / destination | Required interpretation |
| --- | --- | --- |
| Falista | A4 (7,1); source contact Falista the Unicorn | Preserve the conditional empty/rescued sanctuary. The original unavailable label says “The hut is empty.”; retain that source wording without inventing a human household or spawning the unicorn. |
| Nibbler | B4 (3,12); source contact Nibbler the Monkeydog | Natural shelter and reserved future melon ground. No productive crop or quest reward yet. |
| Gemstone Mine | B3 (10,9) → map 39 (25,0) | Timber-supported natural entrance, preserving this particular mine pocket. |
| Troll Hole west | B4 (8,12) → map 40 (3,3) | Voluntary descent and fall are alternative source triggers for one destination. |
| Troll Hole east | B4 (12,13) → map 40 (9,3) | Separate pocket; no invented connecting tunnel. |
| Troll Hole south | B4 (11,6) → map 40 (15,3) | Separate off-road descent. |
| Sewer outfall | A4 (14,8) → map 30 (17,0) | Retained alternative sewer access with a dry supported approach from the river bank. |
| Skyroad rope | A3 (14,7) → map 91 (13,8) | Source text describes a rope rising through the ceiling. Preserve the upper destination and separate return marker; current interaction must leave the party in this map. |

The Garrote [Dragon Cave assembly](../../../catalogues/mm8_garrote_gorge/images/assembly_dragon_cave.png) and both
component views were actually inspected. The native composition uses rough `T68A02A` rock and a recessed `solid01`
dark entrance surface. These provide an original-game reference for readable cave mouths and placeholder depth;
the new entrance geometry must be independently constructed and fitted to MM5 terrain. The dark face is not proof
of a connected interior. Preserve ordinary entry scale and sufficient standing space.

The troll sites need a deliberate descent treatment. Native terrain cannot be cut by placing a BModel ring on it.
Do not leave visible grass through a supposedly open hole, create a fall trap without an implemented destination,
or certify a dark flat decal as a finished shaft. Fit a shallow rocky descent/entrance volume and its supported
interactive surface, then review it from player height. Its deeper BLV and fall-state behavior remain deferred.

The sewer reservation needs particular attention: its centre (-768,-10240) and old south-facing frontage
(-768,-10528) lie at Z256. The source material mask places river water here, with southern land beginning around
Y=-10752 and rising toward Z352 at Y=-11264. Before committing geometry, inspect the native water/shore flags and
painted boundary. Resolve a bounded bank placement or supported landing linked to dry ground; a flat Z256 sample
alone does not establish dry access. Keep the source identity and record any frontage/placement change explicitly.

A bounded [approach proposal](../review/sewer_approach_proposal.json) now retains the original outfall position:
a 256-wide, 736-long landing descends from southern bank Z358 to threshold Z288. Both proposed walking triangles
remain at least six units above native ground, with the threshold 32 above the river level. Native tile sampling
distinguishes the source water mask from runtime behavior: the current frontage/centre use `wtrdrs`, flags `0x0300`
(shore/transition), while the bank uses `grastyl` and `grdrtn`. They are not pure-water descriptors. Inspect the
painted shoreline and actual movement with the built landing before acceptance.
[The authored sewer](SEWER.md) refines this into a 608-long ramp, 128-long level landing and recessed grating.
Source and native views are inspected; ordinary bank access, grating click/collision and reload now have evidence.

The mine and three troll descents now have [authored source geometry](NATURAL_ENTRANCES.md), with their local native
review tracked separately. Falista, Nibbler and Skyroad rope remain unauthored; sewer local native review is recorded
in its linked construction notes. This source-evidence
record itself does not establish terrain corrections, active travel or runtime acceptance.

[The measured Falista/Nibbler clearing proposal](NATURAL_CLEARINGS.md) retains their open approaches and deferred
occupancy/growing-ground rules. Its plan and native sprite art are inspected; no native entities are added yet.

[Skyroad source-art verification](SKYROPE.md) identifies the original shared hut marker and retains the accepted
exposed rope/anchor interpretation and required upper-endpoint review. The rope remains unauthored.
