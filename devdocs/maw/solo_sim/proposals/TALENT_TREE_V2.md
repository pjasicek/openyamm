# Solo run talent tree v2: proposal for simulation (2026-11-14)

The user's direction (SOLO_RULES.md §6, 2026-11-14):
- The solo rules become talents of the MAW solo run (`assets_dev/engine/data_tables/talents.yml`), except
  Bodybuilding, which is innate.
- The largest effects are **keystones**, rare slots, not ordinary ranks.
- No Legend lines and no Legend points (user, 2026-11-14): talents only. The grinding power curve has to come
  from items and crafting (ITEMS_AND_CRAFTING.md), not from points.
- Casters need their own answer.
- Nothing ships before calibration.

The machine-readable copy of this page is [talents_v2.py](../scripts/talents_v2.py); the simulation reads that file.
Numbers are first values to simulate, not final.

## Points

| Source | Points |
| --- | --- |
| Levels | 1 per 15 levels (user, 2026-11-14; the current tree has 1 per 10) |
| Keystone slots | one per 150 levels: at levels 150, 300, 450, 600 and 750 |

The budget by level:

| Level | Points | Keystone slots |
| --- | --- | --- |
| 10 | 0 | 0 |
| 50 | 3 | 0 |
| 200 | 13 | 1 |
| 500 | 33 | 3 |
| About 800, end of Beyond Madness | 53 | 5 |

The whole tree costs about 65 points (level 975). One tree's rows cost about 20, so a character fills its main tree
by about level 300 and has a dozen points for the other trees at level 500.

## Innate (no points)

**Dragon items ×3 (×2.5 reverted).** A solo Dragon's items count three times, as in MAW. The 2.5 times of 2026-11-14 was
reverted by the user on 2026-11-15 (`MawItemRules::applyEquippedEnchantEffects`).

**Lone Discipline.** A solo character trains Bodybuilding one mastery above its class cap after its first promotion,
and to Grandmaster after its final one.

## Talents

Existing talents are unchanged unless marked. **New** rows are this proposal.

**Arms** (weapon fighting; was "Melee")

| Talent | Ranks | Effect |
| --- | --- | --- |
| Weapon Training | 5 | +2 % Might, Endurance and Speed per rank |
| Cleave (active) | 3 | **A burst** (user, 2026-11-14): 150 % to everything in the 120° arc in front (±60°) and a 1 s stagger, cooldown 12/10/8 s |
| ~~Whirlwind~~ | – | **Dropped** (user, 2026-11-14): with Sweeping Blows it fired about once a minute and added nothing. |
| **Onslaught** (passive, replaces the active Frenzy; user 2026-11-14) | 3 | Each kill adds a stack of +1 % attack speed, at most 10 / 20 / 30 stacks (+10 / 20 / 30 %); the stacks last 30 s and every kill refreshes them, so they carry from one pull into the next. By design it adds little to slow pulls and pays off only when kills chain (user, 2026-11-14) |
| Charge (active) | 3 | Dash to the target, a blow, stagger 1.5 s, cooldown 25/22/19 s |
| Shield Wall (active) | 3 | With a shield: 50 % less damage for 6 s, cooldown 60/50/40 s |
| **Sweeping Blows** (new) | 3 | Every swing also strikes 1 / 2 / 3 more monsters in the same 120° arc at 30 % + 0.25 % per weapon-skill point, **at most 50 %** (user, 2026-11-14: a built-in passive stays below the active). Needs Cleave. |

**Archery** (bow; was "Ranged"). Bows only: none of these touch a Dragon's breath (user, 2026-11-14).

| Talent | Ranks | Effect |
| --- | --- | --- |
| Marksman | 5 | +2 % Accuracy and Speed per rank |
| **Multishot** (replaces Volley, user 2026-11-14) | 3 | A shotgun: 2 / 3 / 4 bow attacks at once across a ±30° cone, 75 % each (with Grandmaster Bow each attack carries its extra arrow, as normal). Every arrow hits the first monster in its line: point-blank all land on the target, against a spread group they split. Cooldown 12/10/8 s. |
| Disengage (active) | 3 | Leap back 420, cooldown 15/13/11 s |
| Pinning Shot (active) | 3 | A shot that halves the target's speed for 4/5/6 s, cooldown 10 s |
| Steady Aim | 3 | +5 % Luck per rank while still (was 3 %, user 2026-11-14) |
| **Piercing Arrows** (new) | 3 | Each arrow continues to 1 / 2 / 3 monsters behind the target at 50 % |

