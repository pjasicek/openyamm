eventSupport = eventSupport or {}

local support = eventSupport

support.varTag = support.varTag or {
    Sex = 0x0001,
    ClassId = 0x0002,
    Awards = 0x000C,
    Experience = 0x000D,
    Race = 0x000E,
    QBits = 0x0010,
    Inventory = 0x0011,
    ClassIs = 0x0002,
    Hour = 0x0012,
    DayOfYear = 0x0013,
    CurrentHealth = 0x0003,
    HP = 0x0003,
    MaxHealth = 0x0004,
    HasFullHP = 0x0004,
    CurrentSpellPoints = 0x0005,
    SP = 0x0005,
    MaxSpellPoints = 0x0006,
    HasFullSP = 0x0006,
    ActualArmorClass = 0x0007,
    ArmorClassBonus = 0x0008,
    BaseLevel = 0x0009,
    LevelBonus = 0x000A,
    Age = 0x000B,
    DayOfWeek = 0x0014,
    DayOfWeekIs = 0x0014,
    Gold = 0x0015,
    RandomGold = 0x0016,
    Food = 0x0017,
    RandomFood = 0x0018,
    MightBonus = 0x0019,
    IntellectBonus = 0x001A,
    PersonalityBonus = 0x001B,
    EnduranceBonus = 0x001C,
    SpeedBonus = 0x001D,
    AccuracyBonus = 0x001E,
    LuckBonus = 0x001F,
    BaseMight = 0x0020,
    BaseIntellect = 0x0021,
    BasePersonality = 0x0022,
    BaseEndurance = 0x0023,
    BaseSpeed = 0x0024,
    BaseAccuracy = 0x0025,
    BaseLuck = 0x0026,
    ActualMight = 0x0027,
    CurrentMight = 0x0027,
    ActualIntellect = 0x0028,
    CurrentIntellect = 0x0028,
    ActualPersonality = 0x0029,
    CurrentPersonality = 0x0029,
    ActualEndurance = 0x002A,
    CurrentEndurance = 0x002A,
    ActualSpeed = 0x002B,
    CurrentSpeed = 0x002B,
    ActualAccuracy = 0x002C,
    CurrentAccuracy = 0x002C,
    ActualLuck = 0x002D,
    CurrentLuck = 0x002D,
    FireResistance = 0x002E,
    AirResistance = 0x002F,
    WaterResistance = 0x0030,
    EarthResistance = 0x0031,
    SpiritResistance = 0x0032,
    MindResistance = 0x0033,
    BodyResistance = 0x0034,
    LightResistance = 0x0035,
    DarkResistance = 0x0036,
    PhysicalResistance = 0x0037,
    MagicResistance = 0x0038,
    FireResistanceBonus = 0x0039,
    AirResistanceBonus = 0x003A,
    WaterResistanceBonus = 0x003B,
    EarthResistanceBonus = 0x003C,
    SpiritResistanceBonus = 0x003D,
    MindResistanceBonus = 0x003E,
    BodyResistanceBonus = 0x003F,
    LightResistanceBonus = 0x0040,
    DarkResistanceBonus = 0x0041,
    PhysicalResistanceBonus = 0x0042,
    MagicResistanceBonus = 0x0043,
    FireResBonus = 0x0039,
    StaffSkill = 0x0044,
    SwordSkill = 0x0045,
    DaggerSkill = 0x0046,
    AxeSkill = 0x0047,
    SpearSkill = 0x0048,
    BowSkill = 0x0049,
    MaceSkill = 0x004A,
    BlasterSkill = 0x004B,
    ShieldSkill = 0x004C,
    LeatherSkill = 0x004D,
    ChainSkill = 0x004E,
    PlateSkill = 0x004F,
    FireSkill = 0x0050,
    AirSkill = 0x0051,
    WaterSkill = 0x0052,
    EarthSkill = 0x0053,
    SpiritSkill = 0x0054,
    MindSkill = 0x0055,
    BodySkill = 0x0056,
    LightSkill = 0x0057,
    DarkSkill = 0x0058,
    IdentifyItemSkill = 0x0059,
    MerchantSkill = 0x005A,
    RepairSkill = 0x005B,
    BodybuildingSkill = 0x005C,
    MeditationSkill = 0x005D,
    PerceptionSkill = 0x005E,
    DiplomacySkill = 0x005F,
    ThieverySkill = 0x0060,
    DisarmTrapSkill = 0x0061,
    DodgeSkill = 0x0062,
    UnarmedSkill = 0x0063,
    IdentifyMonsterSkill = 0x0064,
    ArmsmasterSkill = 0x0065,
    StealingSkill = 0x0066,
    AlchemySkill = 0x0067,
    LearningSkill = 0x0068,
    Cursed = 0x0069,
    Weak = 0x006A,
    Asleep = 0x006B,
    Afraid = 0x006C,
    Drunk = 0x006D,
    Insane = 0x006E,
    PoisonedGreen = 0x006F,
    DiseasedGreen = 0x0070,
    PoisonedYellow = 0x0071,
    DiseasedYellow = 0x0072,
    PoisonedRed = 0x0073,
    DiseasedRed = 0x0074,
    Paralyzed = 0x0075,
    Unconscious = 0x0076,
    Dead = 0x0077,
    Stoned = 0x0078,
    Eradicated = 0x0079,
    MajorCondition = 0x007A,
    MapPersistentVariableBegin = 0x007B,
    MapPersistentVariableEnd = 0x00C5,
    MapVarBegin = 0x007B,
    MapVarEnd = 0x00C5,
    MapPersistentDecorVariableBegin = 0x00C6,
    MapPersistentDecorVariableEnd = 0x00DE,
    DecorVarBegin = 0x00C6,
    DecorVarEnd = 0x00DE,
    AutoNotes = 0x00DF,
    AutonotesBits = 0x00E1,
    IsMightMoreThanBase = 0x00E0,
    IsIntellectMoreThanBase = 0x00E1,
    IsPersonalityMoreThanBase = 0x00E2,
    IsEnduranceMoreThanBase = 0x00E3,
    IsSpeedMoreThanBase = 0x00E4,
    IsAccuracyMoreThanBase = 0x00E5,
    IsLuckMoreThanBase = 0x00E6,
    PlayerBits = 0x00E7,
    Npcs2 = 0x00E8,
    IsFlying = 0x00F0,
    HiredNpcHasSpeciality = 0x00F1,
    CircusPrises = 0x00F2,
    Counter1 = 0x00F5,
    NumSkillPoints = 0x00F3,
    MonthIs = 0x00F4,
    SkillPoints = 0x00F3,
    Counter2 = 0x00F6,
    Counter3 = 0x00F7,
    Counter4 = 0x00F8,
    Counter5 = 0x00F9,
    Counter6 = 0x00FA,
    Counter7 = 0x00FB,
    Counter8 = 0x00FC,
    Counter9 = 0x00FD,
    Counter10 = 0x00FE,
    UnknownTimeEventBegin = 0x00FF,
    UnknownTimeEventEnd = 0x0112,
    ReputationInCurrentLocation = 0x0113,
    HistoryBegin = 0x0114,
    HistoryEnd = 0x0130,
    Unknown1 = 0x0131,
    BankGold = 0x0132,
    GoldInBank = 0x0132,
    NumDeaths = 0x0133,
    NumBounties = 0x0134,
    PrisonTerms = 0x0135,
    ArenaWinsPage = 0x0136,
    ArenaWinsSquire = 0x0137,
    ArenaWinsKnight = 0x0138,
    ArenaWinsLord = 0x0139,
    Invisible = 0x013A,
    ItemEquipped = 0x013B,
    Players = 0x013E,
}

