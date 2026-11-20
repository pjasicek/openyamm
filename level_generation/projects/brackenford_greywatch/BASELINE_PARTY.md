# Ordinary MM8 test party and encounter placement

The driver asked on 2026-09-06 to use comparable dungeons for a reasonable first placement and leave final balance
tuning to them. Combat observations below validate actual gameplay input and reveal placement issues; they do not
certify difficulty or require every fixture to win without healing or movement.

## Party source and setup

[source/baseline_party.json](source/baseline_party.json) is the canonical five-member level-25 fixture. Generate the
scenarios with `python3 level_generation/projects/brackenford_greywatch/build_baseline_tests.py`. A scenario selects
this fresh party through `new_game_flow.party`; it does not inherit the development party's level-200 Grandmaster
skills. Start records include class, level, health, mana and skill counts. Equipment is installed through the shared
class/race/equipment restrictions, and skill mastery is checked against the merged class/race tables.

| Member | Main equipment, original MM8 item IDs | Skills | Starting HP / SP |
| --- | --- | --- | --- |
| Knight | Templar Sword 4, shield 101, crossbow 64, plate 96 | Sword 7; other listed skills 4–7, Expert | 260 / 0 |
| Cleric | Reverend Sceptre 69, shield 101, chain 91 | Mace 7, Body Magic 7, Meditation 7; Expert | 90 / 153 |
| Dark Elf | Dark Elven Longsword 3, Elven Warbow 59, chain 91 | Sword/Bow/Disarm/Perception 7; Expert | 115 / 66 |
| Minotaur | Dwarven Battleaxe 34, crossbow 64, chain 91 | Axe/Body Building 7; other skills 4, Expert | 214 / 33 |
| Necromancer | Serpent Staff 82, leather 86 | Fire/Water/Meditation 7; other skills 4, Expert | 80 / 163 |

Shared ordinary gear uses MM8 IDs 111 (helm), 119 (belt), 124 (cloak), 129 (gauntlets), 134 (boots), where the doll
supports the slot. The Minotaur has no helm or boots. Gear has no generated enchantments. Portrait rows are the
original MM8 Knight, Cleric, Dark Elf, Minotaur and Necromancer selections; exact portrait/race IDs and attributes are
in the JSON. Starting gold is 50,000 and food is 40. Known spells are existing MM8 spells, with no custom definitions.

The isolated stage explicitly disables immortality, unlimited mana and the god-lich start, with movement multiplier
one. Each member is initialized with normal full resources. Normal damage and recovery remain active afterwards;
there is no recurring heal, invulnerability, invisibility or scripted damage against enemies.

`baseline_party_smoke.yml` checks actual equipped items before and after a native save/load, all five levels, and
current HP bounds. `verify_baseline_party.py` checks rejected classes, skills, equipment, zero/overflow levels,
impossible health assertions and invalid action durations. Reports are under `review/`.

## Placement rationale

[Naga Vault](../../case_studies/indoor/mm8_d18.md) has 14 occupied sectors, 18 spawn records, four initial fixed actors,
and several door events which summon additional enemies. Those counts describe different kinds of population and
must not be added as an exact simultaneous monster count. Its useful pattern is a sequence of guarded chambers,
bent passages and controlled openings. [Ilsingore's Cave](../../case_studies/indoor/mm8_d48.md) supplies the rough lower
approach language. Greywatch uses original geometry and fixed, reproducible MM8 mercenary placements.

Greywatch retains 24 actors, with 2–4 in ordinary defended chambers and five captains in the final vault. Both arrival
rooms and the upper lift landing start empty. There are two armory guards, four watch-hall guards, two gallery guards,
four records defenders, four barracks defenders, three at the lower junction and five in the vault. The existing
Human Mercenary A/B/C definitions supply all combat statistics. No shared monster table is modified.

Initial testing in the middle of records drew the barracks and lower-junction groups into the same encounter. Doors
7 and 8 now separate those approaches, while preserving every actor ID and the first six mechanism IDs. They begin
closed and have controls on both sides. The lift gate separates the final area. Nearby actors can still become alert
or pursue within their reachable space; a closed door is not a promise that they are unaware of the party.

`greywatch_entrance_combat.yml` holds the real shared Attack action at the entrance, earns experience and records
actual actor/party state. The records scenario is an observation fixture, starting inside that room; it is not a
continuous dungeon playthrough. Stationary attack-only observations can leave wounded or unconscious members, and
low-health enemies can retreat out of the aim cone. These observations are retained for the driver's balance pass.

`greywatch_encounter_doors.yml` checks closed world collision, both sets of fixed controls, and saved open state with
normal AI and collision enabled. It does not claim a complete combat route or open-door actor clearance. Existing
lift, control and trap tests remain separate functional checks. The final segmented route, trap, lighting and reward results are indexed in [ACCEPTANCE.md](ACCEPTANCE.md).
Four watch mercenaries crossed the opened entrance door; six records/junction enemies were defeated. The open-gate
lift and both-direction lower stair/shortcut routes pass with normal collision and active actors.
