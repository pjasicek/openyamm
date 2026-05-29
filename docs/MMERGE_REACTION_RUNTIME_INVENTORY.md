# MMerge Reaction Runtime Inventory

This tracks whether MMerge character speech / face reactions have a runtime cause in OpenYAMM.

Data plumbing is in place:

- `assets_dev/engine/data_tables/character_voices.txt` is the authoritative MMerge voice table.
- `assets_dev/engine/data_tables/character_speech_events.txt` maps `SpeechId` to MMerge sound-type columns and face animations.
- `assets_dev/engine/data_tables/face_animations.txt` maps face-animation ids to portrait expressions.
- `evt.FaceAnimation(...)` supports the MMerge extended ids through `109`, so scripts can trigger any mapped reaction.

Legend:

- `Native`: emitted by a gameplay/runtime path without script help.
- `Script`: supported through `evt.FaceAnimation(...)`, but no native gameplay emitter was found.
- `Partial`: a related native feature exists, but it uses a generic reaction, house sound, status text, or face-only animation.

## Implemented Native Paths

| Reaction | Runtime cause |
| --- | --- |
| `DisarmTrap` | Chest trap disarm success queues party speech. |
| `StoreClosed` | Closed house interaction plays character reaction. |
| `TrapExploded` | Chest trap failure queues party speech. |
| `SelectCharacter` | Character creation voice preview. |
| `IdentifyWeakItem` | Item identify result for weak/useless items. |
| `IdentifyGreatItem` | Item identify result for valuable items. |
| `IdentifyFailItem` | Failed item identify. |
| `RepairSuccess` | Item repair success. |
| `RepairFail` | Item repair failure. |
| `SetQuickSpell` | Spellbook quick-spell assignment. |
| `Hungry` | Rest action with insufficient food. |
| `DamageMinor` | Party member damage. |
| `DamageMajor` | Heavy damage / low-health threshold. |
| `Dying` | Damage that drops a member to zero or lower HP. |
| `Drunk` | First acquisition of the drunk condition. |
| `Insane` | First acquisition of the insane condition. |
| `Cursed` | First acquisition of the cursed condition. |
| `Falling` | Fall-damage application path. |
| `CantRestHere` | Failed rest attempt. |
| `NotEnoughGold` | Common house, shop, guild, bank, and transport not-enough-gold failures. |
| `InventoryRoom` | Full inventory failures for shop buy, held-item placement, equipment fallback, and world pickup blocked by full pack plus occupied hand. |
| `PotionSuccess` | Potion mixing success / mapped potion success. |
| `PotionFail` | Potion mixing failure / unusable potion-like action. |
| `DoorLocked` | Event script face animation, including locked-door EVT behavior. |
| `LearnSpell` | Spellbook learning success. |
| `CantLearnSpell` | Spellbook learning failure. |
| `CantEquip` | Rejected equipment placement paths. |
| `HelloDay` | Outdoor NPC / actor greeting during daytime. |
| `HelloEvening` | Outdoor NPC / actor greeting during evening/night. |
| `KillStrongEnemy` | Combat kill reaction for strong enemy. |
| `KillWeakEnemy` | Combat kill reaction for weak enemy. |
| `LastPersonStanding` | Damage/incapacitation transition that leaves exactly one acting party member. |
| `LeaveDungeon` | Leave-dungeon dialogue/action. |
| `EnterDungeon` | Enter-map / enter-dungeon transition path. |
| `Yes` | Map-transition confirmation. |
| `ThankYou` | Temple donation and tavern tip success. |
| `Yell` | Attempted hostile actor/NPC dialogue activation. |
| `AttackHit` | Party attack hit. |
| `AttackMiss` | Party attack miss. |
| `Shoot` | Party ranged shot. |
| `CastSpell` | Party spell cast. |
| `DamagedParty` | Party-wide damage/combat events. |
| `FoundItem` | Ground/map item pickup. |
| `SkillIncreased` | Manual skill-point increase. |
| `Beg` | Successful NPC beg BTB action. |
| `BegFail` | Failed NPC beg BTB action. |
| `Threat` | Successful NPC threat BTB action. |
| `ThreatFail` | Failed NPC threat BTB action. |
| `Bribe` | Successful NPC bribe BTB action or paid bribe. |
| `BribeFail` | Failed NPC bribe BTB action. |
| `NpcDontTalk` | Generic indoor/outdoor actor dialogue target with no resolvable talk/news content. |
| `HireNpc` | Follower hire and roster-join success flows. |
| `TavernPacksFull` | Tavern food purchase when packs are already full. |
| `TavernDrink` | Tavern drink service success. |
| `TavernGotDrunk` | Tavern drink service drunk result. |
| `TavernTip` | Tavern tip service success. |
| `ShopItemBought` | Shop stock purchase success. |
| `ShopRude` | Closing a shop with very bad local reputation. |
| `SkillLearned` | House/guild learn-skill success. |
| `SkillMasteryIncreased` | Mastery teacher success. |
| `JoinedGuild` | Guild membership purchase success. |
| `QuestGot` | Quest portrait FX request. |
| `AwardGot` | Award portrait FX request. |
| `TempleHeal` | Temple healing service success. |
| `TempleDonate` | Temple donation success. |
| `TravelBoat` | Boat transport service success. |
| `TravelHorse` | Stable/coach transport service success. |
| `ShopIdentify` | Shop identify success. |
| `ShopRepair` | Shop repair success. |
| `AlreadyIdentified` | Already identified / nothing to repair in shop overlay. |
| `ItemSold` | Shop sell success. |
| `WrongShop` | Shop item-service wrong shop. |
| `BankDeposit` | Bank deposit success. |
| `LevelUp` | Training service success. |
| `Indignant` | Stat-decrease portrait FX request. |
| `StatBonusIncreased` | Stat-increase portrait FX request. |
| `StatBaseIncreased` | Base stat/resistance event increase. |
| `AfraidSilent` | First acquisition of the fear condition. |
| `CheatedDeath` | Preservation-active damage crossing to zero or lower HP. |
| `InPrison` | Prison-term event variable increase. |
| `Awaken` | Awaken spell success when at least one member was asleep. |
| `IdentifyMonsterWeak` | Monster inspect success for weaker monsters. |
| `IdentifyMonsterBig` | Monster inspect success for strong monsters. |
| `IdentifyMonsterFail` | Monster inspect failed skill check. |
| `DeathBlow` | Critical melee hit that kills the target. |
| `Poisoned` | Disease/poison portrait FX request and script face animation. |

## Partial Or Missing Native Causes

| Reaction | Status | Gap / policy |
| --- | --- | --- |
| `HelloHouse` | Script | House entry uses the house/proprietor greeting sound. Party portrait speech/fx is script-only unless a real NPC/dialogue path explicitly needs it. |

## Completed Runtime Work

- Low-risk house/service reactions: `ShopItemBought`, `SkillLearned`, `SkillMasteryIncreased`, `JoinedGuild`,
  `TavernPacksFull`, and common `NotEnoughGold`.
- NPC dialogue reactions: BTB success/failure reactions, `HireNpc`, and unresolved generic actor `NpcDontTalk`.
- Inventory/equipment failure reactions: common `InventoryRoom` and `CantEquip` paths.
- Spell and damage/condition reactions: `Awaken`, `Falling`, `Dying`, `LastPersonStanding`, `CheatedDeath`,
  `Drunk`, `Insane`, `Cursed`, and `AfraidSilent`.
- Final parity pass reactions: monster inspection, hungry/rest, tavern drink/tip, rude shop close, prison terms,
  party-wide damage, base-stat gains, transition yes, hostile yell, and critical-kill death blow.
