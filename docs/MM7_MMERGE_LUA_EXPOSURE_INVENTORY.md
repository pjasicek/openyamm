# MM7 MMMerge Lua Exposure Inventory

This document tracks the engine-to-Lua/runtime surface needed to implement the MM7 MMMerge fixup slice from
`MM7_MMERGE_FIXUP_INVENTORY.md`.

The goal is not MMExt compatibility. The target is a small OpenYAMM overlay API that can express the MMerge behaviors
cleanly on top of generated map/global scripts.

## Current Surface Already Available

These are already usable from OpenYAMM event Lua or support helpers:

| Surface | Available API | Notes |
| --- | --- | --- |
| Event registration/replacement | `RegisterEvent`, `RegisterGlobalEvent`, `ReplaceMapEvent`, `ReplaceGlobalEvent`, `RemoveMapEvent`, `RegisterMapOnLoadEvent`, `RegisterMapOnLeaveEvent`, `RegisterMapTimerEvent` | Enough for simple event replacement and load/leave supplements. |
| Basic event actions | `evt.MoveToMap`, `evt.EnterHouse`, `evt.SpeakNPC`, `evt.ShowMovie`, `evt.PlaySound`, `evt.StatusText`, `evt.SimpleMessage` | Move/dialogue/status primitives exist. |
| Map/world mutation | `evt.SetDoorState`, `evt.StopDoor`, `evt.SetTexture`, `evt.SetOutdoorModelFacetTexture`, `evt.SetSprite`, `evt.SetFacetBit`, `evt.SetMonGroupBit`, `evt.SetMonsterBit`, `evt.SetMonsterGroup`, `evt.ChangeGroupAlly` | Enough for many static and event-driven map fixes. |
| Spawn/object/chest | `evt.SummonMonsters`, `evt.SummonItem`, `evt.SummonObject`, `evt.OpenChest`, `evt.EnsureChestItem`, `evt.SetChestBit`, `evt.SetMonsterItem`, `RegisterMapRefillHook` | Enough for the current `mdt15` monster inventory refill; fuller slot-level monster inventory APIs remain optional. |
| Party state and variables | `IsQBitSet`, `SetQBit`, `ClearQBit`, `HasAward`, `SetAward`, `ClearAward`, `SetAutonote`, `MapVar`, `GetRuntimeVariable`, `SetRuntimeVariable`, `GetPartyVariable`, `SetPartyVariable`, `CurrentGameMinutes` | Numeric runtime variables exist; named persistent vars need a cleaner API. |
| Inventory basics | `HasItem`, `GiveItem`, `RemoveItem`, `evt.CheckItemsCount`, `evt.RemoveItems` | Missing mouse-carried item and equipped-item checks. |
| NPC state | `evt.MoveNPC`, `evt.SetNPCTopic`, `evt.SetNPCGreeting`, `evt.SetNPCItem`, `evt.SetNPCGroupNews`, `AddFollowerNpc`, `RemoveFollowerNpc`, `HasFollowerNpc` | Missing NPC enter/exit hooks and fuller follower/roster operations. |
| Dimension Door | `evt.OpenDimensionDoor` | Need map trigger wiring for MM7 outdoor locations. |
| Local relations | `evt.SetMonsterRelation`, `ApplyLocalMonsterRelations` | Need explicit local hostile-table-style override semantics where MMerge edits `HostileTxt`. |

## Required New Hook Surfaces

### 1. NPC Enter/Exit Hooks

MMerge source shape:

- `function events.EnterNPC(i) ... end`
- `function events.ExitNPC(i) ... end`

Needed OpenYAMM API:

```lua
RegisterNpcEnterHook(eventId, title, function(npcId, actorIndex) ... end)
RegisterNpcExitHook(eventId, title, function(npcId, actorIndex) ... end)
```

Runtime requirements:

- Invoke enter hook when NPC dialogue is opened.
- Invoke exit hook when NPC dialogue closes, after any topic event side effects are applied.
- Provide canonical merged NPC id.
- Provide actor/runtime actor index when the NPC came from an in-world actor, optional otherwise.

MM7 overlays unblocked:

- `7d24`: clear QBit 658 when exiting Dwarf King NPC 398.
- `7out05`: summon hostile group 59 after exiting NPC 461 if QBit 761 is not set.
- `StdQuestsFollowers.lua`: remove rescued dwarves when entering Dwarf King NPC 398.
- Future promotion/follower global topic cleanup.

Implementation notes:

- This belongs in shared dialogue/gameplay code, not indoor/outdoor-specific code.
- Hooks should be map-local plus global. Global hooks are needed for `StdQuestsFollowers.lua`.

### 2. House/Shop Topic Hooks

MMerge source shape:

- `events.DrawShopTopics(t)`
- `events.ClickShopTopic(t)`

Needed OpenYAMM API:

```lua
RegisterHouseTopicFilter(eventId, title, function(context)
    -- context.houseId, context.houseType, context.mapName
    -- context:SetTopics({ HouseTopic.RentRoom, HouseTopic.BuyFood, HouseTopic.Learn })
end)

RegisterHouseTopicClickHook(eventId, title, function(context)
    -- return true/false handled
end)
```

Runtime requirements:

- Called before house dialogue topics are built/rendered.
- Allows replacing the visible action list for a specific map/house type.
- Allows intercepting a clicked topic and marking it handled.
- Needs stable topic constants for tavern rent/buy-food/learn/play-Arcomage.

MM7 overlays unblocked:

- `7out01`: remove Arcomage from Emerald Island taverns.
- `StdQuestsFunctions.lua`: block Antagarich Arcomage unless the party has Arcomage Deck item 1453.
- Later house-rule edge cases where MMerge alters specific house behavior.

Implementation notes:

- Prefer typed topic ids/action ids over raw MMExt `const.ShopTopics`.
- Keep table-driven house rules authoritative; use hooks only for map-specific overrides.

### 3. Rest Cost Hook

MMerge source shape:

- `events.CalcRestFoodCost(t)`

Needed OpenYAMM API:

```lua
RegisterRestFoodCostHook(eventId, title, function(context)
    -- context.baseFoodCost
    -- context:SetFoodCost(amount)
end)
```

Runtime requirements:

- Called when rest UI/action calculates the food requirement.
- Must be able to override food cost to zero for current map.

MM7 overlays unblocked:

- `7d29`: resting in Castle Harmondale costs zero food after QBit 610.

Implementation notes:

- Shared rest system hook. Do not special-case map names in rest UI.

### 4. Save/Lloyd Restriction Hooks

Current state:

- Arena restrictions exist in runtime, but MMerge expresses this as `events.CanSaveGame` and `events.CanCastLloyd`.

Needed OpenYAMM API:

```lua
RegisterCanSaveHook(eventId, title, function(context)
    return false, "optional status"
end)

RegisterCanCastLloydHook(eventId, title, function(context)
    return false, "optional status"
end)
```

Runtime requirements:

- Called by shared save and Lloyd's Beacon availability checks.
- Supports map-local and global hooks.

MM7 overlays unblocked:

- `7d05`: arena save/Lloyd blocks if current hardcoded restriction is not enough.
- `TownPortalSwitches.lua`: shared arena handling for `7d05.blv`.

Implementation notes:

- If current arena restriction already covers `7d05`, this API can be lower priority, but it is needed for parity and
  future map overlays.

### 5. Outdoor Edge Travel Hook

MMerge source shape:

- `events.WalkToMap(t)` with `t.LeaveSide`

Needed OpenYAMM API:

```lua
RegisterOutdoorEdgeTravelHook(eventId, title, function(context)
    -- context.leaveSide, context.defaultDestination
    -- context:Block(statusText)
    -- context:MoveToMap(x, y, z, direction, lookAngle, speedZ, houseId, icon, mapName)
end)
```

Runtime requirements:

- Called before automatic outdoor edge travel executes.
- Provides edge/side name matching the outdoor travel table direction.
- Allows blocking default travel.
- Allows replacing the map move.

MM7 overlays unblocked:

- `out14`: wetsuit-gated travel from Avlee to Shoals.
- Potential future MM6/MM8 edge-travel gates.

Implementation notes:

- Integrate with the existing `outdoor_travels.txt` consumer. The hook should decorate or override table travel, not
  replace the table.