support.houseId = support.houseId or {
    ThroneroomWinGood = 600,
    ThroneroomWinEvil = 601,
}

support.faceAttribute = support.faceAttribute or {
    Invisible = 0x00002000,
    HasHint = 0x00100000,
    Clickable = 0x02000000,
    PressurePlate = 0x04000000,
    Untouchable = 0x20000000,
}

support.actorAttribute = support.actorAttribute or {
    Invisible = 0x00010000,
    FullAi = 0x00000400,
    Active = 0x00004000,
    Nearby = 0x00008000,
    Fleeing = 0x00020000,
    Aggressor = 0x00080000,
    HasItem = 0x00800000,
    Hostile = 0x01000000,
}

support.chestFlag = support.chestFlag or {
    Trapped = 0x00000001,
    ItemsPlaced = 0x00000002,
    Opened = 0x00000004,
}

support.season = support.season or {
    Spring = 0,
    Summer = 1,
    Autumn = 2,
    Winter = 3,
}

support.partySelector = support.partySelector or {
    Member0 = 0,
    Member1 = 1,
    Member2 = 2,
    Member3 = 3,
    Member4 = 4,
    All = 5,
    Current = 7,
}

support.faceAnimation = support.faceAnimation or {
    KillSmallEnemy = 1,
    KillBigEnemy = 2,
    StoreClosed = 3,
    DisarmTrap = 4,
    TrapExploded = 5,
    AvoidDamage = 6,
    IdentifyUseless = 7,
    IdentifyGreat = 8,
    IdentifyFail = 9,
    RepairItem = 10,
    RepairFail = 11,
    SetQuickSpell = 12,
    CantRestHere = 13,
    SkillIncreased = 14,
    CantCarry = 15,
    MixPotion = 16,
    PotionExplode = 17,
    DoorLocked = 18,
    WontBudge = 19,
    CantLearnSpell = 20,
    LearnSpell = 21,
    Hello = 22,
    HelloNight = 23,
    Damaged = 24,
    Weak = 25,
    Afraid = 26,
    Poisoned = 27,
    Diseased = 28,
    Insane = 29,
    Cursed = 30,
    Drunk = 31,
    Unconscious = 32,
    Death = 33,
    Stoned = 34,
    Eradicated = 35,
    DrinkPotion = 36,
    ReadScroll = 37,
    NotEnoughGold = 38,
    CantEquip = 39,
    ItemBrokenStolen = 40,
    SpellPointsDrained = 41,
    Aged = 42,
    SpellFailed = 43,
    DamagedParty = 44,
    Tired = 45,
    EnterDungeon = 46,
    LeaveDungeon = 47,
    AlmostDead = 48,
    CastSpell = 49,
    Shoot = 50,
    AttackHit = 51,
    AttackMiss = 52,
    ShopIdentify = 53,
    ShopRepair = 54,
    AlreadyIdentified = 55,
    ItemSold = 56,
    WrongShop = 57,
}

