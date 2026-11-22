# Prep: Q-C1 The Seasons Relay

Scenario `q-c1_seasons_relay.yml`. Quest file `source/quests/q-c1.yml`; generated `events/common/xeen_quests.lua`
(topics 42551 Summer, 42552 Autumn, 42553 Winter, 42554 Spring); quest stub `tools/xeen/quest_stub/act3_cloudside.yml`.
No story precondition; no gate on any druid's topic.

## Getting there

All four druids stand outdoors (no house), so the party is placed beside each (PLAYBOOK section 2) and moves between
the maps with `travel` (overland, 4 days each leg).

| map | druid | scene actor | NPC | actor at | stand at |
| --- | --- | --- | --- | --- | --- |
| X6 | the Summer Druid | 6 | 4601 | (2867, -13414, 1440) | (2560, -13926, 1440) (X6 L4 playtest) |
| X4 | the Autumn Druid | 35 | 4321 | (-19456, -3379, 1120) | (-19149, -3584, 1120) (X4 L4 playtest) |
| X5 | the Winter Druid | 123 | 4529 | (-17203, 1229, 1024) | (-16589, 1331, 1043) (X5 L4 playtest) |
| X1 | the Spring Druid | 77 | 4048 | (-18842, 1638, 640) | (-18500, 1638, 640) |

## Topics (one each; the state picks the text)

- Summer (4601): first "…The year is a relay, and I have held it long enough." gives the Last Flower of Summer 12510,
  sets summer 112021 and started 112020; again "Take the Last Flower of Summer to the Autumn Druid on the savannah…".
- Autumn (4321): with the flower "Thank you for the Last Flower of Summer…" takes 12510, gives the Leaf 12511, sets
  autumn 112022; again "Please take the Last Fallen Leaf of Autumn to the Winter Druid."
- Winter (4529): with the leaf "The last leaf. Then winter may begin…" takes 12511, gives the Snowflake 12512, sets
  winter 112023; again "Take the Snowflake to the Spring Druid by Pitchfork Creek…".
- Spring (4048): with the snowflake "…As I renew the year, so will I renew you." takes 12512, gives the Raindrop
  12513, sets done 112024, `Xeen.renewAges()` (every member `SetValue(Age, 0)`, i.e. `ageModifier = 0`), 8,000 XP
  each; again "Spring comes to those who wait. You did not wait; you walked. That works too."

`started` is not cleared by done: `until: [done]` only hides its journal line (quests.txt's forbidden column), so the
scenario asserts both set. No journal or quest-line assert form exists (only `autonote`, which this quest has none of).

## Magical age

The Age variable (EvtVariable 11) reads natural + magical age (`GameMechanics::characterAge`); the new level-26 party
is 28. `assert: {runtime_event_variable: {id: 11, member_index: N, value: ...}}` checks it. The scenario gives ten
years with `lua_event` `evt.ForPlayer(Players.All); AddValue(Age, 10)` (CONVENTION) and asserts 38, then 28 after
Spring.

## Fixed bug (engine, merge point 33)

Every rest used to clear magical age (`clearTemporaryEventBonuses` set `ageModifier = 0`, called by `restAndHealAll`
on rests and travel days), so an aged party lost it on the first rest and the Spring Druid had nothing to renew. A1
fixed it in merge point 33 (2026-11-21 14:44). The scenario now gives the ten years on X6 at the start and asserts them
still there on X1 after three overland trips.
