# Actor profiles

A world can declare `actorProfiles: actor_profiles.yml` in `world.yml`. Profiles contribute immutable base content
for particular actors without changing the shared monster table. The first consumer is Amber Island in MM7.

```yaml
schema: openyamm.actorProfiles.v1
profiles:
  mm7.encounter_healer:
    monster: 59
    name: Encounter Healer
    spell1: {id: 77, chance: 11, skill: 5, mastery: 4}
    spell2: {id: 37, chance: 15, skill: 10, mastery: 2}
    attack1_element: Earth
  mm7.friendly_captive:
    monster: 405
    party_damage_reaction: stay_friendly
map_defaults:
  encounter.blv: [mm7.encounter_healer]
```

Each profile starts with its mounted `monster` row. It may replace `name`, `on_hit` (`none` or `poison1`), either
spell slot, either attack element, and the reaction to party damage (`retaliate`, the default, or `stay_friendly`).
Spell ids come from the mounted spell table, chance is 0–100 percent, skill is 1–255, and mastery is 1–4. An explicit
`{id: 0, chance: 0, skill: 0, mastery: 0}` clears a slot; an omitted slot keeps the base monster's spell. Attack
elements use `Physical`, `Fire`, `Air`, `Water`, `Earth`, `Spirit`, `Mind`, `Body`, `Light`, `Dark`, or `Energy`.
Unknown fields, invalid values, duplicate ids/defaults and missing references reject the contribution atomically.
Profile ids must begin with the contributing world id and a dot. The file path stays inside that world's package.

Bind a placed actor with `actor_profile: mm7.encounter_healer` in its scene actor entry. For Lua summons use
`evt.SummonMonstersById{monster = 59, profile = "mm7.encounter_healer", ...}`. A profile has one monster id; an invalid
id/profile pairing cannot spawn. Map defaults apply to newly generated spawn-point and event actors. Explicit
profiles take priority. Unique NPC names from `place_mon.txt` take priority over a profile's species name.

The indoor and outdoor runtimes resolve the profile before ruleset calculation, AI, inspection and combat. Profiles
own these base fields; the ruleset still owns scaling, generated abilities, boss rolls and modifiers. Native AI casts
healing, buffs and offensive spells through its existing two slots. A profile does not apply a permanent buff, run
a Lua timer, or replace the actor's current health/effects. Refresh and re-entry follow the ordinary ruleset paths.
The AI uses normalized spell names, as the stock monster parser does. Healing and self buffs use the authored
spell chance during combat, including melee: they do not need an offensive ranged-distance roll or a clear shot
at the opponent. Blindness and Dark Grasp retain their normal restrictions. Offensive spells keep their existing
range, line-of-sight and commitment checks. Ordinary map re-entry still heals living monsters to full health;
loading a save or refreshing a profile does not add a heal or stack an existing buff.

`stay_friendly` suppresses party-provoked hostility and faction retaliation. The actor still takes ordinary damage,
hit reactions and death. Breaking fear/control on a hit still removes those effects, while preserving the actor's
prior relation. A nearby faction member being hit also cannot provoke this actor. Authored hostility changes remain
available to events; the policy does not change the global relation of every monster of that kind.

Amber's captive Greene additionally receives `mm7/amber_greene` from the Watchtower map's on-load hook. This
world-local actor behavior uses the existing `self:setInvulnerable(true)` on start/load, independently of the
profile's friendly reaction policy. It has no monster-id default: other knights remain mortal. Rescue still
removes the captive normally. The protection is an explicit user-requested change after a bat killed him in play.
His authored scene also uses private neutral Ally 9538 (Amber's 9000 + source NPC id convention), so he and other
monsters do not select each other as combat targets. This preserves the party's kills instead of adding an
invulnerable combat ally. The converter binds this allegiance only to Greene; use a fresh Watchtower visit to check it.

Save version 143 stores profile identity on `MapDeltaActor` and outdoor runtime actors. Indoor AI reconstructs its
static profile fields from the map actor after load; existing HP, ruleset facts and buff timers use their existing
serialization. Old Amber actors are not migrated or assigned profiles from their merged monster ids.

Amber's converter imports `tools/amber_actors/profiles.py` and keeps its original-kind/index map until scene export.
This distinguishes troll warriors (original 292–294) from plain trolls (250–252), which share merged ids 58–60.
Only the warriors receive the healing/spell profiles. Map defaults for lizards and pirates are limited to Amber's
twelve maps; the stock MM7/MM8 monsters keep their original rows. Michael's duel assigns his profile explicitly.

Coverage lives in `ActorProfileTests`, `IndoorActorFactionRuntimeTests`, `EventScriptingTests`, the Amber scenarios,
and `python -m unittest tools.amber_actors.test_profiles`. The native world fixtures belong to
`openyamm_runtime_tests`; the API and scenario-schema checks belong to `openyamm_unit_tests`.
