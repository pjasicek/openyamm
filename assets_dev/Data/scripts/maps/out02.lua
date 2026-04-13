-- Ravenshore
-- normalized from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
    openedChestIds = {
        [81] = {0},
        [82] = {1},
        [83] = {2},
        [84] = {3},
        [85] = {4},
        [86] = {5},
        [87] = {6},
        [88] = {7},
        [89] = {8},
        [90] = {9},
        [91] = {10},
        [92] = {11},
        [93] = {12},
        [94] = {13},
        [95] = {14},
        [96] = {15},
        [97] = {16},
        [98] = {17},
        [99] = {18},
        [100] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
        { eventId = 131, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
        { eventId = 132, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
        { eventId = 478, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
        { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    },
})

local QBIT_RAVENSHORE_INITIALIZED = QBit(93)
local QBIT_MERCHANT_HOUSE_BARRIER_OPEN = QBit(10)
local QBIT_RAVENSHORE_SAVED = QBit(56)
local QBIT_RAVENSHORE_UNDER_ATTACK = QBit(57)
local QBIT_RAVENSHORE_INVADERS_DEFEATED = QBit(58)
local QBIT_RAVENSHORE_VICTORY_FINALIZED = QBit(228)
local QBIT_HOSTEL_CONFLUX_KEY_BUILT = QBit(286)
local QBIT_DIRE_WOLF_DEN_CLEARED = QBit(140)
local QBIT_DIRE_WOLF_LEADER_SUMMONED = QBit(141)
local QBIT_RAVENSHORE_FOUNTAIN_DISCOVERED = QBit(180)
local QBIT_RAVENSHORE_OBELISK_READ = QBit(187)
local QBIT_TREE_CACHE_COLLECTED = QBit(272)
local QBIT_ROCK_CACHE_COLLECTED = QBit(273)
local QBIT_BUOY_VISITED = QBit(274)

local MAPVAR_RAVENSHORE_FOUNTAIN_REWARD_COUNT = MapVar(29)

local RAVENSHORE_SAVED_NEWS_GROUPS = {
    1, 3, 5, 6, 7, 16, 17, 18, 19, 20, 21, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35,
}

local conditionallySiegeLockedTownHousePairs = {
    { enterEventId = 11, hoverEventId = 12, houseId = 244, hint = "Wilburt's Hovel" },
    { enterEventId = 13, hoverEventId = 14, houseId = 245, hint = "Jack's Hovel" },
    { enterEventId = 15, hoverEventId = 16, houseId = 246, hint = "Iver's Estate" },
    { enterEventId = 17, hoverEventId = 18, houseId = 247, hint = "Pederton Place" },
    { enterEventId = 19, hoverEventId = 20, houseId = 248, hint = "Puddle's Hovel" },
    { enterEventId = 21, hoverEventId = 22, houseId = 249, hint = "Forgewright Estate" },
    { enterEventId = 23, hoverEventId = 24, houseId = 250, hint = "Apple Home" },
    { enterEventId = 25, hoverEventId = 26, houseId = 251, hint = "Treblid's Home" },
    { enterEventId = 27, hoverEventId = 28, houseId = 252, hint = "Holden's Hovel" },
    { enterEventId = 29, hoverEventId = 30, houseId = 253, hint = "Aznog's Hovel" },
    { enterEventId = 31, hoverEventId = 32, houseId = 254, hint = "Luodrin House" },
    { enterEventId = 33, hoverEventId = 34, houseId = 255, hint = "Applebee Estate" },
    { enterEventId = 35, hoverEventId = 36, houseId = 256, hint = "Archibald's Home" },
    { enterEventId = 37, hoverEventId = 38, houseId = 257, hint = "Arius' House" },
    { enterEventId = 39, hoverEventId = 40, houseId = 258, hint = "Deerhunter's House" },
    { enterEventId = 41, hoverEventId = 42, houseId = 259, hint = "Townsaver Hall" },
    { enterEventId = 43, hoverEventId = 44, houseId = 260, hint = "Jobber's Home" },
    { enterEventId = 45, hoverEventId = 46, houseId = 261, hint = "Maylander's House" },
    { enterEventId = 47, hoverEventId = 48, houseId = 262, hint = "Bluesawn Home" },
    { enterEventId = 49, hoverEventId = 50, houseId = 263, hint = "Quicktongue Estate" },
    { enterEventId = 51, hoverEventId = 52, houseId = 264, hint = "Laraselle Estate" },
    { enterEventId = 53, hoverEventId = 54, houseId = 265, hint = "Hillsman Cottage" },
    { enterEventId = 55, hoverEventId = 56, houseId = 266, hint = "Caverhill Estate" },
    { enterEventId = 57, hoverEventId = 58, houseId = 267, hint = "Reaver's Home" },
    { enterEventId = 59, hoverEventId = 60, houseId = 268, hint = "Temper Hall" },
    { enterEventId = 61, hoverEventId = 62, houseId = 269, hint = "Putnam's Home" },
    { enterEventId = 63, hoverEventId = 64, houseId = 270, hint = "Karrand's Cottage" },
    { enterEventId = 65, hoverEventId = 66, houseId = 271, hint = "Lathius' Home" },
    { enterEventId = 67, hoverEventId = 68, houseId = 272, hint = "Guild of Bounty Hunters" },
    { enterEventId = 69, hoverEventId = 70, houseId = 273, hint = "Botham Hall" },
    { enterEventId = 71, hoverEventId = 72, houseId = 274, hint = "Neblick's House" },
    { enterEventId = 73, hoverEventId = 74, houseId = 275, hint = "Stonecleaver Hall" },
    { enterEventId = 77, hoverEventId = 78, houseId = 277, hint = "Hostel" },
    { enterEventId = 79, hoverEventId = 80, houseId = 278, hint = "Brigham's Home" },
}

local conditionallySiegeLockedServiceHousePairs = {
    { enterEventId = 171, hoverEventId = 172, houseId = 2, hint = "Keen Edge" },
    { enterEventId = 173, hoverEventId = 174, houseId = 16, hint = "The Polished Shield" },
    { enterEventId = 175, hoverEventId = 176, houseId = 30, hint = "Needful Things" },
    { enterEventId = 177, hoverEventId = 178, houseId = 43, hint = "Apothecary" },
    { enterEventId = 179, hoverEventId = 180, houseId = 140, hint = "Vexation's Hexes" },
    { enterEventId = 181, hoverEventId = 182, houseId = 54, hint = "Guild Caravans" },
    { enterEventId = 183, hoverEventId = 184, houseId = 64, hint = "The Dauntless" },
    { enterEventId = 185, hoverEventId = 186, houseId = 75, hint = "Sanctum" },
    { enterEventId = 187, hoverEventId = 188, houseId = 90, hint = "Gymnasium" },
    { enterEventId = 191, hoverEventId = 192, houseId = 108, hint = "Kessel's Kantina" },
    { enterEventId = 193, hoverEventId = 194, houseId = 129, hint = "Steele's Vault" },
    { enterEventId = 195, hoverEventId = 196, houseId = 36, hint = "Caori's Curios" },
    { enterEventId = 197, hoverEventId = 198, houseId = 116, hint = "The Dancing Ogre" },
    { enterEventId = 199, hoverEventId = 200, houseId = 67, hint = "Wind" },
    { enterEventId = 201, hoverEventId = 202, houseId = 148, hint = "Self Guild" },
    { enterEventId = 209, hoverEventId = 210, houseId = 185, hint = "The Adventurer's Inn" },
}

local conditionallySiegeLockedOutskirtsHousePairs = {
    { enterEventId = 451, hoverEventId = 452, houseId = 279, hint = "House Memoria" },
    { enterEventId = 453, hoverEventId = 454, houseId = 280, hint = "House of Hawthorne" },
    { enterEventId = 455, hoverEventId = 456, houseId = 281, hint = "Lott's Family Home" },
    { enterEventId = 457, hoverEventId = 458, houseId = 282, hint = "House of Nosewort" },
    { enterEventId = 459, hoverEventId = 460, houseId = 286, hint = "Dotes Family Hovel" },
    { enterEventId = 461, hoverEventId = 462, houseId = 283, hint = "Hall of the Tracker" },
    { enterEventId = 463, hoverEventId = 464, houseId = 284, hint = "Hunter's Hovel" },
    { enterEventId = 465, hoverEventId = 466, houseId = 285, hint = "Dervish's Cottage" },
    { enterEventId = 467, hoverEventId = 468, houseId = 478, hint = "House Understone" },
}

local openHousePairs = {
    { enterEventId = 203, hoverEventId = 204, houseId = 187, hint = "Oracle" },
}

local simpleChestEvents = {
    { eventId = 81, chestId = 0, title = "Chest", hint = "Chest" },
    { eventId = 82, chestId = 1, title = "Chest", hint = "Chest" },
    { eventId = 83, chestId = 2, title = "Chest", hint = "Chest" },
    { eventId = 84, chestId = 3, title = "Chest", hint = "Chest" },
    { eventId = 85, chestId = 4, title = "Chest", hint = "Chest" },
    { eventId = 86, chestId = 5, title = "Chest", hint = "Chest" },
    { eventId = 87, chestId = 6, title = "Chest", hint = "Chest" },
    { eventId = 88, chestId = 7, title = "Chest", hint = "Chest" },
    { eventId = 89, chestId = 8, title = "Chest", hint = "Chest" },
    { eventId = 90, chestId = 9, title = "Chest", hint = "Chest" },
    { eventId = 91, chestId = 10, title = "Chest", hint = "Chest" },
    { eventId = 92, chestId = 11, title = "Tree", hint = "Tree" },
    { eventId = 93, chestId = 12, title = "Chest", hint = "Chest" },
    { eventId = 94, chestId = 13, title = "Chest", hint = "Chest" },
    { eventId = 95, chestId = 14, title = "Chest", hint = "Chest" },
    { eventId = 96, chestId = 15, title = "Chest", hint = "Chest" },
    { eventId = 97, chestId = 16, title = "Chest", hint = "Chest" },
    { eventId = 98, chestId = 17, title = "Chest", hint = "Chest" },
}

local hoverOnlyEvents = {
    { eventId = 401, hint = "Smuggler's Cove" },
    { eventId = 402, hint = "Dire Wolf Den" },
    { eventId = 403, hint = "Merchant House of Alvar" },
    { eventId = 404, hint = "Escaton's Crystal" },
    { eventId = 405, hint = "The Tomb of Lord Brinne" },
    { eventId = 406, hint = "Chapel of Eep" },
    { eventId = 407, hint = "Sealed Crate" },
    { eventId = 408, hint = "The Vault of Time" },
    { eventId = 449, hint = "Fountain" },
    { eventId = 450, hint = "Well" },
}

local function playLockedDoorAnimation()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end

local function registerConditionallySiegeLockedHousePairs(housePairs)
    for _, house in ipairs(housePairs) do
        local enterEventId = house.enterEventId
        local hoverEventId = house.hoverEventId
        local houseId = house.houseId
        local hint = house.hint

        RegisterEvent(enterEventId, hint, function()
            if IsQBitSet(QBIT_RAVENSHORE_UNDER_ATTACK) then
                playLockedDoorAnimation()
                return
            end

            evt.EnterHouse(houseId) -- hint
            return
        end, hint)

        RegisterEvent(hoverEventId, hint, function()
            return
        end, hint)
    end
end

local function registerOpenHousePairs(housePairs)
    for _, house in ipairs(housePairs) do
        local enterEventId = house.enterEventId
        local hoverEventId = house.hoverEventId
        local houseId = house.houseId
        local hint = house.hint

        RegisterEvent(enterEventId, hint, function()
            evt.EnterHouse(houseId) -- hint
            return
        end, hint)

        RegisterEvent(hoverEventId, hint, function()
            return
        end, hint)
    end
end

local function registerSimpleChestEvents(chestEvents)
    for _, chest in ipairs(chestEvents) do
        local eventId = chest.eventId
        local chestId = chest.chestId
        local title = chest.title
        local hint = chest.hint

        RegisterEvent(eventId, title, function()
            evt.OpenChest(chestId)
            return
        end, hint)
    end
end

local function registerHoverOnlyEvents(events)
    for _, eventData in ipairs(events) do
        RegisterNoOpEvent(eventData.eventId, eventData.hint, eventData.hint)
    end
end

local function setRavenshoreSavedNews()
    for _, groupId in ipairs(RAVENSHORE_SAVED_NEWS_GROUPS) do
        evt.SetNPCGroupNews(groupId, 10)
        -- "We will be forever in your debt!  You have saved Ravenshore and all of Jadame!"
    end
end

local function finalizeRavenshoreVictory()
    evt.SetNPCTopic(23, 0, 0)
    evt.SetNPCTopic(23, 1, 157)
    evt.SetNPCGreeting(23, 47)
    setRavenshoreSavedNews()

    evt.ForPlayer(Players.All)
    AddValue(Experience, 100000)

    ClearQBit(QBit(220))
    evt.MoveNPC(24, 0)
    evt.MoveNPC(25, 0)
    evt.SetFacetBit(30, FacetBits.Untouchable, 1)
    evt.SetFacetBit(30, FacetBits.Invisible, 1)
end

registerConditionallySiegeLockedHousePairs(conditionallySiegeLockedTownHousePairs)
registerSimpleChestEvents(simpleChestEvents)
registerConditionallySiegeLockedHousePairs(conditionallySiegeLockedServiceHousePairs)
registerHoverOnlyEvents(hoverOnlyEvents)
registerConditionallySiegeLockedHousePairs(conditionallySiegeLockedOutskirtsHousePairs)
registerOpenHousePairs(openHousePairs)

RegisterEvent(1, "Initialize Ravenshore state", function()
    if IsQBitSet(QBIT_RAVENSHORE_INITIALIZED) then
        return
    end

    SetQBit(QBIT_RAVENSHORE_INITIALIZED)
    ClearQBit(QBit(212))
    ClearQBit(QBit(213))
    return
end)

RegisterEvent(2, "Update Merchant House barrier", function()
    if not IsQBitSet(QBIT_MERCHANT_HOUSE_BARRIER_OPEN) then
        evt.SetFacetBit(10, FacetBits.Invisible, 1)
        evt.SetFacetBit(10, FacetBits.Untouchable, 1)
        evt.SetFacetBit(12, FacetBits.Untouchable, 1)
        return
    end

    evt.SetFacetBit(10, FacetBits.Invisible, 0)
    evt.SetFacetBit(10, FacetBits.Untouchable, 0)
    evt.SetFacetBit(12, FacetBits.Untouchable, 0)
    return
end)

RegisterEvent(3, "Finalize Ravenshore victory", function()
    if IsQBitSet(QBIT_RAVENSHORE_VICTORY_FINALIZED) then
        evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        evt.SetFacetBit(30, FacetBits.Invisible, 1)
        return
    end

    if not IsQBitSet(QBIT_RAVENSHORE_SAVED) then
        return
    end

    SetQBit(QBIT_RAVENSHORE_VICTORY_FINALIZED)
    AddValue(History(20), 0)
    evt.EnterHouse(600) -- Win

    evt.SetNPCTopic(53, 1, 115)
    evt.SetNPCGreeting(53, 38)
    evt.SetNPCTopic(68, 0, 143)
    evt.MoveNPC(68, 183)
    evt.SetNPCGreeting(68, 42)

    if not IsQBitSet(QBit(22)) then
        evt.SetNPCTopic(65, 0, 122)
        evt.SetNPCGreeting(65, 39)
        evt.MoveNPC(65, 179)
        evt.MoveNPC(64, 0)
    else
        evt.SetNPCTopic(66, 0, 129)
        evt.SetNPCGreeting(66, 40)
        evt.MoveNPC(66, 178)
    end

    if not IsQBitSet(QBit(19)) then
        evt.SetNPCTopic(67, 0, 136)
        evt.SetNPCGreeting(67, 41)
        evt.MoveNPC(67, 182)
    else
        evt.SetNPCTopic(69, 0, 150)
        evt.SetNPCGreeting(69, 43)
        evt.MoveNPC(69, 180)
        evt.MoveNPC(76, 0)
    end

    finalizeRavenshoreVictory()
    return
end)

RegisterEvent(4, "Update Ravenshore invaders", function()
    if IsQBitSet(QBIT_RAVENSHORE_INVADERS_DEFEATED)
        or not IsQBitSet(QBit(6))
        or IsQBitSet(QBit(37))
    then
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 1)
        return
    end

    evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
    SetQBit(QBIT_RAVENSHORE_UNDER_ATTACK)
    SetValue(BankGold, 0)
    return
end)

RegisterNoOpEvent(6, "OnLeaveMap")
RegisterNoOpEvent(7, "OnLeaveMap")
RegisterNoOpEvent(8, "OnLeaveMap")
RegisterNoOpEvent(9, "OnLeaveMap")
RegisterNoOpEvent(10, "OnLeaveMap")

RegisterEvent(75, "Build the Conflux Key", function()
    if IsQBitSet(QBIT_RAVENSHORE_UNDER_ATTACK) then
        playLockedDoorAnimation()
        return
    end

    if not IsQBitSet(QBIT_HOSTEL_CONFLUX_KEY_BUILT) then
        evt.ForPlayer(Players.All)

        if HasItem(606) and HasItem(607) and HasItem(608) and HasItem(609) then
            evt.ShowMovie("\"confluxkey\" ", false)

            evt.ForPlayer(Players.Current)
            RemoveItem(606) -- Heart of Fire
            RemoveItem(607) -- Heart of Water
            RemoveItem(608) -- Heart of Air
            RemoveItem(609) -- Heart of Earth
            GiveItem(610) -- Conflux Key

            SetQBit(QBit(46))
            ClearQBit(QBit(41))
            ClearQBit(QBit(42))
            ClearQBit(QBit(43))
            ClearQBit(QBit(44))
            SetQBit(QBit(45))

            evt.ForPlayer(Players.All)
            AddValue(Experience, 250000)
            SetAward(Award(13)) -- Built the Conflux Key.

            evt.SetNPCTopic(23, 0, 0)
            evt.SetNPCTopic(23, 1, 0)
            evt.SetNPCGreeting(23, 46)
            evt.SetNPCTopic(53, 1, 113)
            evt.SetNPCTopic(65, 0, 120)
            evt.SetNPCTopic(66, 0, 127)
            evt.SetNPCTopic(67, 0, 134)
            evt.SetNPCTopic(68, 0, 141)
            evt.SetNPCTopic(69, 0, 148)
            AddValue(History(17), 0)

            SetQBit(QBit(209))
            ClearQBit(QBit(205))
            ClearQBit(QBit(206))
            ClearQBit(QBit(207))
            ClearQBit(QBit(208))
            SetQBit(QBIT_HOSTEL_CONFLUX_KEY_BUILT)
        end
    end

    evt.EnterHouse(276) -- Hostel
    return
end, "Hostel")

RegisterEvent(99, "Champion's chest", function()
    evt.ForPlayer(Players.All)

    if not HasAward(Award(41)) then -- Arcomage Champion.
        playLockedDoorAnimation()
        return
    end

    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "The Vault of Time", function()
    evt.ForPlayer(Players.All)

    if not HasItem(661) then -- Emperor Thorn's Key
        playLockedDoorAnimation()
        return
    end

    evt.OpenChest(19)
    RemoveItem(661) -- Emperor Thorn's Key
    evt.SetFacetBit(15, FacetBits.Invisible, 1)
    evt.SetFacetBit(15, FacetBits.Untouchable, 1)
    return
end, "The Vault of Time")

RegisterEvent(101, "Ravenshore strength well", function()
    if not IsAtLeast(MightBonus, 25) then
        AddValue(MightBonus, 25)
        evt.StatusText("Might +25 (Temporary)")
        SetAutonote(249) -- Well in the city of Ravenshore gives a temporary Strength bonus of 25.
        return
    end

    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(102, "Ravenshore poison well", function()
    evt.StatusText("That was not so refreshing")
    SetValue(PoisonedYellow, 0)
    return
end, "Drink from the well")

RegisterEvent(103, "Ravenshore empty well", function()
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(104, "Ravenshore gold fountain", function()
    if not IsQBitSet(QBIT_RAVENSHORE_FOUNTAIN_DISCOVERED) then
        SetQBit(QBIT_RAVENSHORE_FOUNTAIN_DISCOVERED)
    end

    if IsAtLeast(MAPVAR_RAVENSHORE_FOUNTAIN_REWARD_COUNT, 2)
        or IsAtLeast(Gold, 199)
        or IsAtLeast(BankGold, 99)
    then
        evt.StatusText("Refreshing")
        return
    end

    AddValue(MAPVAR_RAVENSHORE_FOUNTAIN_REWARD_COUNT, 1)
    AddValue(Gold, 200)
    SetAutonote(250) -- Fountain in the city of Ravenshore gives 200 gold if the total gold on party and in the bank is less than 100.
    return
end, "Drink from the fountain")

RegisterEvent(131, "Check whether the Ravenshore invaders are defeated", function()
    if IsQBitSet(QBIT_RAVENSHORE_INVADERS_DEFEATED) or not IsQBitSet(QBIT_RAVENSHORE_UNDER_ATTACK) then
        return
    end

    if not evt.CheckMonstersKilled(1, 10, 0, true) then
        return
    end

    SetQBit(QBIT_RAVENSHORE_INVADERS_DEFEATED)
    SetQBit(QBit(225))
    SetQBit(QBit(225))
    evt.StatusText("The Invaders have been defeated!")
    ClearQBit(QBIT_RAVENSHORE_UNDER_ATTACK)
    return
end)

RegisterEvent(132, "Check whether the Dire Wolves are cleared", function()
    if IsQBitSet(QBIT_DIRE_WOLF_DEN_CLEARED) then
        return
    end

    if not evt.CheckMonstersKilled(2, 84, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 85, 0, false) then return end
    if not evt.CheckMonstersKilled(2, 86, 0, false) then return end

    if not IsQBitSet(QBIT_DIRE_WOLF_LEADER_SUMMONED) then
        SetQBit(QBIT_DIRE_WOLF_LEADER_SUMMONED)
        evt.SummonMonsters(3, 1, 1, -18208, 16256, 8, 1, 0)
        evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
        return
    end

    SetQBit(QBIT_DIRE_WOLF_DEN_CLEARED)
    evt.StatusText("You have killed all of the Dire Wolves")
    SetQBit(QBit(225))
    ClearQBit(QBit(225))
    return
end)

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBIT_RAVENSHORE_OBELISK_READ) then
        return
    end

    evt.StatusText("ethesunsh")
    SetAutonote(23) -- Obelisk message #7: ethesunsh
    SetQBit(QBIT_RAVENSHORE_OBELISK_READ)
    return
end, "Obelisk")

RegisterEvent(478, "Distant cannon rumble", function()
    if PickRandomOption(478, 2, {2, 2, 3, 3, 3, 3}) == 2 then
        evt.PlaySound(325, 17056, -12512)
    end
    return
end)

RegisterEvent(479, "Idle bombardment timer", function()
    PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
    return
end)

RegisterEvent(490, "Potion bottle tree cache", function()
    if not evt.CheckItemsCount(DecorVar(23), 1) then
        return
    end

    evt.RemoveItems(DecorVar(23))
    GiveItem(220) -- Potion Bottle
    return
end, "Tree")

RegisterEvent(491, "Launch pad", function()
    evt._SpecialJump(19661824, 220)
    return
end)

RegisterEvent(492, "Launch pad", function()
    evt._SpecialJump(19662336, 220)
    return
end)

RegisterEvent(493, "Launch pad", function()
    evt._SpecialJump(19660800, 220)
    return
end)

RegisterEvent(494, "Locked door", function()
    playLockedDoorAnimation()
    evt.StatusText("The door is locked")
    return
end, "Door")

RegisterEvent(495, "Hidden reagent tree", function()
    if IsQBitSet(QBIT_TREE_CACHE_COLLECTED) or not IsAtLeast(PerceptionSkill, 3) then
        return
    end

    local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11, 13})

    if randomStep == 5 then
        evt.SummonItem(200, 1376, 5312, 126, 1000, 1, true) -- Widowsweep Berries
    elseif randomStep == 7 then
        evt.SummonItem(205, 1376, 5312, 126, 1000, 1, true) -- Phima Root
    elseif randomStep == 9 then
        evt.SummonItem(210, 1376, 5312, 126, 1000, 1, true) -- Poppy Pod
    elseif randomStep == 11 then
        evt.SummonItem(215, 1376, 5312, 126, 1000, 1, true) -- Mushroom
    elseif randomStep == 13 then
        evt.SummonItem(220, 1376, 5312, 126, 1000, 1, true) -- Potion Bottle
    end

    SetQBit(QBIT_TREE_CACHE_COLLECTED)
    return