**Arcana** (spells; was "Caster")

| Talent | Ranks | Effect |
| --- | --- | --- |
| Attunement | 5 | +2 % Intellect, Personality, Endurance, spell damage and healing per rank |
| Blink (active) | 3 | Teleport 1600 forward, cooldown 15/13/11 s |
| Spell Surge (active) | 3 | The next spell is free and hits 50 % harder, cooldown 45/40/35 s |
| ~~Mana Font~~ | – | **Dropped** (user, 2026-11-14) |
| ~~Purify~~ | – | **Dropped** (user, 2026-11-14) |
| Resolve | 5 | +2 % to all resistances per rank |
| **Overload** (new) | 3 | Area spells +10 / 20 / 30 % per monster hit beyond the first (at most 3 more) |
| **Binding Circle** (new, active) | 3 | Roots every monster within 500 for 2 / 2.5 / 3 s, cooldown 20/18/16 s. It is the caster's window to Blink or cast. |

**Any tree**

| Talent | Ranks | Effect |
| --- | --- | --- |
| **Bloodthirst** (new) | 3 | +2 % leech on melee, ranged and spells per rank. The leech floor's ÷5 becomes ÷4 / ÷3 / ÷2.5, counted once per swing or cast, not per struck monster. |

## Keystones (one per slot, chosen from a short list)

The trees name what they train, not a role: points mix freely (user, 2026-11-14). A tree's keystone needs 10 points
spent in that tree; Unbroken is open to all; the Oath is the class's own.

| Keystone | Who | Effect |
| --- | --- | --- |
| **Unbroken** | all | The part of one landed hit above 30 % of max HP is halved |
| **Oath** | per class | The class's identity cut or gain (below) |
| **Warlord** | 10 points in Arms | Sweeping Blows always at its 50 % cap with one more monster |
| **Deadeye** | 10 points in Archery | +30 % bow damage (not a Dragon's breath); Piercing Arrows at 75 % |
| **Archon** | 10 points in Arcana | Mana Shield absorbs 10 HP per SP instead of 5 once the skill is at its cap of 50 |

**What an Oath is.** Every class except the Death Knight gets one Oath: a keystone that only its class can take, and the one that matters
most in the simulation. MAW never lets armour and resistances cut a hit below 10 % of its raw damage (its 90 %
reduction cap). At Beyond Madness level 500, melee characters already sit on that floor, so more armour or resistance
does nothing. Most Oaths are a cut that comes *after* that floor, so every landed hit is smaller (the Knight line's
Juggernaut takes 30 % off while it is fighting).

The classes whose defence already holds (Troll, Dragon) get damage instead. Everything after the floor together stays
at or above ×0.25.

**Oaths** (the after-floor cuts of TALENTS M1/M4):

| Class | Oath | Effect |
| --- | --- | --- |
| Knight line (Champion) | Juggernaut | ×0.7 damage taken after the floor while it struck in the last 2 s |
| Minotaur | Juggernaut | the same |
| Monk | Inner Peace | ×0.75 damage taken after the floor |
| Death Knight | – | **No Oath** (Lichborne removed, user 2026-11-14): its keystones are Unbroken and the tree keystones |
| Seraph | Sanctified | ×0.7 damage taken after the floor |
| Vampire | Night Lord | ×0.7 damage taken after the floor |
| Troll | Unstoppable | +30 % damage |
| Dragon | Elder Wyrm | +30 % damage |
| Archer | Ranger | ×0.7 damage taken after the floor while no monster is adjacent |
| Shaman | Storm Ward | Air's cut acts after the floor (×0.59) |
| Assassin | Shadow | ×0.75 damage taken after the floor |
| Arch Mage, Elementalist, Priest | Elemental Ward | ×0.55 magic damage taken after the floor |

**Shared clamp:** everything after the floor together never goes below ×0.25 (Oath × Shield Wall ×
Unbroken's part).

## What the simulation must answer

- Does each build reach the targets (SOLO_RULES.md §4, POWER_GAP)?
- Do Nightmare and Doom stay sensible?
- Which keystone combinations are outliers?
- How much does range (approach, Blink, Disengage, Pinning Shot, Binding Circle) give casters and the Archer?