support.players = support.players or {
    Member0 = 0,
    Member1 = 1,
    Member2 = 2,
    Member3 = 3,
    Member4 = 4,
    All = 5,
    Current = 7,
}

support.facetBits = support.facetBits or {
    Invisible = support.faceAttribute.Invisible,
    IsSecret = 0x00000002,
    MoveByDoor = 0x00040000,
    Untouchable = support.faceAttribute.Untouchable,
}

support.monsterBits = support.monsterBits or {
    Invisible = support.actorAttribute.Invisible,
    Hostile = support.actorAttribute.Hostile,
}

support.itemType = support.itemType or {
    Weapon_ = 20,
    Armor_ = 21,
    Misc = 22,
    Ring_ = 40,
    Scroll_ = 43,
}

support.mechanismState = support.mechanismState or {
    Closed = 0,
    Opening = 1,
    Open = 2,
    Closing = 3,
}

support.mechanismAction = support.mechanismAction or {
    Open = 0,
    Close = 1,
    Trigger = 2,
}
support.doorAction = support.doorAction or support.mechanismAction

support.actorKillCheck = support.actorKillCheck or {
    Any = 0,
    Group = 1,
    MonsterId = 2,
    ActorIdOe = 3,
    UniqueNameId = 4,
}

support.skillJoinedMask = support.skillJoinedMask or {
    Level = 0x003F,
    Normal = 0x0040,
    Expert = 0x0080,
    Master = 0x0100,
}

