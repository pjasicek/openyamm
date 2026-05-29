# Party Member Loop Export Audit

This file was created before code or script changes for the party-member loop export fix.

Goal: replace generated MM6/MM7 four-member-only script patterns with party-size-aware forms, without changing
event intent. The target party-size-aware primitive is expected to iterate runtime party members `0..memberCount - 1`
using `evt.GetPartyMemberCount()`.

## Normalized Four-Member Loops

Old generated shape:

```lua
for _, player in ipairs({Players.Member0, Players.Member1, Players.Member2, Players.Member3}) do
    evt.ForPlayer(player)
    ...
end
```

Expected shape:

```lua
for _, player in ipairs(PartyMembers()) do
    evt.ForPlayer(player)
    ...
end
```

Occurrences:

- `assets_dev/worlds/mm6/events/maps/6d04.lua:178`
- `assets_dev/worlds/mm6/events/maps/6d04.lua:292`
- `assets_dev/worlds/mm6/events/maps/6d04.lua:322`
- `assets_dev/engine/events/Global.lua:7547`
- `assets_dev/engine/events/Global.lua:7584`
- `assets_dev/engine/events/Global.lua:7650`
- `assets_dev/engine/events/Global.lua:7686`
- `assets_dev/engine/events/Global.lua:7726`
- `assets_dev/engine/events/Global.lua:7799`
- `assets_dev/engine/events/Global.lua:7831`
- `assets_dev/engine/events/Global.lua:7869`
- `assets_dev/engine/events/Global.lua:7927`
- `assets_dev/engine/events/Global.lua:7984`
- `assets_dev/engine/events/Global.lua:8020`
- `assets_dev/engine/events/Global.lua:8057`
- `assets_dev/engine/events/Global.lua:8116`
- `assets_dev/engine/events/Global.lua:8147`
- `assets_dev/engine/events/Global.lua:8182`
- `assets_dev/engine/events/Global.lua:8230`
- `assets_dev/engine/events/Global.lua:8283`
- `assets_dev/engine/events/Global.lua:8303`
- `assets_dev/engine/events/Global.lua:8399`
- `assets_dev/engine/events/Global.lua:8431`
- `assets_dev/engine/events/Global.lua:8472`
- `assets_dev/engine/events/Global.lua:8501`
- `assets_dev/engine/events/Global.lua:8521`
- `assets_dev/engine/events/Global.lua:8564`
- `assets_dev/engine/events/Global.lua:8960`
- `assets_dev/engine/events/Global.lua:9006`
- `assets_dev/engine/events/Global.lua:9058`
- `assets_dev/engine/events/Global.lua:13389`
- `assets_dev/engine/events/Global.lua:13423`
- `assets_dev/engine/events/Global.lua:13585`
- `assets_dev/engine/events/Global.lua:13606`
- `assets_dev/engine/events/Global.lua:13801`
- `assets_dev/engine/events/Global.lua:13829`
- `assets_dev/engine/events/Global.lua:13916`
- `assets_dev/engine/events/Global.lua:13942`
- `assets_dev/engine/events/Global.lua:14149`
- `assets_dev/engine/events/Global.lua:14209`
- `assets_dev/engine/events/Global.lua:16774`
- `assets_dev/engine/events/Global.lua:16794`

Semantic check after change:

- Same loop order for existing four-member parties: 0, 1, 2, 3.
- Fifth member is included only when present at runtime.
- Loop body remains unchanged except for the source of the `player` values.

## Ugly Unrolled Member0-Member3 Sequences

Old generated shape:

```lua
evt.ForPlayer(Players.Member0)
...
evt.ForPlayer(Players.Member1)
...
evt.ForPlayer(Players.Member2)
...
evt.ForPlayer(Players.Member3)
...
```

Target shape depends on control flow:

- Repeated per-member effects: use `for _, player in ipairs(PartyMembers()) do`.
- First matching inventory trade/buyer: use `for _, player in ipairs(PartyMembers()) do` and keep the first-match
  `return` behavior.
- Whole-party punishments: use `for _, player in ipairs(PartyMembers()) do` and apply the condition to each member.
- Special altar sequences must preserve their original per-member stat reward intent while making member selection
  runtime-sized.

Occurrences:

- `assets_dev/worlds/mm6/events/maps/6d13.lua:179`
- `assets_dev/worlds/mm6/events/maps/6d13.lua:195`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:88`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:121`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:150`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:184`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:218`
- `assets_dev/worlds/mm6/events/maps/6t5.lua:250`
- `assets_dev/worlds/mm7/events/maps/7d23.lua:741`
- `assets_dev/engine/events/Global.lua:258`
- `assets_dev/engine/events/Global.lua:274`
- `assets_dev/engine/events/Global.lua:8612`
- `assets_dev/engine/events/Global.lua:8664`
- `assets_dev/engine/events/Global.lua:9665`
- `assets_dev/engine/events/Global.lua:9758`
- `assets_dev/engine/events/Global.lua:9879`
- `assets_dev/engine/events/Global.lua:9970`
- `assets_dev/engine/events/Global.lua:15367`
- `assets_dev/engine/events/Global.lua:15400`
- `assets_dev/engine/events/Global.lua:15437`
- `assets_dev/engine/events/Global.lua:15470`
- `assets_dev/engine/events/Global.lua:15503`
- `assets_dev/engine/events/Global.lua:15536`
- `assets_dev/engine/events/Global.lua:15569`
- `assets_dev/engine/events/Global.lua:15602`
- `assets_dev/engine/events/Global.lua:15635`
- `assets_dev/engine/events/Global.lua:15710`
- `assets_dev/engine/events/Global.lua:15742`
- `assets_dev/engine/events/Global.lua:15774`
- `assets_dev/engine/events/Global.lua:15806`
- `assets_dev/engine/events/Global.lua:15838`
- `assets_dev/engine/events/Global.lua:15870`
- `assets_dev/engine/events/Global.lua:15903`
- `assets_dev/engine/events/Global.lua:16361`

## Exporter Implementation

Generated Lua scripts were not edited directly. The change is in the Lua exporter and common event support:

- `event_support.lua` now exports `PartyMembers()`, which returns runtime party member ids from
  `evt.GetPartyMemberCount()`.
- Normalized exporter party-member loops that previously emitted `{Players.Member0, ... Players.Member3}` now emit
  `PartyMembers()`.
- A final exporter compatibility rewrite handles generated unrolled `evt.ForPlayer(Players.MemberN)` blocks:
  identical `Member0..Member3` blocks become a single `PartyMembers()` loop; optional identical `Member4` or
  `Players.Current` tails are consumed so the current player is not rewarded twice.
- The MM6 altar luck exception is preserved explicitly: member 0 keeps the old `+2 BaseLuck` reward and all other
  runtime party members get `+5 BaseLuck`.
- The MM7 Lincoln wetsuit gate is rewritten from nested fixed-member checks to a runtime all-members check.
- The MM7 lich ritual step-machine output is rewritten to party-size-aware jar validation, promotion, jar cleanup,
  reward, topic, and greeting logic.

## Post-Change Semantic Review

Normalized loop occurrences:

- Old behavior on a four-member party is unchanged: iteration order remains member 0, 1, 2, 3.
- New behavior includes member 4 only when `evt.GetPartyMemberCount()` reports that member exists.
- The original loop body is otherwise unchanged.

Ugly unrolled occurrences:

- `6d13.lua:179` and `6d13.lua:195`: both altar class checks remain per-member checks with the same class
  thresholds and `+5 BasePersonality` reward. The second old block's `evt.ForPlayer(Players.All)` reset is emitted
  after the dynamic loop, preserving the original selected-player cleanup.
- `6t5.lua:88`, `6t5.lua:121`, `6t5.lua:150`, `6t5.lua:184`, `6t5.lua:218`: repeated stat rewards are emitted as
  one runtime party loop. The old `Players.Current` tail is consumed, which avoids double-awarding the current
  player and extends the reward to member 4.
- `6t5.lua:250`: the special luck altar remains asymmetric: member 0 gets `+2 BaseLuck`; every other runtime party
  member gets `+5 BaseLuck`.
- `7d23.lua:741`: the Lincoln exit still requires every checked member to have a wetsuit before moving to Shoals.
  The checked set is now the runtime party instead of hardcoded members 0-3 plus current.
- `Global.lua:258` and `Global.lua:274`: identical per-member item grant blocks are handled by the same sequential
  block rewrite, including an optional existing member 4 tail if the source emits one.
- `Global.lua:8612` and `Global.lua:8664`: the lich ritual now requires every runtime party member to hold a Lich
  Jar, then applies the same class-dependent Lich/Honorary Lich promotion and experience rewards to every runtime
  party member. The follow-up quest clear, lost-jar clear, gold/reputation changes, all-party jar removal loop, NPC
  topic clear, and greeting change are preserved.
- `Global.lua:9665`, `Global.lua:9758`, `Global.lua:9879`, `Global.lua:9970`, and `Global.lua:16361`: execution
  punishment blocks remain the same `SetValue(Eradicated, 1)` effect, now over the runtime party.
- `Global.lua:15367` through `Global.lua:15903`: item buyer/trader blocks keep first-match behavior. The generated
  loop checks members in order, performs the same remove/reward/message/random branch body, and the existing `return`
  still exits the event immediately after the first successful trade. Failure messages remain after the loop.

Tests added:

- MM6 6T5 repeated altar rewards emit `PartyMembers()` and no hardcoded `Member0`/`Players.Current` tail.
- MM6 6T5 luck altar keeps the `+2` first-member exception while removing the `Players.Current` tail.
- MM7 7d23 Lincoln wetsuit check emits an all-runtime-party loop.
- MM7 Global event 847 lich ritual emits dynamic jar validation, promotion, jar cleanup, and final state updates.