end, "Tree")

RegisterEvent(497, "Hidden potion rock", function()
    if IsQBitSet(QBIT_ROCK_CACHE_COLLECTED) or not IsAtLeast(PerceptionSkill, 7) then
        return
    end

    local randomStep = PickRandomOption(497, 4, {5, 7, 9, 11, 13, 15})

    if randomStep == 5 then
        evt.SummonItem(240, 11520, 14320, 992, 1000, 1, true) -- Might Boost
    elseif randomStep == 7 then
        evt.SummonItem(241, 11520, 14320, 992, 1000, 1, true) -- Intellect Boost
    elseif randomStep == 9 then
        evt.SummonItem(242, 11520, 14320, 992, 1000, 1, true) -- Personality Boost
    elseif randomStep == 11 then
        evt.SummonItem(243, 11520, 14320, 992, 1000, 1, true) -- Endurance Boost
    elseif randomStep == 13 then
        evt.SummonItem(244, 11520, 14320, 992, 1000, 1, true) -- Speed Boost
    elseif randomStep == 15 then
        evt.SummonItem(245, 11520, 14320, 992, 1000, 1, true) -- Accuracy Boost
    end

    SetQBit(QBIT_ROCK_CACHE_COLLECTED)
    return
end, "Rock")

RegisterEvent(499, "Buoy", function()
    if IsQBitSet(QBIT_BUOY_VISITED) or not IsAtLeast(BaseLuck, 20) then
        return
    end

    SetQBit(QBIT_BUOY_VISITED)
    AddToCounter(Counter(1), 5)
    return
end, "Buoy")

