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

support.houseAction = support.houseAction or {
    TempleHeal = 1,
    TempleDonate = 2,
    TavernRentRoom = 3,
    TavernBuyFood = 4,
    TrainingTrainActiveMember = 5,
    BankDepositAll = 6,
    BankWithdrawAll = 7,
    OpenLearnSkillsMenu = 8,
    OpenShopEquipmentMenu = 9,
    OpenTavernArcomageMenu = 10,
    BackToRootMenu = 11,
    LearnSkill = 12,
    ShopBuyStandard = 13,
    ShopBuySpecial = 14,
    ShopSell = 15,
    ShopIdentify = 16,
    ShopRepair = 17,
    GuildBuySpellbooks = 18,
    TavernArcomageRules = 19,
    TavernArcomageVictoryConditions = 20,
    TavernArcomagePlay = 21,
    TransportRoute = 22,
    ExtraExit = 23,
    LorettaPriceFixing = 24,
}

support.faceAttribute = support.faceAttribute or {
    Fluid = 0x00000010,
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
    Beg = 53,
    BegFail = 54,
    Threat = 55,
    ThreatFail = 56,
    Bribe = 57,
    BribeFail = 58,
    NpcDontTalk = 59,
    NPCDontTalk = 59,
    FoundItem = 60,
    HireNpc = 61,
    HireNPC = 61,
    LookUp = 63,
    LookDown = 64,
    Yell = 65,
    Falling = 66,
    TavernPacksFull = 67,
    ShakeHeadNo = 67,
    TavernDrink = 68,
    TavernGotDrunk = 69,
    TavernTip = 70,
    TravelHorse = 71,
    ShakeHeadYes = 71,
    TravelBoat = 72,
    ShopIdentify = 73,
    ShopRepair = 74,
    ShopItemBought = 75,
    ShopAlreadyIdentified = 76,
    AlreadyIdentified = 76,
    ShopItemSold = 77,
    ItemSold = 77,
    SkillLearned = 78,
    ShopWrongShop = 79,
    WrongShop = 79,
    ShopRude = 80,
    BankDeposit = 81,
    TempleHeal = 82,
    SmileBig = 82,
    TempleDonate = 83,
    HelloHouse = 84,
    SkillMasteryIncreased = 85,
    SkillMasteryIcreased = 85,
    JoinedGuild = 86,
    LevelUp = 87,
    StatBonusIncreased = 91,
    StatBaseIncreased = 92,
    QuestGot = 93,
    AwardGot = 96,
    AfraidSilent = 98,
    CheatedDeath = 99,
    InPrison = 100,
    ChooseMe = 102,
    Awaken = 103,
    IdMonsterWeak = 104,
    IdentifyMonsterWeak = 104,
    IdMonsterBig = 105,
    IdentifyMonsterBig = 105,
    IdMonsterFail = 106,
    IdentifyMonsterFail = 106,
    LastManStanding = 107,
    NotEnoughFood = 108,
    Hungry = 108,
    DeathBlow = 109,
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
    Fluid = support.faceAttribute.Fluid,
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

support.damage = support.damage or {
    Fire = 0,
    Air = 1,
    Water = 2,
    Earth = 3,
    Physical = 4,
    Magic = 5,
    Spirit = 6,
    Mind = 7,
    Body = 8,
    Light = 9,
    Dark = 10,
    Energy = 12,
    Electric = 1,
    Cold = 2,
    Poison = 8,
}

support.skills = support.skills or {
    Perception = 31,
    DisarmTraps = 33,
}

support.skillCheck = support.skillCheck or {
    Novice = 0,
    Effective = 0,
    Expert = 1,
    Master = 2,
    Grandmaster = 3,
    GM = 3,
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
    meta.npcEnterHooks = meta.npcEnterHooks or {}
    meta.npcExitHooks = meta.npcExitHooks or {}
    meta.houseTopicFilterHooks = meta.houseTopicFilterHooks or {}
    meta.houseTopicClickHooks = meta.houseTopicClickHooks or {}
    meta.restFoodCostHooks = meta.restFoodCostHooks or {}
    meta.gameplayActionHooks = meta.gameplayActionHooks or {}
    meta.mapRefillHooks = meta.mapRefillHooks or {}
    meta.mapTransitionHooks = meta.mapTransitionHooks or {}
    meta.monsterKilledHooks = meta.monsterKilledHooks or {}
    meta.monsterDamageHooks = meta.monsterDamageHooks or {}
    meta.chestOpenHooks = meta.chestOpenHooks or {}
    meta.title = meta.title or {}
    meta.hint = meta.hint or {}
    meta.openedChestIds = meta.openedChestIds or {}
    meta.contextActions = meta.contextActions or {}
    meta.textureNames = meta.textureNames or {}
    meta.spriteNames = meta.spriteNames or {}
    meta.castSpellIds = meta.castSpellIds or {}
    meta.timers = meta.timers or {}

    return meta
end

local function removeArrayValue(values, value)
    if values == nil then
        return
    end

    local writeIndex = 1

    for readIndex = 1, #values do
        if values[readIndex] ~= value then
            values[writeIndex] = values[readIndex]
            writeIndex = writeIndex + 1
        end
    end

    for index = writeIndex, #values do
        values[index] = nil
    end
end

local function removeTimersForEvent(timers, eventId)
    if timers == nil then
        return
    end

    local writeIndex = 1

    for readIndex = 1, #timers do
        local timer = timers[readIndex]

        if timer == nil or timer.eventId ~= eventId then
            timers[writeIndex] = timer
            writeIndex = writeIndex + 1
        end
    end

    for index = writeIndex, #timers do
        timers[index] = nil
    end
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

function support.hasEverOwnedItem(itemId)
    return evt.HasEverOwnedItem(itemId)
end

function support.hasItemAnywhere(itemId)
    return evt.HasItemAnywhere(itemId)
end

function support.removeItem(itemId)
    evt.Subtract(support.inventory(itemId), itemId)
end

function support.giveItem(...)
    evt.GiveItem(...)
end

function support.anyQBitSet(qbits)
    for _, qbit in ipairs(qbits or {}) do
        if IsQBitSet(QBit(qbit)) then
            return true
        end
    end

    return false
end

function support.tryRecoverLostItem(entries)
    for _, entry in ipairs(entries or {}) do
        local itemId = entry.Item
        local recoveryQBit = entry.QBit
        local recoveryQBits = entry.QBits
        local proofQBits = entry.ProofQBits
        local questActive = recoveryQBit == nil and recoveryQBits == nil
        local proofActive = false

        if recoveryQBit ~= nil and IsQBitSet(QBit(recoveryQBit)) then
            questActive = true
            proofActive = true
        end

        if recoveryQBits ~= nil then
            questActive = support.anyQBitSet(recoveryQBits)
        end

        if proofQBits ~= nil then
            proofActive = support.anyQBitSet(proofQBits)
        end

        local everOwned = itemId and HasEverOwnedItem(itemId)
        local currentlyOwned = itemId and HasItemAnywhere(itemId)
        local wasOwned = everOwned or proofActive

        if itemId
            and wasOwned
            and not currentlyOwned
            and questActive then
            GiveItem(itemId)
            evt.SimpleMessage(entry.Message or "Here is your missing item.")
            return true
        end
    end

    evt.SimpleMessage("You never had it!")
    return false
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

function support.mergedClassIdToEngineClassId(value)
    return value
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

function support.removeScopeEvent(scopeName, tableName, eventId)
    local meta = ensureMetaScope(scopeName)

    if evt[tableName] ~= nil then
        evt[tableName][eventId] = nil
    end

    meta.title[eventId] = nil
    meta.hint[eventId] = nil
    meta.summary = meta.summary or {}
    meta.summary[eventId] = nil
    meta.openedChestIds[eventId] = nil
    meta.contextActions[eventId] = nil

    removeArrayValue(meta.onLoad, eventId)
    removeArrayValue(meta.onLeave, eventId)
    removeTimersForEvent(meta.timers, eventId)
end

function support.removeMapEvent(eventId)
    support.removeScopeEvent("map", "map", eventId)
end

function support.removeGlobalEvent(eventId)
    support.removeScopeEvent("global", "global", eventId)
end

function support.replaceMapEvent(eventId, title, handler, hint)
    support.removeMapEvent(eventId)
    support.registerEvent(eventId, title, handler, hint)
end

function support.replaceGlobalEvent(eventId, title, handler, hint)
    support.removeGlobalEvent(eventId)
    support.registerGlobalEvent(eventId, title, handler, hint)
end

function support.appendScopeEvent(scopeName, tableName, eventId, handler)
    local previous = evt[tableName][eventId]

    evt[tableName][eventId] = function(...)
        if previous ~= nil then
            previous(...)
        else
            evt._BeginEvent(eventId)
        end

        if handler ~= nil then
            handler(...)
        end
    end
end

function support.appendMapEvent(eventId, handler)
    support.appendScopeEvent("map", "map", eventId, handler)
end

function support.appendGlobalEvent(eventId, handler)
    support.appendScopeEvent("global", "global", eventId, handler)
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

function support.registerOutdoorModelMechanism(mechanismId, modelName, dx, dy, dz, moveTimeMs, closed, moveParty)
    evt.RegisterOutdoorModelMechanism(
        mechanismId,
        modelName,
        dx or 0,
        dy or 0,
        dz or 0,
        moveTimeMs or 1000,
        closed == nil and true or closed,
        moveParty or false)
end

function support.setOutdoorModelMechanismState(mechanismId, action)
    evt.SetOutdoorModelMechanismState(mechanismId, action)
end

function support.saveCurrentLocation(name)
    evt.SaveCurrentLocation(name)
end

function support.hasSavedLocation(name)
    return evt.HasSavedLocation(name)
end

function support.moveToSavedLocation(name, clearAfterUse)
    return evt.MoveToSavedLocation(name, clearAfterUse)
end

function support.clearSavedLocation(name)
    evt.ClearSavedLocation(name)
end

function support.setTransportRouteOverride(houseId, routeIndex, route)
    evt.SetTransportRouteOverride(houseId, routeIndex, route)
end

function support.clearTransportRouteOverride(houseId, routeIndex)
    evt.ClearTransportRouteOverride(houseId, routeIndex)
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

function support.askQuestionWithAnswerSteps(eventId, fallbackStep, question, choices)
    evt.AskQuestionWithAnswerSteps(eventId, fallbackStep, question, choices)
end

function support.setMapMetadata(metadata)
    local meta = ensureMetaScope("map")
    local existingOnLoad = meta.onLoad or {}
    local existingOnLeave = meta.onLeave or {}
    local existingTimers = meta.timers or {}

    for key, value in pairs(metadata) do
        meta[key] = value
    end

    if #existingOnLoad > 0 then
        meta.onLoad = meta.onLoad or {}
        for _, eventId in ipairs(existingOnLoad) do
            table.insert(meta.onLoad, eventId)
        end
    end

    if #existingOnLeave > 0 then
        meta.onLeave = meta.onLeave or {}
        for _, eventId in ipairs(existingOnLeave) do
            table.insert(meta.onLeave, eventId)
        end
    end

    if #existingTimers > 0 then
        meta.timers = meta.timers or {}
        for _, timer in ipairs(existingTimers) do
            table.insert(meta.timers, timer)
        end
    end
end

function support.setMapContextAction(eventId, metadata)
    local meta = ensureMetaScope("map")
    meta.contextActions[eventId] = metadata
end

function support.appendMapOnLoadEvent(eventId)
    local meta = ensureMetaScope("map")
    table.insert(meta.onLoad, eventId)
end

function support.appendMapOnLeaveEvent(eventId)
    local meta = ensureMetaScope("map")
    table.insert(meta.onLeave, eventId)
end

function support.registerMapOnLoadEvent(eventId, title, handler, hint)
    support.registerEvent(eventId, title, handler, hint)
    support.appendMapOnLoadEvent(eventId)
end

function support.registerMapOnLeaveEvent(eventId, title, handler, hint)
    support.registerEvent(eventId, title, handler, hint)
    support.appendMapOnLeaveEvent(eventId)
end

function support.registerMapTimerEvent(eventId, intervalSeconds, handler, title, hint, initialDelaySeconds)
    support.removeMapEvent(eventId)
    support.registerEvent(eventId, title, handler, hint)

    local meta = ensureMetaScope("map")
    local intervalGameMinutes = (intervalSeconds or 0) / 60
    local remainingGameMinutes = (initialDelaySeconds or intervalSeconds or 0) / 60
    table.insert(meta.timers, {
        eventId = eventId,
        repeating = true,
        intervalGameMinutes = intervalGameMinutes,
        remainingGameMinutes = remainingGameMinutes,
    })
end

function support.appendGlobalOnLoadEvent(eventId)
    local meta = ensureMetaScope("global")
    table.insert(meta.onLoad, eventId)
end

function support.registerGlobalOnLoadEvent(eventId, title, handler, hint)
    support.registerGlobalEvent(eventId, title, handler, hint)
    support.appendGlobalOnLoadEvent(eventId)
end

function support.registerGlobalTimerEvent(eventId, intervalSeconds, handler, title, hint, initialDelaySeconds)
    support.removeGlobalEvent(eventId)
    support.registerGlobalEvent(eventId, title, handler, hint)

    local meta = ensureMetaScope("global")
    local intervalGameMinutes = (intervalSeconds or 0) / 60
    local remainingGameMinutes = (initialDelaySeconds or intervalSeconds or 0) / 60
    table.insert(meta.timers, {
        eventId = eventId,
        repeating = true,
        intervalGameMinutes = intervalGameMinutes,
        remainingGameMinutes = remainingGameMinutes,
    })
end

local function appendHookEvent(scopeName, hookName, eventId)
    local meta = ensureMetaScope(scopeName)
    meta[hookName] = meta[hookName] or {}
    table.insert(meta[hookName], eventId)
end

local function registerMapHook(hookName, eventId, title, handler)
    support.replaceMapEvent(eventId, title, function()
        handler(evt.GetHookContext())
    end)
    appendHookEvent("map", hookName, eventId)
end

local function registerGlobalHook(hookName, eventId, title, handler)
    support.replaceGlobalEvent(eventId, title, function()
        handler(evt.GetHookContext())
    end)
    appendHookEvent("global", hookName, eventId)
end

function support.registerNpcEnterHook(eventId, title, handler)
    registerMapHook("npcEnterHooks", eventId, title, handler)
end

function support.registerGlobalNpcEnterHook(eventId, title, handler)
    registerGlobalHook("npcEnterHooks", eventId, title, handler)
end

function support.registerNpcExitHook(eventId, title, handler)
    registerMapHook("npcExitHooks", eventId, title, handler)
end

function support.registerGlobalNpcExitHook(eventId, title, handler)
    registerGlobalHook("npcExitHooks", eventId, title, handler)
end

function support.registerHouseTopicFilter(eventId, title, handler)
    registerMapHook("houseTopicFilterHooks", eventId, title, handler)
end

function support.registerGlobalHouseTopicFilter(eventId, title, handler)
    registerGlobalHook("houseTopicFilterHooks", eventId, title, handler)
end

function support.registerHouseTopicClickHook(eventId, title, handler)
    registerMapHook("houseTopicClickHooks", eventId, title, handler)
end

function support.registerGlobalHouseTopicClickHook(eventId, title, handler)
    registerGlobalHook("houseTopicClickHooks", eventId, title, handler)
end

function support.registerRestFoodCostHook(eventId, title, handler)
    registerMapHook("restFoodCostHooks", eventId, title, handler)
end

function support.registerGlobalRestFoodCostHook(eventId, title, handler)
    registerGlobalHook("restFoodCostHooks", eventId, title, handler)
end

function support.registerGameplayActionHook(eventId, title, handler)
    registerMapHook("gameplayActionHooks", eventId, title, handler)
end

function support.registerGlobalGameplayActionHook(eventId, title, handler)
    registerGlobalHook("gameplayActionHooks", eventId, title, handler)
end

function support.registerMapRefillHook(eventId, title, handler)
    registerMapHook("mapRefillHooks", eventId, title, handler)
end

function support.registerGlobalMapRefillHook(eventId, title, handler)
    registerGlobalHook("mapRefillHooks", eventId, title, handler)
end

function support.registerMapTransitionHook(eventId, title, handler)
    registerMapHook("mapTransitionHooks", eventId, title, handler)
end

function support.registerGlobalMapTransitionHook(eventId, title, handler)
    registerGlobalHook("mapTransitionHooks", eventId, title, handler)
end

function support.registerMonsterKilledHook(eventId, title, handler)
    registerMapHook("monsterKilledHooks", eventId, title, handler)
end

function support.registerGlobalMonsterKilledHook(eventId, title, handler)
    registerGlobalHook("monsterKilledHooks", eventId, title, handler)
end

function support.registerMonsterDamageHook(eventId, title, handler)
    registerMapHook("monsterDamageHooks", eventId, title, handler)
end

function support.registerGlobalMonsterDamageHook(eventId, title, handler)
    registerGlobalHook("monsterDamageHooks", eventId, title, handler)
end

function support.registerChestOpenHook(eventId, title, handler)
    registerMapHook("chestOpenHooks", eventId, title, handler)
end

function support.registerGlobalChestOpenHook(eventId, title, handler)
    registerGlobalHook("chestOpenHooks", eventId, title, handler)
end

function support.registerInventoryOpenHook(eventId, title, handler)
    registerMapHook("inventoryOpenHooks", eventId, title, handler)
end

function support.registerGlobalInventoryOpenHook(eventId, title, handler)
    registerGlobalHook("inventoryOpenHooks", eventId, title, handler)
end

function support.isFlying()
    return evt.Cmp(support.varTag.IsFlying, 1)
end

function support.isInvisible()
    return evt.Cmp(support.varTag.Invisible, 1)
end

function support.hasFollowerProfession(professionId)
    return evt.Cmp(support.packSelector(support.varTag.HiredNpcHasSpeciality, professionId), 1)
end

function support.removeFollowerProfession(professionId)
    return evt.RemoveFollowerProfession(professionId)
end

function support.hasFollowerNpc(npcId)
    return evt.HasFollowerNpc(npcId)
end

function support.addFollowerNpc(npcId, professionId, weeklyCost)
    return evt.AddFollowerNpc(npcId, professionId or 0, weeklyCost or 0)
end

function support.removeFollowerNpc(npcId)
    return evt.RemoveFollowerNpc(npcId)
end

function support.currentGameMinutes()
    return evt.CurrentGameMinutes()
end

function support.npcText(textId, fallback)
    return evt.NPCText(textId or 0, fallback or "")
end

Game = Game or {}
Game.NPCText = setmetatable(Game.NPCText or {}, {
    __index = function(_, key)
        return support.npcText(tonumber(key) or 0)
    end,
})

function support.currentContinent()
    return evt.GetCurrentContinent()
end

function support.advanceGameMinutes(minutes)
    evt.AdvanceGameMinutes(minutes or 0)
end

function support.getRuntimeVariable(variableId)
    return evt.GetRuntimeVariable(variableId)
end

function support.setRuntimeVariable(variableId, value)
    evt.SetRuntimeVariable(variableId, value or 0)
end

function support.currentEventSpellId()
    return evt.GetActiveEventSpellId()
end

function support.getPartyVariable(variableId)
    return evt.GetPartyVariable(variableId)
end

function support.setPartyVariable(variableId, value)
    evt.SetPartyVariable(variableId, value or 0)
end

function support.getClassId(className)
    return evt.GetClassId(className or "")
end

function support.getClassName(classId)
    return evt.GetClassName(classId or 0)
end

function support.getPlayerClass(playerIndex)
    return evt.GetPlayerClass(playerIndex)
end

function support.getPlayerClassName(playerIndex)
    return evt.GetPlayerClassName(playerIndex)
end

function support.setPlayerClass(playerIndex, classIdOrName)
    return evt.SetPlayerClass(playerIndex, classIdOrName)
end

function support.playerItemCount(playerIndex, itemId)
    return evt.PartyMemberItemCount(playerIndex, itemId or 0)
end

function support.playerHasItem(playerIndex, itemId)
    return support.playerItemCount(playerIndex, itemId) > 0
end

function support.givePlayerItem(playerIndex, itemId, quantity)
    return evt.GivePartyMemberItem(playerIndex, itemId or 0, quantity or 1)
end

function support.replacePartyInventoryItems(fromItemId, toItemId)
    return evt.ReplacePartyInventoryItems(fromItemId or 0, toItemId or 0)
end

function support.playerKnowsSpell(playerIndex, spellId)
    return evt.PartyMemberKnowsSpell(playerIndex, spellId or 0)
end

function support.removePlayerItem(playerIndex, itemId, quantity)
    return evt.RemovePartyMemberItem(playerIndex, itemId or 0, quantity or 1)
end

function support.applyLichTransformation(playerIndex)
    return evt.ApplyLichTransformation(playerIndex)
end

function support.getClassSkillCap(classIdOrName, skillName)
    return evt.GetClassSkillCap(classIdOrName, skillName or "")
end

function support.canClassLearnSkill(classIdOrName, skillName, requiredMastery)
    return evt.CanClassLearnSkill(classIdOrName, skillName or "", requiredMastery or 1)
end

function support.canPlayerLearnSkill(playerIndex, skillName, requiredMastery)
    return evt.CanPlayerLearnSkill(playerIndex, skillName or "", requiredMastery or 1)
end

local function normalizeClassId(classIdOrName)
    if type(classIdOrName) == "string" then
        return support.getClassId(classIdOrName)
    end

    return classIdOrName or -1
end

function support.playerClassMatches(playerIndex, classIdOrNameOrList)
    local currentClassId = support.getPlayerClass(playerIndex)

    if type(classIdOrNameOrList) == "table" then
        for _, candidate in ipairs(classIdOrNameOrList) do
            if currentClassId == normalizeClassId(candidate) then
                return true
            end
        end

        return false
    end

    return currentClassId == normalizeClassId(classIdOrNameOrList)
end

function support.applyPlayerRewards(playerIndex, rewards)
    if rewards == nil then
        return
    end

    evt.ForPlayer(playerIndex)

    for key, value in pairs(rewards) do
        if type(key) == "number" then
            evt.Add(key, value or 0)
        elseif key == "Experience" then
            evt.Add(support.varTag.Experience, value or 0)
        elseif key == "SkillPoints" then
            evt.Add(support.varTag.SkillPoints, value or 0)
        elseif key == "Award" or key == "Awards" then
            if type(value) == "table" then
                for _, awardId in ipairs(value) do
                    evt.Add(support.award(awardId), awardId)
                end
            else
                evt.Add(support.award(value or 0), value or 0)
            end
        elseif key == "Inventory" or key == "Item" or key == "Items" then
            if type(value) == "table" then
                for _, itemId in ipairs(value) do
                    evt.Add(support.inventory(itemId), itemId)
                end
            else
                evt.Add(support.inventory(value or 0), value or 0)
            end
        else
            local selector = support.varTag[key]
            if selector ~= nil then
                evt.Add(selector, value or 0)
            end
        end
    end

    evt.ForPlayer(support.players.Current)
end

function support.partyMembers()
    local players = {}
    local memberCount = evt.GetPartyMemberCount()

    for playerIndex = 0, memberCount - 1 do
        table.insert(players, playerIndex)
    end

    return players
end

function support.promotePlayers(promotion)
    local result = {
        promotedCount = 0,
        promotedPlayers = {},
        nonPromotedPlayers = {},
    }

    if promotion == nil or promotion.to == nil then
        return result
    end

    local memberCount = evt.GetPartyMemberCount()
    local players = promotion.players

    if players == nil then
        players = {}
        for playerIndex = 0, memberCount - 1 do
            table.insert(players, playerIndex)
        end
    end

    for _, playerIndex in ipairs(players) do
        if playerIndex >= 0 and playerIndex < memberCount then
            if promotion.from == nil or support.playerClassMatches(playerIndex, promotion.from) then
                if support.setPlayerClass(playerIndex, promotion.to) then
                    result.promotedCount = result.promotedCount + 1
                    table.insert(result.promotedPlayers, playerIndex)
                    support.applyPlayerRewards(playerIndex, promotion.promotedRewards or promotion.rewards)
                end
            else
                table.insert(result.nonPromotedPlayers, playerIndex)
                support.applyPlayerRewards(playerIndex, promotion.nonPromotedRewards)
            end
        end
    end

    return result
end

function support.applyLocalMonsterRelations(relations)
    if relations == nil then
        return
    end

    for _, relation in ipairs(relations) do
        evt.SetMonsterRelation(relation[1] or 0, relation[2] or 0, relation[3] or 0)
    end
end

function support.setNpcName(npcId, name)
    evt.SetNPCName(npcId, name or "")
end

function support.setNpcPicture(npcId, pictureId)
    evt.SetNPCPicture(npcId, pictureId or 0)
end

function support.setNpcProfession(npcId, professionId)
    evt.SetNPCProfession(npcId, professionId or 0)
end

function support.setGlobalMetadata(metadata)
    local meta = ensureMetaScope("global")
    local existingOnLoad = meta.onLoad or {}
    local existingOnLeave = meta.onLeave or {}
    local existingTimers = meta.timers or {}

    for key, value in pairs(metadata) do
        meta[key] = value
    end

    if #existingOnLoad > 0 then
        meta.onLoad = meta.onLoad or {}
        for _, eventId in ipairs(existingOnLoad) do
            table.insert(meta.onLoad, eventId)
        end
    end

    if #existingOnLeave > 0 then
        meta.onLeave = meta.onLeave or {}
        for _, eventId in ipairs(existingOnLeave) do
            table.insert(meta.onLeave, eventId)
        end
    end

    if #existingTimers > 0 then
        meta.timers = meta.timers or {}
        for _, timer in ipairs(existingTimers) do
            table.insert(meta.timers, timer)
        end
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
HouseAction = support.houseAction
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
HasEverOwnedItem = support.hasEverOwnedItem
HasItemAnywhere = support.hasItemAnywhere
RemoveItem = support.removeItem
GiveItem = support.giveItem
ReplacePartyInventoryItems = support.replacePartyInventoryItems
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
PartyMembers = support.partyMembers
RegisterEvent = support.registerEvent
RegisterGlobalEvent = support.registerGlobalEvent
RegisterNoOpEvent = support.registerNoOpEvent
RegisterGlobalNoOpEvent = support.registerGlobalNoOpEvent
RemoveMapEvent = support.removeMapEvent
RemoveGlobalEvent = support.removeGlobalEvent
ReplaceMapEvent = support.replaceMapEvent
ReplaceGlobalEvent = support.replaceGlobalEvent
AppendMapEvent = support.appendMapEvent
AppendGlobalEvent = support.appendGlobalEvent
RegisterCanShowTopic = support.registerCanShowTopic
Point = support.point
MoveToMap = support.moveToMap
RegisterOutdoorModelMechanism = support.registerOutdoorModelMechanism
SetOutdoorModelMechanismState = support.setOutdoorModelMechanismState
SaveCurrentLocation = support.saveCurrentLocation
HasSavedLocation = support.hasSavedLocation
MoveToSavedLocation = support.moveToSavedLocation
ClearSavedLocation = support.clearSavedLocation
SetTransportRouteOverride = support.setTransportRouteOverride
ClearTransportRouteOverride = support.clearTransportRouteOverride
CastSpellFromTo = support.castSpellFromTo
PickRandomOption = support.pickRandomOption
AskQuestionWithAnswerSteps = support.askQuestionWithAnswerSteps
SetMapMetadata = support.setMapMetadata
SetMapContextAction = support.setMapContextAction
AppendMapOnLoadEvent = support.appendMapOnLoadEvent
AppendMapOnLeaveEvent = support.appendMapOnLeaveEvent
RegisterMapOnLoadEvent = support.registerMapOnLoadEvent
RegisterMapOnLeaveEvent = support.registerMapOnLeaveEvent
RegisterMapTimerEvent = support.registerMapTimerEvent
RegisterGlobalOnLoadEvent = support.registerGlobalOnLoadEvent
RegisterGlobalTimerEvent = support.registerGlobalTimerEvent
RegisterNpcEnterHook = support.registerNpcEnterHook
RegisterGlobalNpcEnterHook = support.registerGlobalNpcEnterHook
RegisterNpcExitHook = support.registerNpcExitHook
RegisterGlobalNpcExitHook = support.registerGlobalNpcExitHook
RegisterHouseTopicFilter = support.registerHouseTopicFilter
RegisterGlobalHouseTopicFilter = support.registerGlobalHouseTopicFilter
RegisterHouseTopicClickHook = support.registerHouseTopicClickHook
RegisterGlobalHouseTopicClickHook = support.registerGlobalHouseTopicClickHook
RegisterRestFoodCostHook = support.registerRestFoodCostHook
RegisterGlobalRestFoodCostHook = support.registerGlobalRestFoodCostHook
RegisterGameplayActionHook = support.registerGameplayActionHook
RegisterGlobalGameplayActionHook = support.registerGlobalGameplayActionHook
RegisterMapRefillHook = support.registerMapRefillHook
RegisterGlobalMapRefillHook = support.registerGlobalMapRefillHook
RegisterMapTransitionHook = support.registerMapTransitionHook
RegisterGlobalMapTransitionHook = support.registerGlobalMapTransitionHook
RegisterMonsterKilledHook = support.registerMonsterKilledHook
RegisterGlobalMonsterKilledHook = support.registerGlobalMonsterKilledHook
RegisterMonsterDamageHook = support.registerMonsterDamageHook
RegisterGlobalMonsterDamageHook = support.registerGlobalMonsterDamageHook
RegisterChestOpenHook = support.registerChestOpenHook
RegisterGlobalChestOpenHook = support.registerGlobalChestOpenHook
RegisterInventoryOpenHook = support.registerInventoryOpenHook
RegisterGlobalInventoryOpenHook = support.registerGlobalInventoryOpenHook
IsFlying = support.isFlying
IsInvisible = support.isInvisible
HasFollowerProfession = support.hasFollowerProfession
RemoveFollowerProfession = support.removeFollowerProfession
HasFollowerNpc = support.hasFollowerNpc
AddFollowerNpc = support.addFollowerNpc
RemoveFollowerNpc = support.removeFollowerNpc
CurrentGameMinutes = support.currentGameMinutes
NPCText = support.npcText
CurrentContinent = support.currentContinent
AdvanceGameMinutes = support.advanceGameMinutes
GetRuntimeVariable = support.getRuntimeVariable
SetRuntimeVariable = support.setRuntimeVariable
CurrentEventSpellId = support.currentEventSpellId
GetPartyVariable = support.getPartyVariable
SetPartyVariable = support.setPartyVariable
GetClassId = support.getClassId
GetClassName = support.getClassName
GetPlayerClass = support.getPlayerClass
GetPlayerClassName = support.getPlayerClassName
SetPlayerClass = support.setPlayerClass
PlayerItemCount = support.playerItemCount
PlayerHasItem = support.playerHasItem
GivePlayerItem = support.givePlayerItem
PlayerKnowsSpell = support.playerKnowsSpell
RemovePlayerItem = support.removePlayerItem
ApplyLichTransformation = support.applyLichTransformation
GetClassSkillCap = support.getClassSkillCap
CanClassLearnSkill = support.canClassLearnSkill
CanPlayerLearnSkill = support.canPlayerLearnSkill
PlayerClassMatches = support.playerClassMatches
ApplyPlayerRewards = support.applyPlayerRewards
PromotePlayers = support.promotePlayers
ApplyLocalMonsterRelations = support.applyLocalMonsterRelations
SetNPCName = support.setNpcName
SetNPCPicture = support.setNpcPicture
SetNPCProfession = support.setNpcProfession
SetGlobalMetadata = support.setGlobalMetadata
exportTableEntries(support.varTag)
Players = support.players
FacetBits = support.facetBits
MonsterBits = support.monsterBits
ItemType = support.itemType
Damage = support.damage
Skills = support.skills
SkillCheck = support.skillCheck
DoorAction = support.doorAction
ActorKillCheck = support.actorKillCheck

const = const or {}
const.FacetBits = support.facetBits
const.MonsterBits = support.monsterBits
const.ItemType = support.itemType
const.Damage = support.damage
const.Skills = support.skills
const.SkillCheck = support.skillCheck
const.DoorAction = support.doorAction
const.ActorKillCheck = support.actorKillCheck
const.HouseId = support.houseId
const.HouseAction = support.houseAction

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
saveCurrentLocation = support.saveCurrentLocation
hasSavedLocation = support.hasSavedLocation
moveToSavedLocation = support.moveToSavedLocation
clearSavedLocation = support.clearSavedLocation
setTransportRouteOverride = support.setTransportRouteOverride
clearTransportRouteOverride = support.clearTransportRouteOverride
castSpellFromTo = support.castSpellFromTo
pickRandomOption = support.pickRandomOption
setMapMetadata = support.setMapMetadata
setGlobalMetadata = support.setGlobalMetadata
registerMapTimerEvent = support.registerMapTimerEvent
registerNpcEnterHook = support.registerNpcEnterHook
registerNpcExitHook = support.registerNpcExitHook
registerHouseTopicFilter = support.registerHouseTopicFilter
registerHouseTopicClickHook = support.registerHouseTopicClickHook
registerRestFoodCostHook = support.registerRestFoodCostHook
registerGameplayActionHook = support.registerGameplayActionHook
registerMapRefillHook = support.registerMapRefillHook
registerInventoryOpenHook = support.registerInventoryOpenHook
isFlying = support.isFlying
isInvisible = support.isInvisible
hasFollowerNpc = support.hasFollowerNpc
addFollowerNpc = support.addFollowerNpc
removeFollowerNpc = support.removeFollowerNpc
currentGameMinutes = support.currentGameMinutes
getRuntimeVariable = support.getRuntimeVariable
setRuntimeVariable = support.setRuntimeVariable
currentEventSpellId = support.currentEventSpellId
getPartyVariable = support.getPartyVariable
setPartyVariable = support.setPartyVariable
getClassId = support.getClassId
getClassName = support.getClassName
getPlayerClass = support.getPlayerClass
getPlayerClassName = support.getPlayerClassName
setPlayerClass = support.setPlayerClass
playerItemCount = support.playerItemCount
playerHasItem = support.playerHasItem
playerKnowsSpell = support.playerKnowsSpell
removePlayerItem = support.removePlayerItem
applyLichTransformation = support.applyLichTransformation
getClassSkillCap = support.getClassSkillCap
canClassLearnSkill = support.canClassLearnSkill
canPlayerLearnSkill = support.canPlayerLearnSkill
playerClassMatches = support.playerClassMatches
applyPlayerRewards = support.applyPlayerRewards
promotePlayers = support.promotePlayers
applyLocalMonsterRelations = support.applyLocalMonsterRelations