### 6. Action / Item-Use Blocking Hook

MMerge source shape:

- `events.Action(t)` checks action ids and `Mouse.Item.Number`.

Needed OpenYAMM API:

```lua
RegisterGameplayActionHook(eventId, title, function(context)
    -- context.actionId, context.heldItemId, context.screen
    -- context:Block(statusText, soundId)
end)
```

Runtime requirements:

- Called before gameplay/UI action dispatch for map-local restrictions.
- Can block actions and set status/sound.
- Needs held item id.

MM7 overlays unblocked:

- `7out15`: underwater Shoals blocks specific actions and carried item use with status text.

Implementation notes:

- Keep action ids engine-native where possible; only expose legacy ids if we deliberately map them.

### 7. Tick / Proximity Hooks With Party Facts

Current state:

- `RegisterMapTimerEvent` can fire repeated events, but Lua lacks enough party/world facts for MMerge proximity logic.

Needed OpenYAMM API:

```lua
RegisterMapTickHook(eventId, title, intervalSeconds, function(context)
    -- context.partyX, partyY, partyZ
    -- context.flying, enemyDetectorYellow, enemyDetectorRed
    -- context.currentScreen, currentGameMinutes
end)
```

Runtime requirements:

- Supports repeated map-local callbacks.
- Supplies party position and safety/combat state.
- Can remove/disable itself through a runtime variable or explicit `context:Disable()`.

MM7 overlays unblocked:

- `7out02`: scavenger-hunt advertisement near Harmondale coordinates.
- `7out03`: scavenger-hunt advertisement near Erathia coordinates.
- `out09`: Dimension Door proximity trigger.
- `7out15`: Z-height auto-travel to Avlee.

Implementation notes:

- Existing timer metadata can back this if we add party fact getters and a stable self-disable mechanism.
- Avoid real-time SDL ticks here; these are game-time/event checks.

### 8. Party Position And State Accessors

Needed OpenYAMM API:

```lua
evt.GetPartyPosition() -> x, y, z
evt.GetPartyDirection() -> direction
evt.IsPartyFlying() -> bool
evt.GetEnemyDetectorState() -> yellow, red
evt.GetCurrentScreen() -> screenId
evt.GetCurrentMapName() -> mapName
evt.GetCurrentMapStatsId() -> mapStatsId
```

MM7 overlays unblocked:

- All proximity/tick hooks.
- `7out02`, `7out03`, `out09`, `7out15`.
- CrossContinent/Verdant logic later.

Implementation notes:

- `IsFlying` is already expressible through an event variable, but explicit fact access keeps authored overlays
  readable and avoids packed variable abuse.

### 9. Mouse-Carried Item API

MMerge source shape:

- `Mouse.Item.Number = ...`
- `Mouse.Item.Identified = true`
- `Mouse.Item.Charges = ...`
- `Mouse:ReleaseItem()`

Needed OpenYAMM API:

```lua
evt.GetHeldItemId() -> itemId
evt.ClearHeldItem()
evt.SetHeldItem(itemId, options)
-- options: identified, charges, maxCharges, bonus, enchantment, artifact
```

Runtime requirements:

- Works whether called from dialogue, map load, or item-use flow.
- If a held item exists, `ClearHeldItem` should follow current engine policy for dropping/returning/releasing.
- `SetHeldItem` must create a real inventory item instance, not only an item id.

MM7 overlays unblocked:

- `StdQuestsFunctions.lua`: Malwick grants identified charged Fireball wand.
- `out12`: Xenofex/control cube item 866 is put in mouse before speaking NPC 462.
- `7d27`: checks mouse item before granting item 1463.
- `UsableItems.lua` / `7nwc`: Temple in a Bottle return state.

Implementation notes:

- This should share code with the normal held-item UI/inventory service.

### 10. Equipped/Per-Member Inventory Queries

Needed OpenYAMM API:

```lua
evt.PartyMemberHasItem(memberIndex, itemId) -> bool
evt.PartyMemberHasEquippedItem(memberIndex, itemId, slot?) -> bool
evt.ForEachPartyMember(function(memberIndex) ... end)
evt.GetPartyMemberCount() -> count
```

Runtime requirements:

- Query active party members only.
- Equipped armor checks need enough slot information for wetsuits.
- Inventory checks should include normal inventory, not mouse item unless explicitly requested.

MM7 overlays unblocked:

- `7d23`: every active party member must have/equip wetsuit item 1406 to leave Lincoln for Shoals.
- `out14`: every active party member must have/equip wetsuit item 1406 to travel from Avlee to Shoals.
- Promotion/follower scripts that use party-wide item checks.

Implementation notes:

- The current generated scripts can do coarse `HasItem`; the wetsuit cases require per-character semantics.

### 11. Named Persistent Vars

Current state:

- Numeric runtime variables and `MapVar` exist.
- MMerge uses `mapvars.SomeName` and `vars.SomeName`.

Needed OpenYAMM API:

```lua
evt.GetMapVar(name, defaultValue)
evt.SetMapVar(name, value)
evt.GetGlobalVar(name, defaultValue)
evt.SetGlobalVar(name, value)
evt.ClearMapVar(name)
evt.ClearGlobalVar(name)
```

Runtime requirements:

- Persist map-local named values in saves.
- Persist global named values in saves.
- Support at least bool, number, string, and small structured values needed by this slice.

MM7 overlays unblocked:

- `7out02`: `GotAdvertisment`, `InvasionTime`.
- `7out03`: `GotAdvertisment`.
- `7d37`: `PortraitTaken`.
- `7nwc` / `UsableItems`: `TempleInABottleEnteredFrom`.
- `Quest_CrossContinents.lua`: multiple global quest state tables later.

Implementation notes:

- For near-term MM7 overlays, avoid full arbitrary Lua table serialization. Provide typed helpers for scalar values and
  a small `SetGlobalMapMoveVar` if needed for Temple-in-a-Bottle return.

### 12. Local Hostile/Relation Override API

Current state:

- `evt.SetMonsterRelation` exists.
- Runtime has `monsterRelationOverrides`.

Needed OpenYAMM API:

```lua
evt.SetLocalMonsterRelation(leftMonsterId, rightMonsterId, relation)
evt.SetLocalGroupRelation(leftGroupId, rightGroupId, relation) -- if needed
evt.ClearLocalMonsterRelations()
```

MMerge source shape:

- `LocalHostileTxt()`
- `Game.HostileTxt[91][0] = 0`

MM7 overlays unblocked:

- `7out05`: Deyja local relation override.
- Similar guard/peasant relation fixes from MM6/MM7 map overlays.

Implementation notes:

- Prefer explicit relation overrides over exposing raw `HostileTxt`.
- Must be map-local and reset on map unload unless persisted deliberately.

### 13. Map Refill Hook And Monster Inventory API

MMerge source shape:

- `if Map.Refilled then ... Map.Monsters[0].Items[0].Number = 866 ... end`

Needed OpenYAMM API:

```lua
evt.GetMapMonsterCount() -> count
evt.ClearMonsterItems(monsterIndex)
evt.SetMonsterItem(monsterIndex, itemSlot, itemId)
evt.SetMonsterTreasureItem(monsterIndex, itemId)
```

Current state:

- `RegisterMapRefillHook(eventId, title, function(context) ... end)` exists.
- `evt.SetMonsterItem(monsterIndex, itemId, has)` exists and now preserves multiple guaranteed items when scripts call it more than once for the same monster.
- Explicit monster item-slot APIs are still deferred until a later overlay needs them.

MM7 overlays unblocked:

- `mdt15`: refill resets the first two monsters so control cube 866 and blaster 1477 can be acquired again.

Implementation notes:

- This should run only on actual map refill/reset, not every load.

### 14. Party Face Override API

Needed OpenYAMM API:

```lua
evt.PushPartyFaceOverride(faceId)
evt.PopPartyFaceOverride()
evt.SetPartyMemberFace(memberIndex, faceId)
evt.RestorePartyMemberFace(memberIndex)
```

MM7 overlays unblocked:

- `7out15`: Shoals temporarily sets all party faces to 30 and restores original faces on leave.

Implementation notes:

- Prefer an overlay stack/saved-original mechanism over permanently mutating character face ids.

### 15. Transport Route Override API