RegisterEvent(501, "Enter Smuggler's Cove", function()
    evt.MoveToMap(-3800, 623, 1, 2000, 0, 0, 193, 0, "D07.blv") -- Smuggler's Cove
    return
end, "Enter Smuggler's Cove")

RegisterEvent(502, "Enter the Dire Wolf Den", function()
    evt.MoveToMap(2157, 1003, 1, 1024, 0, 0, 194, 0, "D08.blv") -- Dire Wolf Den
    return
end, "Enter the Dire Wolf Den")

RegisterEvent(503, "Enter the Merchant House of Alvar", function()
    if not IsQBitSet(QBit(59)) then
        evt.SpeakNPC(3) -- Elgar Fellmoon
        return
    end

    evt.MoveToMap(320, -1290, 513, 512, 0, 0, 195, 0, "D09.blv") -- Merchant House of Alvar
    return
end, "Enter the Merchant House of Alvar")

RegisterEvent(504, "Enter Escaton's Crystal", function()
    evt.ForPlayer(Players.All)

    if not HasItem(610) then -- Conflux Key
        playLockedDoorAnimation()
        return
    end

    evt.MoveToMap(-1024, -1626, 0, 520, 0, 0, 196, 0, "D10.blv") -- Escaton's Crystal
    return
end, "Enter Escaton's Crystal")

RegisterEvent(505, "Enter the Merchant House of Alvar", function()
    evt.MoveToMap(-1752, 1370, 449, 0, 0, 0, 195, 0, "D09.blv") -- Merchant House of Alvar
    return
end, "Enter the Merchant House of Alvar")

RegisterEvent(506, "Enter the Tomb of Lord Brinne", function()
    evt.MoveToMap(0, -448, 0, 0, 0, 0, 0, 0, "D28.blv") -- The Tomb of Lord Brinne
    return
end, "Enter the Tomb of Lord Brinne")

RegisterEvent(507, "Enter the Chapel of Eep", function()
    evt.MoveToMap(-481, -2824, 321, 512, 0, 0, 0, 0, "D45.blv") -- Chapel of Eep
    return
end, "Enter the Chapel of Eep")
