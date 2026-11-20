# Brackenford and Greywatch Vault

Two original playable MM8 maps, generated through Blender MCP and native OpenYAMM writers. The completed test brief
is [GOAL.md](GOAL.md). The current outdoor work is documented in [ROAD_PURPOSE_REVISION.md](ROAD_PURPOSE_REVISION.md);
[ACCEPTANCE.md](ACCEPTANCE.md) retains the original functional history.

## Play this revision

The revised snapshot is `/tmp/openyamm-brackenford-playtest-offroad`. Run either:

```sh
/tmp/openyamm-brackenford-playtest-offroad/play.sh outdoor
/tmp/openyamm-brackenford-playtest-offroad/play.sh indoor
```

Choose **Load Game → Scenario**. At the driver’s request, both current launchers now start with the built-in **God**
level-100 Lich (Grandmaster-200 skills and all spells). Each launch has separate saves/settings. The earlier
`playtest-final` snapshot and its `level25_saves/` backups remain available; original acceptance used that ordinary party.
The executable, maps, Lua and tables are copied; original artwork is shared from this checkout. Subsequent generation
builds do not refresh this snapshot. `/tmp` may disappear on reboot; [REBUILD.md](REBUILD.md) recreates it from the archive.

Brackenford's castle and hillside cave enter different parts of the same Greywatch dungeon. Both exits return to their
corresponding exterior. Ordinary doors accept clicks. The records control opens the lift gate and unlocks the shortcut;
the shortcut's two landing controls then operate it. Boarding the lift triggers one trip; wall controls call/recover it.
The west regional road reaches Ravenshore and the north road reaches Alvar. Their stables have a daily return in this
isolated installation; Brackenford's borrowed MM8 stable service retains its original schedule.

Final encounter balance belongs to the driver. [BASELINE_PARTY.md](BASELINE_PARTY.md) records equipment, skills and
reference-based placement; the functional checks do not claim a continuous, attack-only victory through every room.

## Delivered maps

| | Brackenford `lg01.odm` | Greywatch `lg02.blv` |
| --- | --- | --- |
| Native structure | 128 × 128 terrain; 87 BModels / 3,880 faces | 778 faces; 25 sectors including empty zero; 24 portals |
| Layout | 29 doors in 28 houses/blocks; 10 forms; river/pond/bridge, castle, cave, two regional passes | 11 chambers plus connectors; floors at 0/384/768; stair shortcut |
| Population | 9 guards, 20 villagers; 73 enemies in 11 wilderness areas | 24 existing MM8 mercenaries |
| Decoration | 487 trees, 416 plants, 239 rocks, 18 props, six lights | 34 decorations; native benches/tables/rack; 22 light pools |
| Gameplay | MM8 services, four teachers, resident topics, four chests, five loose items, two wells, fountain, four stat barrels/obelisk, two buffs/one challenge | Eight movers, automatic/button lift, secret room, two projectile plates, four chests |
| Treasure / refill | Level 6 / 336 days | Level 5 / 336 days |

Town house shapes, roof heights, sizes and orientations vary within a shared MM8 timber/stone palette. Gardens and
woodland groups preserve door/road clearances. Native terrain rises through town shelves and encloses the regional
approaches; ridges screen wilderness routes without changing draw distance. The cave has a small dirt-matched collar within a terrain cleft, with wolves and a nearby chest.
A quiet meadow pond and open timber bridge use native terrain water and existing MM8 art.
The cave and ogre caches are off-road; roads serve the town, castle and regional connections.
The density revision reduces median nearest-house envelope gaps from 1,866 to 832 native units and the settlement
footprint by 57%; see [spacing and reference districts](../../SETTLEMENT_DENSITY.md). The facade revision uses 128×256 doors, coherent native window/wall panels, service signs and no chimneys; ordinary
houses retain the calibrated repeated forms, with five additional inhabited court/well-lane buildings. Ordinary doors now sit close to shared streets, dedicated lanes align with their doors, and the corrected terrain uses matching native transition corners. Wells and fountains sit outside the road corridor. See [variety ratios](../../HOUSE_VARIETY.md).
Greywatch's upper entrance uses the vault's masonry; its natural lower entrance keeps sloping rock walls. Occupied
sectors use native ambient 22, matching the inspected Naga Vault and Ilsingore's Cave values.

## Sources, package and evidence

- [Content ZIP](dist/brackenford_greywatch_content.zip) and [manifest](dist/brackenford_greywatch_content.manifest.json):
  native maps, companion scenes, complete Lua, automap and isolated registration tables. Requires the matching local base.
- Editable [outdoor Blender source](source/lg01.blend) and [indoor Blender source](source/lg02.blend): independently
  reopened with packed images, no linked libraries. Authoring scripts regenerate geometry and semantic manifests.
- [Rebuild/install instructions](REBUILD.md): exact compiler, Blender, native writer, staging and verification sequence.
- [Stable IDs](source/ids.json), [town reuse](TOWN_REUSE.md), [reward provenance](source/reward_registry.json),
  [travel registrations](source/travel_registry.json), [outdoor markers](source/lg01.semantic.json) and
  [indoor markers](source/lg02.semantic.json). Map IDs are 9081/9082; house/NPC instance allocations start at 12000.
- [Outdoor plan](outdoor_plan.json), [indoor room/event graph](indoor_plan.json),
  [current town overview](review/brackenford_native_landscape_town.png), [indoor cutaway](review/greywatch_native_north.png).
- [Reference population/composition guide](../../POPULATION_AND_COMPOSITION.md): 33 MM6/MM7/MM8 case studies with
  inventories, highlighted reference captures, terrain and architectural comparisons.
- [Review history](REVIEW_LOG.md) and [current progress](progress.json). Older failed reports are retained; the acceptance
  checklist identifies their passing replacements and current artifact hashes.

Edit `source/lg01.handlers.lua` / `source/lg02.handlers.lua` for gameplay. Builders assemble registrations around these
handlers; never edit generated runtime Lua or original legacy scripts. Marker previews are excluded from native collision.
No final BLV/ODM needs manual repair or finishing.

The current sketch layout uses an irregular loop, a native diagonal street, an uphill guildmaster residence and a raised,
rotated temple. The fountain restores 15 HP and 15 mana per selected-character use, capped at 40 shared uses per game day.