local function ensureMetaScope(scopeName)
    evt.meta = evt.meta or {}
    evt.meta[scopeName] = evt.meta[scopeName] or {}

    local meta = evt.meta[scopeName]
    meta.onLoad = meta.onLoad or {}
    meta.onLeave = meta.onLeave or {}
    meta.title = meta.title or {}
    meta.hint = meta.hint or {}
    meta.openedChestIds = meta.openedChestIds or {}
    meta.textureNames = meta.textureNames or {}
    meta.spriteNames = meta.spriteNames or {}
    meta.castSpellIds = meta.castSpellIds or {}
    meta.timers = meta.timers or {}

    return meta
end

function support.packSelector(tag, index)
    return math.floor(index or 0) * 65536 + tag
end

function support.ensurePackedSelector(selectorOrIndex, tag)
    if (selectorOrIndex or 0) > 0xFFFF then
        return selectorOrIndex
    end

    return support.packSelector(tag, selectorOrIndex)
end

function support.qbit(index)
    return support.packSelector(support.varTag.QBits, index)
end

function support.award(index)
    return support.packSelector(support.varTag.Awards, index)
end

function support.inventory(index)
    return support.packSelector(support.varTag.Inventory, index)
end

function support.autonote(index)
    return support.packSelector(support.varTag.AutonotesBits, index)
end

function support.player(index)
    return support.packSelector(support.varTag.Players, index)
end

function support.playerBit(index)
    return support.packSelector(support.varTag.PlayerBits, index)
end

function support.mapVar(index)
    return 0x007B + index
end

function support.decorVar(index)
    return support.varTag.DecorVarBegin + index
end

function support.counter(index)
    return support.varTag.Counter1 + index - 1
end

function support.history(index)
    return support.varTag.HistoryBegin + index - 1
end

function support.selectorIndex(selector)
    return math.floor((selector or 0) / 65536)
end

function support.isQBitSet(selector)
    local packedSelector = support.ensurePackedSelector(selector, support.varTag.QBits)
    return evt.Cmp(packedSelector, support.selectorIndex(packedSelector))
end

function support.setQBit(selector)
    local packedSelector = support.ensurePackedSelector(selector, support.varTag.QBits)
    evt.Add(packedSelector, support.selectorIndex(packedSelector))
end

function support.clearQBit(selector)
    local packedSelector = support.ensurePackedSelector(selector, support.varTag.QBits)
    evt.Subtract(packedSelector, support.selectorIndex(packedSelector))
end

function support.hasAward(awardId)
    local packedSelector = support.ensurePackedSelector(awardId, support.varTag.Awards)
    return evt.Cmp(packedSelector, support.selectorIndex(packedSelector))
end

function support.setAward(awardId)
    local packedSelector = support.ensurePackedSelector(awardId, support.varTag.Awards)
    evt.Add(packedSelector, support.selectorIndex(packedSelector))
end

function support.clearAward(awardId)
    local packedSelector = support.ensurePackedSelector(awardId, support.varTag.Awards)
    evt.Subtract(packedSelector, support.selectorIndex(packedSelector))
end

function support.isAutonoteSet(noteId)
    local packedSelector = support.ensurePackedSelector(noteId, support.varTag.AutonotesBits)
    return evt.Cmp(packedSelector, support.selectorIndex(packedSelector))
end

function support.setAutonote(noteId)
    local packedSelector = support.ensurePackedSelector(noteId, support.varTag.AutonotesBits)
    evt.Add(packedSelector, support.selectorIndex(packedSelector))
end

function support.clearAutonote(noteId)
    local packedSelector = support.ensurePackedSelector(noteId, support.varTag.AutonotesBits)
    evt.Subtract(packedSelector, support.selectorIndex(packedSelector))
end

function support.hasItem(itemId)
    return evt.Cmp(support.inventory(itemId), itemId)
end

function support.removeItem(itemId)
    evt.Subtract(support.inventory(itemId), itemId)
end

function support.giveItem(...)
    evt.GiveItem(...)
end