MMerge source shape:

- `Game.TransportIndex[34][4] = 44` or `101`

Needed OpenYAMM API:

```lua
evt.SetTransportRouteDestination(routeId, slot, destinationId)
evt.SetTransportRouteEnabled(routeId, slot, enabled)
```

MM7 overlays unblocked:

- `7out03`: route to Emerald Island changes depending on whether QBit 519 is set.

Implementation notes:

- This should decorate the typed `transport_locations`/house-rules route model.
- If route ids are not stable in OpenYAMM, expose a semantic route key instead of raw index/slot.

### 16. House Override API

Current state:

- `evt.EnterHouse` exists.
- `npcHouseOverrides` exists.

Needed OpenYAMM API:

```lua
evt.SetMapHouseEvent(eventId, houseId)
evt.SetHouseExitMap(houseId, mapStatsIdOrMapName)
evt.SetHouseExitPic(houseId, imageId)
```

MM7 overlays unblocked:

- `7out13`: event/house 82 enters Adventurer's Inn house 1607.
- `7out04`: Clanker's Lab house 395 exit map/pic changes when QBit 710 is set.

Implementation notes:

- For simple map house entry, prefer `ReplaceMapEvent(... evt.EnterHouse(...))`.
- Exit-map/pic mutation should be a runtime override layered on top of `house_exits.txt`.

### 17. Dialogue Offer / Promotion Helpers

Needed OpenYAMM API:

```lua
evt.PromoteCharacter(memberIndex, classId)
evt.SetNpcTopicSlot(npcId, slot, topicId)
evt.ClearNpcTopicSlot(npcId, slot)
evt.ShowNpcText(textId)
```

Current state:

- `evt.SetNPCTopic` and messages exist.
- Promotion/class changes are partly possible through variables, but promotion flows need robust helpers.

MM7 overlays unblocked:

- `PromotionTopics.lua`: Antagarich promotion rewrites.
- `Quest_DragonHatchling.lua`: later roster/party-member flow.

Implementation notes:

- This is not first-wave map fixup work. Port promotion families after map overlays and followers.

### 18. Roster / Party Member Lifecycle API

Needed OpenYAMM API:

```lua
evt.HasFreeRosterSlot() -> bool, rosterId
evt.GenerateRosterMember(rosterId, spec)
evt.HireRosterMember(rosterId)
evt.DismissRosterMember(memberIndex)
evt.GetPartySize() -> count
```

MM7 overlays unblocked:

- `Quest_DragonHatchling.lua`: hatchling becomes named dragon party member/follower.
- Some MMerge mercenary/follower content later.

Implementation notes:

- Defer until original MM7 map/quest parity is stable.

## Suggested Implementation Order

1. **Small map overlay unblockers**
   - NPC enter/exit hooks
   - named persistent vars
   - party position/state accessors
   - mouse item API
   - per-member inventory/equipment checks
2. **Outdoor and house behavior**
   - outdoor edge travel hook
   - house/shop topic filter/click hooks
   - rest food cost hook
   - transport route override
3. **Map runtime edge cases**
   - action/item-use blocking hook
   - map refill hook
   - party face override
   - local relation override cleanup/semantics
4. **Large global quest systems**
   - promotion helpers
   - roster/party member lifecycle
   - richer named global structured vars if CrossContinents/Dragon Hatchling are in scope

## First Slice Recommendation

For the first implementation slice, expose only:

- `RegisterNpcEnterHook` / `RegisterNpcExitHook`
- `evt.GetPartyPosition`
- `evt.GetEnemyDetectorState`
- `evt.GetCurrentMapName`
- `evt.GetHeldItemId`, `evt.SetHeldItem`, `evt.ClearHeldItem`
- `evt.PartyMemberHasItem`, `evt.PartyMemberHasEquippedItem`, `evt.GetPartyMemberCount`
- scalar `evt.GetMapVar` / `evt.SetMapVar` and `evt.GetGlobalVar` / `evt.SetGlobalVar`
- `RegisterOutdoorEdgeTravelHook`
- `RegisterRestFoodCostHook`

That unblocks most non-CrossContinents MM7 map overlays without committing to the full promotion/roster/custom quest
surface.
