# Decompiled Event Semantic Catalog

Generated from `OpenMM8_Data/DecompiledScripts/*`.

## Operations

| Operation | Count |
| --- | ---: |
| `Exit` | 6583 |
| `SetDoorState` | 3317 |
| `Cmp` | 1234 |
| `OpenChest` | 1200 |
| `GoTo` | 1146 |
| `Add` | 1090 |
| `SetMessage` | 764 |
| `EnterHouse` | 718 |
| `Set` | 394 |
| `Subtract` | 326 |
| `OnLeaveMap` | 300 |
| `OnLoadMap` | 287 |
| `StatusText` | 232 |
| `SetNPCTopic` | 212 |
| `SetFacetBit` | 187 |
| `CanShowTopic.Set` | 168 |
| `CanShowTopic.Exit` | 166 |
| `CastSpell` | 166 |
| `MoveToMap` | 144 |
| `SetMonGroupBit` | 119 |
| `CanShowTopic.Cmp` | 98 |
| `FaceAnimation` | 95 |
| `RandomGoTo` | 73 |
| `SetTexture` | 73 |
| `PlaySound` | 63 |
| `SetLight` | 59 |
| `SummonObject` | 59 |
| `GiveItem` | 58 |
| `SummonMonsters` | 51 |
| `CheckMonstersKilled` | 44 |
| `MoveNPC` | 36 |
| `OnTimer` | 36 |
| `SetNPCGroupNews` | 27 |
| `SetNPCGreeting` | 23 |
| `ChangeEvent` | 22 |
| `CheckItemsCount` | 20 |
| `RemoveItems` | 20 |
| `SpeakNPC` | 20 |
| `SetSprite` | 10 |
| `ShowMovie` | 8 |
| `Jump` | 7 |
| `IsPlayerInParty` | 4 |
| `StopDoor` | 4 |
| `IsTotalBountyInRange` | 3 |
| `Question` | 3 |

## Variable Kinds