function support.hasPlayer(rosterId)
    return evt.Cmp(support.player(rosterId), rosterId)
end

function support.isPlayerBitSet(bitId)
    local packedSelector = support.ensurePackedSelector(bitId, support.varTag.PlayerBits)
    return evt.Cmp(packedSelector, support.selectorIndex(packedSelector))
end

function support.setPlayerBit(bitId)
    local packedSelector = support.ensurePackedSelector(bitId, support.varTag.PlayerBits)
    evt.Add(packedSelector, support.selectorIndex(packedSelector))
end

function support.clearPlayerBit(bitId)
    local packedSelector = support.ensurePackedSelector(bitId, support.varTag.PlayerBits)
    evt.Subtract(packedSelector, support.selectorIndex(packedSelector))
end

function support.isAtLeast(selector, value)
    return evt.Cmp(selector, value)
end

function support.addValue(selector, value)
    if selector == support.varTag.IsIntellectMoreThanBase then
        local packedSelector = support.packSelector(selector, value)
        evt.Add(packedSelector, value)
        return
    end

    evt.Add(selector, value)
end

function support.setValue(selector, value)
    if selector == support.varTag.IsIntellectMoreThanBase then
        local packedSelector = support.packSelector(selector, value)
        evt.Set(packedSelector, value)
        return
    end

    evt.Set(selector, value)
end

function support.subtractValue(selector, value)
    evt.Subtract(selector, value)
end

function support.addToCounter(counterSelector, value)
    evt.Add(counterSelector, value)
end

function support.setCounter(counterSelector, value)
    evt.Set(counterSelector, value)
end

function support.registerScopeEvent(scopeName, tableName, eventId, title, handler, hint)
    local meta = ensureMetaScope(scopeName)

    if title ~= nil and title ~= "" then
        meta.title[eventId] = title
    end

    if hint ~= nil and hint ~= "" then
        meta.hint[eventId] = hint
    end

    if handler ~= nil then
        evt[tableName][eventId] = function(...)
            evt._BeginEvent(eventId)
            handler(...)
        end
    end
end

function support.registerEvent(eventId, title, handler, hint)
    support.registerScopeEvent("map", "map", eventId, title, handler, hint)
end

function support.registerGlobalEvent(eventId, title, handler, hint)
    support.registerScopeEvent("global", "global", eventId, title, handler, hint)
end

function support.registerNoOpEvent(eventId, title, hint)
    support.registerEvent(eventId, title, function()
    end, hint)
end

function support.registerGlobalNoOpEvent(eventId, title, hint)
    support.registerGlobalEvent(eventId, title, function()
    end, hint)
end

function support.registerCanShowTopic(eventId, handler)
    evt.CanShowTopic[eventId] = function()
        evt._BeginCanShowTopic(eventId)
        return handler()
    end
end

function support.point(x, y, z)
    return {x = x, y = y, z = z}
end

function support.moveToMap(destination)
    evt.MoveToMap(table.unpack(destination))
end

function support.castSpellFromTo(spellId, mastery, skill, from, to)
    evt.CastSpell(spellId, mastery, skill, from.x, from.y, from.z, to.x, to.y, to.z)
end

function support.pickRandomOption(eventId, step, options)
    local indices = {}

    for index = 1, #options do
        indices[index] = index
    end

    local selectedIndex = evt._RandomJump(eventId, step, indices)
    return options[selectedIndex]
end

function support.setMapMetadata(metadata)
    local meta = ensureMetaScope("map")

    for key, value in pairs(metadata) do
        meta[key] = value
    end
end

function support.setGlobalMetadata(metadata)
    local meta = ensureMetaScope("global")

    for key, value in pairs(metadata) do
        meta[key] = value
    end
end

local function exportTableEntries(entries)
    for name, value in pairs(entries) do
        _G[name] = value
    end
end

VarTag = support.varTag
FaceAttribute = support.faceAttribute
ActorAttribute = support.actorAttribute
ChestFlag = support.chestFlag
Season = support.season
PartySelector = support.partySelector
FaceAnimation = support.faceAnimation
Players = support.players
FacetBits = support.facetBits
MonsterBits = support.monsterBits
ItemType = support.itemType
MechanismState = support.mechanismState
MechanismAction = support.mechanismAction
DoorAction = support.doorAction
ActorKillCheck = support.actorKillCheck
HouseId = support.houseId
SkillJoinedMask = support.skillJoinedMask
PackSelector = support.packSelector
EnsurePackedSelector = support.ensurePackedSelector
QBit = support.qbit
Award = support.award
InventoryItem = support.inventory
AutonoteBit = support.autonote
Player = support.player
PlayerVar = support.player
PlayerBit = support.playerBit
MapVar = support.mapVar
DecorVar = support.decorVar
Counter = support.counter
History = support.history
SelectorIndex = support.selectorIndex
IsQBitSet = support.isQBitSet
SetQBit = support.setQBit
ClearQBit = support.clearQBit
HasAward = support.hasAward
SetAward = support.setAward
ClearAward = support.clearAward
IsAutonoteSet = support.isAutonoteSet
SetAutonote = support.setAutonote
ClearAutonote = support.clearAutonote
HasItem = support.hasItem
RemoveItem = support.removeItem
GiveItem = support.giveItem
HasPlayer = support.hasPlayer
IsPlayerBitSet = support.isPlayerBitSet
SetPlayerBit = support.setPlayerBit
ClearPlayerBit = support.clearPlayerBit
IsAtLeast = support.isAtLeast
AddValue = support.addValue
SetValue = support.setValue
SubtractValue = support.subtractValue
AddToCounter = support.addToCounter
SetCounter = support.setCounter
RegisterEvent = support.registerEvent
RegisterGlobalEvent = support.registerGlobalEvent
RegisterNoOpEvent = support.registerNoOpEvent
RegisterGlobalNoOpEvent = support.registerGlobalNoOpEvent
RegisterCanShowTopic = support.registerCanShowTopic
Point = support.point
MoveToMap = support.moveToMap
CastSpellFromTo = support.castSpellFromTo
PickRandomOption = support.pickRandomOption
SetMapMetadata = support.setMapMetadata
SetGlobalMetadata = support.setGlobalMetadata
exportTableEntries(support.varTag)
Players = support.players
FacetBits = support.facetBits
MonsterBits = support.monsterBits
ItemType = support.itemType
DoorAction = support.doorAction
ActorKillCheck = support.actorKillCheck

const = const or {}
const.FacetBits = support.facetBits
const.MonsterBits = support.monsterBits
const.ItemType = support.itemType
const.DoorAction = support.doorAction
const.ActorKillCheck = support.actorKillCheck
const.HouseId = support.houseId

-- Compatibility aliases for older/generated scripts. New authored scripts should use CamelCase globals.
isQBitSet = support.isQBitSet
setQBit = support.setQBit
clearQBit = support.clearQBit
hasAward = support.hasAward
setAward = support.setAward
clearAward = support.clearAward
isAutonoteSet = support.isAutonoteSet
setAutonote = support.setAutonote
clearAutonote = support.clearAutonote
hasItem = support.hasItem
removeItem = support.removeItem
giveItem = support.giveItem
player = support.player
hasPlayer = support.hasPlayer
isPlayerBitSet = support.isPlayerBitSet
setPlayerBit = support.setPlayerBit
clearPlayerBit = support.clearPlayerBit
isAtLeast = support.isAtLeast
addValue = support.addValue
setValue = support.setValue
subtractValue = support.subtractValue
addToCounter = support.addToCounter
setCounter = support.setCounter
registerEvent = support.registerEvent
registerGlobalEvent = support.registerGlobalEvent
registerNoOpEvent = support.registerNoOpEvent
registerGlobalNoOpEvent = support.registerGlobalNoOpEvent
registerCanShowTopic = support.registerCanShowTopic
point = support.point
moveToMap = support.moveToMap
castSpellFromTo = support.castSpellFromTo
pickRandomOption = support.pickRandomOption
setMapMetadata = support.setMapMetadata
setGlobalMetadata = support.setGlobalMetadata