| Decompiled Kind | Count | Internal Tag | Authored Lua Surface | Notes |
| --- | ---: | --- | --- | --- |
| `QBits` | 1066 | `EvtVariable::QBits` | `QBit(id), IsQBitSet(id), SetQBit(id), ClearQBit(id)` | Indexed authored helper family. |
| `MapVar` | 444 | `EvtVariable::MapPersistentVariableBegin..End` | `MapVar(index)` | Indexed selector family. |
| `Inventory` | 395 | `EvtVariable::Inventory` | `InventoryItem(id), HasItem(id), RemoveItem(id), GiveItem(id)` | Indexed inventory helper family. |
| `Awards` | 247 | `EvtVariable::Awards` | `Award(id), HasAward(id), SetAward(id), ClearAward(id)` | Awards are authored as indexed ids, not raw packed numbers. |
| `AutonotesBits` | 196 | `EvtVariable::AutoNotes` | `AutonoteBit(id), IsAutonoteSet(id), SetAutonote(id), ClearAutonote(id)` | Authored API uses direct autonote helpers instead of magic packed selectors. |
| `Experience` | 171 | `EvtVariable::Experience` | `Experience` | Direct selector tag. |
| `ClassIs` | 153 | `EvtVariable::ClassId` | `ClassIs` | Decompiled name kept for authored Lua. |
| `Gold` | 134 | `EvtVariable::Gold` | `Gold` | Direct selector tag. |
| `DayOfWeekIs` | 63 | `EvtVariable::DayOfWeek` | `DayOfWeekIs` | Direct selector tag. |
| `PlayerBits` | 56 | `EvtVariable::PlayerBits` | `PlayerBit(index), IsPlayerBitSet(index), SetPlayerBit(index), ClearPlayerBit(index)` | Indexed authored helper family. |
| `SkillPoints` | 31 | `EvtVariable::NumSkillPoints` | `SkillPoints` | Direct selector tag. |
| `RepairSkill` | 22 | `EvtVariable::RepairSkill` | `RepairSkill` | Direct selector tag. |
| `History` | 20 | `EvtVariable::HistoryBegin..HistoryEnd` | `History(index)` | Indexed selector family. |
| `Counter` | 16 | `EvtVariable::Counter1..Counter10` | `Counter(index), AddToCounter(selector, value), SetCounter(selector, value)` | Indexed selector family. |
| `DiseasedGreen` | 8 | `EvtVariable::DiseasedGreen` | `DiseasedGreen` | Direct selector tag. |
| `Players` | 8 | `EvtVariable::Players` | `Player(index), HasPlayer(index)` | Roster-member indexed selector family. |
| `BankGold` | 7 | `EvtVariable::GoldInBank` | `BankGold` | Direct selector tag. |
| `BaseLuck` | 7 | `EvtVariable::BaseLuck` | `BaseLuck` | Direct selector tag. |
| `Food` | 7 | `EvtVariable::Food` | `Food` | Direct selector tag. |
| `Invisible` | 6 | `EvtVariable::Invisible` | `Invisible` | Direct selector tag. |
| `BaseEndurance` | 5 | `EvtVariable::BaseEndurance` | `BaseEndurance` | Direct selector tag. |
| `CurrentAccuracy` | 4 | `EvtVariable::ActualAccuracy` | `CurrentAccuracy` | Direct selector tag. |
| `CurrentEndurance` | 4 | `EvtVariable::ActualEndurance` | `CurrentEndurance` | Direct selector tag. |
| `CurrentIntellect` | 4 | `EvtVariable::ActualIntellect` | `CurrentIntellect` | Direct selector tag. |
| `CurrentLuck` | 4 | `EvtVariable::ActualLuck` | `CurrentLuck` | Direct selector tag. |
| `CurrentMight` | 4 | `EvtVariable::ActualMight` | `CurrentMight` | Direct selector tag. |
| `CurrentPersonality` | 4 | `EvtVariable::ActualPersonality` | `CurrentPersonality` | Direct selector tag. |
| `CurrentSpeed` | 4 | `EvtVariable::ActualSpeed` | `CurrentSpeed` | Direct selector tag. |
| `AirResistance` | 3 | `EvtVariable::AirResistance` | `AirResistance` | Direct selector tag. |
| `BaseAccuracy` | 3 | `EvtVariable::BaseAccuracy` | `BaseAccuracy` | Direct selector tag. |
| `BaseIntellect` | 3 | `EvtVariable::BaseIntellect` | `BaseIntellect` | Direct selector tag. |
| `BaseMight` | 3 | `EvtVariable::BaseMight` | `BaseMight` | Direct selector tag. |
| `BasePersonality` | 3 | `EvtVariable::BasePersonality` | `BasePersonality` | Direct selector tag. |
| `BaseSpeed` | 3 | `EvtVariable::BaseSpeed` | `BaseSpeed` | Direct selector tag. |
| `DiseasedYellow` | 3 | `EvtVariable::DiseasedYellow` | `DiseasedYellow` | Direct selector tag. |
| `EarthResistance` | 3 | `EvtVariable::EarthResistance` | `EarthResistance` | Direct selector tag. |
| `FireResistance` | 3 | `EvtVariable::FireResistance` | `FireResistance` | Direct selector tag. |
| `WaterResistance` | 3 | `EvtVariable::WaterResistance` | `WaterResistance` | Direct selector tag. |
| `Dead` | 2 | `EvtVariable::Dead` | `Dead` | Direct selector tag. |
| `FireResBonus` | 2 | `EvtVariable::FireResistanceBonus` | `FireResBonus` | Direct selector tag. |
| `HP` | 2 | `EvtVariable::CurrentHealth` | `HP` | Decompiled semantic name kept for authored Lua. |
| `HasFullHP` | 2 | `EvtVariable::MaxHealth` | `HasFullHP` | Decompiled semantic name for the full-health compare selector. |
| `HasFullSP` | 2 | `EvtVariable::MaxSpellPoints` | `HasFullSP` | Decompiled semantic name for the full-spell-points compare selector. |
| `IntellectBonus` | 2 | `EvtVariable::IntellectBonus` | `IntellectBonus` | Direct selector tag. |
| `MightBonus` | 2 | `EvtVariable::MightBonus` | `MightBonus` | Direct selector tag. |
| `PersonalityBonus` | 2 | `EvtVariable::PersonalityBonus` | `PersonalityBonus` | Direct selector tag. |
| `PoisonedYellow` | 2 | `EvtVariable::PoisonedYellow` | `PoisonedYellow` | Direct selector tag. |
| `SP` | 2 | `EvtVariable::CurrentSpellPoints` | `SP` | Decompiled semantic name kept for authored Lua. |
| `Drunk` | 1 | `EvtVariable::Drunk` | `Drunk` | Direct selector tag. |
| `PoisonedGreen` | 1 | `EvtVariable::PoisonedGreen` | `PoisonedGreen` | Direct selector tag. |

## Coverage Check

Every normalized variable kind referenced by the decompiled corpus must exist in the coverage table used by
this tool. The tool exits with a failure if any kind is missing.
