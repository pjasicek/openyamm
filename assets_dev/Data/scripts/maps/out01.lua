-- Dagger Wound Island
-- normalized from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4},
    openedChestIds = {
        [81] = {0, 3},
        [82] = {1},
        [83] = {2},
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
    castSpellIds = {6, 9, 136},
    timers = {
        { eventId = 456, repeating = true, intervalGameMinutes = 15, remainingGameMinutes = 15 },
        { eventId = 460, repeating = true, intervalGameMinutes = 15, remainingGameMinutes = 15 },
        { eventId = 463, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
        { eventId = 468, repeating = true, intervalGameMinutes = 20, remainingGameMinutes = 20 },
        { eventId = 469, repeating = true, intervalGameMinutes = 20, remainingGameMinutes = 20 },
        { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
        { eventId = 500, repeating = false, targetHour = 10, intervalGameMinutes = 600, remainingGameMinutes = 60 },
    },
})

local QBIT_FIRST_TELEPORTER_POWERED = QBit(1)
local QBIT_SECOND_TELEPORTER_POWERED = QBit(2)
local QBIT_SIEGE_RESOLVED = QBit(6)
local QBIT_TELEPORTER_ACCESS_GRANTED = QBit(8)
local QBIT_TEMPLE_DOOR_CONDITION_A = QBit(36)
local QBIT_TEMPLE_DOOR_CONDITION_B = QBit(38)
local QBIT_ABANDONED_TEMPLE_VISITED = QBit(185)
local QBIT_OBELISK_VISITED = QBit(186)
local QBIT_ISLAND_STATE_INITIALIZED = QBit(226)
local QBIT_TEMPLE_BACK_EXIT_UNLOCKED = QBit(227)
local QBIT_FIRST_STORY_GREETING_SHOWN = QBit(232)
local QBIT_NORTH_BUOY_VISITED = QBit(268)
local QBIT_SOUTH_BUOY_VISITED = QBit(269)
local QBIT_PALM_TREE_HARVESTED = QBit(270)
local QBIT_FLOWER_HARVESTED = QBit(271)
local QBIT_ABANDONED_TEMPLE_LOAD_FLAG = QBit(401)
local QBIT_PIRATE_SHIP_LOAD_FLAG = QBit(407)

local MAPVAR_BLOOD_DROP_HIDDEN_WELL_STATE = MapVar(29)

local villageHouses = {
    { enterEventId = 11, secondaryEventId = 12, houseId = 224, hint = "Hiss' Hut" },
    { enterEventId = 13, secondaryEventId = 14, houseId = 225, hint = "Rohtnax's House" },
    { enterEventId = 15, secondaryEventId = 16, houseId = 226, hint = "Tisk's Hut" },
    { enterEventId = 17, secondaryEventId = 18, houseId = 227, hint = "Thadin's House" },
    { enterEventId = 19, secondaryEventId = 20, houseId = 228, hint = "House of Ich" },
    { enterEventId = 21, secondaryEventId = 22, houseId = 229, hint = "Languid's Hut" },
    { enterEventId = 23, secondaryEventId = 24, houseId = 230, hint = "House of Thistle" },
    { enterEventId = 25, secondaryEventId = 26, houseId = 231, hint = "Zevah's Hut" },
    { enterEventId = 27, secondaryEventId = 28, houseId = 232, hint = "Isthric's House" },
    { enterEventId = 29, secondaryEventId = 30, houseId = 233, hint = "Bone's House" },
    { enterEventId = 31, secondaryEventId = 32, houseId = 234, hint = "Lasatin's Hut" },
    { enterEventId = 33, secondaryEventId = 34, houseId = 235, hint = "Menasaur's House" },
    { enterEventId = 35, secondaryEventId = 36, houseId = 236, hint = "Husk's Hut" },
    { enterEventId = 37, secondaryEventId = 38, houseId = 237, hint = "Talimere's Hut" },
    { enterEventId = 39, secondaryEventId = 40, houseId = 238, hint = "House of Reshie" },
    { enterEventId = 41, secondaryEventId = 42, houseId = 239, hint = "House" },
    { enterEventId = 43, secondaryEventId = 44, houseId = 240, hint = "Long-Tail's Hut" },
    { enterEventId = 45, secondaryEventId = 46, houseId = 241, hint = "Aislen's House" },
    { enterEventId = 47, secondaryEventId = 48, houseId = 242, hint = "House of Grivic" },
    { enterEventId = 49, secondaryEventId = 50, houseId = 243, hint = "Ush's Hut" },
}

local serviceHouses = {
    { enterEventId = 171, secondaryEventId = 172, houseId = 1, hint = "True Mettle" },
    { enterEventId = 173, secondaryEventId = 174, houseId = 15, hint = "The Tannery" },
    { enterEventId = 175, secondaryEventId = 176, houseId = 29, hint = "Fearsome Fetishes" },
    { enterEventId = 177, secondaryEventId = 178, houseId = 42, hint = "Herbal Elixirs" },
    { enterEventId = 179, secondaryEventId = 180, houseId = 139, hint = "Cures and Curses" },
    { enterEventId = 183, secondaryEventId = 184, houseId = 63, hint = "The Windling" },
    { enterEventId = 185, secondaryEventId = 186, houseId = 74, hint = "Mystic Medicine" },
    { enterEventId = 187, secondaryEventId = 188, houseId = 89, hint = "Rites of Passage" },
    { enterEventId = 191, secondaryEventId = 192, houseId = 107, hint = "The Grog and Grub" },
    { enterEventId = 193, secondaryEventId = 194, houseId = 128, hint = "The Some Place Safe" },
    { enterEventId = 197, secondaryEventId = 198, houseId = 173, hint = "Clan Leader's Hall" },
    { enterEventId = 199, secondaryEventId = 200, houseId = 185, hint = "The Adventurer's Inn" },
}

local simpleChestEvents = {
    { eventId = 82, chestId = 1, title = "Open chest 1", hint = "Chest" },
    { eventId = 83, chestId = 2, title = "Open chest 2", hint = "Chest" },
    { eventId = 85, chestId = 4, title = "Open chest 4", hint = "Chest" },
    { eventId = 86, chestId = 5, title = "Open chest 5", hint = "Chest" },
    { eventId = 87, chestId = 6, title = "Open chest 6", hint = "Chest" },
    { eventId = 88, chestId = 7, title = "Open chest 7", hint = "Chest" },
    { eventId = 89, chestId = 8, title = "Open chest 8", hint = "Chest" },
    { eventId = 90, chestId = 9, title = "Open chest 9", hint = "Chest" },
    { eventId = 91, chestId = 10, title = "Open chest 10", hint = "Chest" },
    { eventId = 92, chestId = 11, title = "Open chest 11", hint = "Chest" },
    { eventId = 93, chestId = 12, title = "Open crate 12", hint = "Open Crate" },
    { eventId = 94, chestId = 13, title = "Open crate 13", hint = "Open Crate" },
    { eventId = 95, chestId = 14, title = "Open crate 14", hint = "Open Crate" },
    { eventId = 96, chestId = 15, title = "Open crate 15", hint = "Open Crate" },
    { eventId = 97, chestId = 16, title = "Open crate 16", hint = "Open Crate" },
    { eventId = 98, chestId = 17, title = "Open crate 17", hint = "Open Crate" },
    { eventId = 99, chestId = 18, title = "Open crate 18", hint = "Open Crate" },
    { eventId = 100, chestId = 19, title = "Open crate 19", hint = "Open Crate" },
}

local hoverOnlyMarkers = {
    { eventId = 401, title = "Abandoned Temple marker", hint = "Abandoned Temple" },
    { eventId = 402, title = "Regnan Pirate Outpost marker", hint = "Regnan Pirate Outpost" },
    { eventId = 403, title = "Uplifted Library marker", hint = "Uplifted Library" },
    { eventId = 404, title = "Plane of Earth gate marker", hint = "Gate to the Plane of Earth" },
    { eventId = 405, title = "Pirate Ship marker", hint = "Pirate Ship" },
    { eventId = 406, title = "Pirate Ship marker", hint = "Pirate Ship" },
    { eventId = 407, title = "Pirate Ship marker", hint = "Pirate Ship" },
    { eventId = 408, title = "Landing Craft marker", hint = "Landing Craft" },
    { eventId = 449, title = "Fountain marker", hint = "Fountain" },
    { eventId = 450, title = "Well marker", hint = "Well" },
    { eventId = 464, title = "Sealed crate marker", hint = "Sealed Crate" },
}

-- On-load setup.

RegisterEvent(1, "Reveal the temple door if the teleport network is active", function()
    if not IsQBitSet(QBIT_SECOND_TELEPORTER_POWERED) then
        return
    end

    evt.SetFacetBit(10, FacetBits.Invisible, 0)
    evt.SetFacetBit(10, FacetBits.Untouchable, 0)
end)

RegisterEvent(2, "Update siege aftermath state and temple approach", function()
    if IsQBitSet(QBIT_SIEGE_RESOLVED) then
        evt.SetFacetBit(20, FacetBits.Invisible, 1)
        evt.SetFacetBit(20, FacetBits.Untouchable, 1)
        evt.SetMonGroupBit(14, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)
        -- NPC group 12 "Misc Group for Riki(M2)" -> news 13
        -- "With the Pirate Outpost defeated our homes are once again safe!  Thank you!"
        evt.SetNPCGroupNews(12, 13)
        -- NPC group 13 "Misc Group for Riki(M3)" -> news 13
        -- "With the Pirate Outpost defeated our homes are once again safe!  Thank you!"
        evt.SetNPCGroupNews(13, 13)
        -- NPC group 1 "Peasants on Main Island of Dagger Wound" -> news 2
        -- "Our thanks for defeating the pirates!  Now if you could only do something about the mountain of fire!"
        evt.SetNPCGroupNews(1, 2)
    else
        -- NPC group 12 "Misc Group for Riki(M2)" -> news 12
        -- "Help us!  If we do not push the pirates off the island all will be lost!"
        evt.SetNPCGroupNews(12, 12)
        -- NPC group 13 "Misc Group for Riki(M3)" -> news 12
        -- "Help us!  If we do not push the pirates off the island all will be lost!"
        evt.SetNPCGroupNews(13, 12)
    end

    if IsQBitSet(QBIT_TEMPLE_DOOR_CONDITION_A) or IsQBitSet(QBIT_TEMPLE_DOOR_CONDITION_B) then
        evt.SetFacetBit(25, FacetBits.Invisible, 0)
        evt.SetFacetBit(25, FacetBits.Untouchable, 0)
        evt.SetFacetBit(26, FacetBits.Untouchable, 1)
        return
    end

    evt.SetFacetBit(25, FacetBits.Invisible, 1)
    evt.SetFacetBit(25, FacetBits.Untouchable, 1)
end)

RegisterEvent(3, "Initialize first-visit quest bits for the island", function()
    if IsQBitSet(QBIT_ISLAND_STATE_INITIALIZED) then
        return
    end

    SetQBit(QBIT_ISLAND_STATE_INITIALIZED)
    SetQBit(QBIT_ABANDONED_TEMPLE_VISITED)
    SetQBit(QBIT_ABANDONED_TEMPLE_LOAD_FLAG)
    SetQBit(QBIT_PIRATE_SHIP_LOAD_FLAG)
end)

RegisterEvent(4, "Unused on-load placeholder", function()
end)

RegisterEvent(6, "Leave-map placeholder", function()
end)

RegisterEvent(7, "Leave-map placeholder", function()
end)

RegisterEvent(8, "Leave-map placeholder", function()
end)

RegisterEvent(9, "Leave-map placeholder", function()
end)

RegisterEvent(10, "Leave-map placeholder", function()
end)

-- Village houses.

for _, house in ipairs(villageHouses) do
    RegisterEvent(house.enterEventId, "Enter " .. house.hint, function()
        evt.EnterHouse(house.houseId)
    end, house.hint)

    RegisterEvent(house.secondaryEventId, house.hint .. " secondary trigger", function()
    end, house.hint)
end

-- Chests and crates.

RegisterEvent(81, "Open the paired chest", function()
    if HasPlayer(2) then
        evt.OpenChest(3)
    else
        evt.OpenChest(0)
    end
end, "Chest")

for _, chest in ipairs(simpleChestEvents) do
    RegisterEvent(chest.eventId, chest.title, function()
        evt.OpenChest(chest.chestId)
    end, chest.hint)
end

-- Wells, fountain, and obelisk.

RegisterEvent(101, "North well: temporary intellect bonus", function()
    if IsAtLeast(IntellectBonus, 15) then
        evt.StatusText("Refreshing")
        return
    end

    AddValue(IntellectBonus, 15)
    evt.StatusText("Intellect +15 (Temporary)")
    SetAutonote(245) -- Well in the village of Blood Drop on Dagger Wound Island gives a temporary Intellect bonus of 15.
end, "Drink from the well")

RegisterEvent(102, "South well: permanent luck bonus", function()
    if IsAtLeast(BaseLuck, 16) then
        evt.StatusText("Refreshing")
        return
    end

    AddValue(BaseLuck, 2)
    evt.StatusText("Luck +2 (Permanent)")
    SetAutonote(246) -- Well in the village of Blood Drop on Dagger Wound Island gives a  permanent Luck bonus up to a Luck of 16.
end, "Drink from the well")

RegisterEvent(103, "Hidden well: large gold reward once the luck requirement is met", function()
    if IsAtLeast(MAPVAR_BLOOD_DROP_HIDDEN_WELL_STATE, 2)
        or IsAtLeast(Gold, 99)
        or IsAtLeast(BankGold, 99)
        or not IsAtLeast(BaseLuck, 14)
    then
        evt.StatusText("Refreshing")
        return
    end

    AddValue(Gold, 1000)
    AddValue(MAPVAR_BLOOD_DROP_HIDDEN_WELL_STATE, 1)
    SetAutonote(247) -- Well in the village of Blood Drop on Dagger Wound Island gives 1000 gold if Luck is greater than 14 and total gold on party and in the bank is less than 100.
end, "Drink from the well")

RegisterEvent(104, "Healing fountain", function()
    if IsAtLeast(HasFullHP, 0) then
        evt.StatusText("Refreshing")
        return
    end

    AddValue(HP, 25)
    evt.StatusText("Your Wounds begin to Heal")
    SetAutonote(248) -- Fountain in the village of Blood Drop on Dagger Wound Island restores Hit Points.
end, "Drink from the fountain")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBIT_OBELISK_VISITED) then
        return
    end

    evt.StatusText("summerday")
    SetAutonote(25) -- Obelisk message #9: summerday
    SetQBit(QBIT_OBELISK_VISITED)
end, "Obelisk")

-- Shops, taverns, temples, and ships.

for _, house in ipairs(serviceHouses) do
    RegisterEvent(house.enterEventId, "Enter " .. house.hint, function()
        evt.EnterHouse(house.houseId)
    end, house.hint)

    RegisterEvent(house.secondaryEventId, house.hint .. " secondary trigger", function()
    end, house.hint)
end

-- Hover-only world points.

for _, marker in ipairs(hoverOnlyMarkers) do
    RegisterEvent(marker.eventId, marker.title, function()
    end, marker.hint)
end

-- Local teleports and map transitions.

RegisterEvent(451, "Beach landing transition", function()
    MoveToMap({-480, 5432, 384, 512, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(452, "Village return transition", function()
    MoveToMap({10123, 4488, 736, 0, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(453, "Activate the first island teleporter", function()
    if IsQBitSet(QBIT_FIRST_TELEPORTER_POWERED) then
        MoveToMap({-21528, -1384, 0, 512, 0, 0, 0, 0}) -- Dagger Wound Island
        return
    end

    evt.ForPlayer(Players.All)

    if not HasItem(617) then -- Power Stone
        evt.StatusText("You need a power stone to operate this teleporter")
        return
    end

    if not IsQBitSet(QBIT_TELEPORTER_ACCESS_GRANTED) then
        return
    end

    RemoveItem(617) -- Power Stone
    SetQBit(QBIT_FIRST_TELEPORTER_POWERED)
    MoveToMap({-21528, -1384, 0, 512, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(454, "Play Abandoned Temple entrance face animation", function()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Abandoned Temple")

RegisterEvent(455, "Reset current player event variable 121", function()
    evt.ForPlayer(Players.All)
    SetValue(121, 0)
end)

-- Artillery and bombardment.

RegisterEvent(456, "Random island artillery barrage", function()
    local barrageOrigin = Point(19872, -19824, 5084)
    CastSpellFromTo(9, 3, 11, barrageOrigin, PickRandomOption(456, 1, { -- Meteor Shower
        Point(-9216, -12848, 3000),
        Point(-9232, -7680, 3000),
        Point(-5872, -8832, 3000),
        Point(-7200, -4656, 3000),
        Point(-4960, -3440, 3000),
        Point(-3472, -6544, 3000),
    }))
    CastSpellFromTo(9, 3, 11, barrageOrigin, PickRandomOption(456, 13, { -- Meteor Shower
        Point(-96, -3568, 3000),
        Point(3184, -976, 3000),
        Point(912, 544, 3000),
        Point(2976, 2240, 3000),
        Point(6144, 832, 3000),
        Point(9376, -4416, 3000),
    }))
    CastSpellFromTo(9, 3, 11, barrageOrigin, PickRandomOption(456, 27, { -- Meteor Shower
        Point(12256, -8640, 3000),
        Point(5136, -14192, 3000),
        Point(6320, -15840, 3000),
        Point(7584, -20016, 3000),
        Point(-3504, -15744, 3000),
        Point(560, -9776, 3000),
    }))
end)

RegisterEvent(457, "Fire the north cannon", function()
    CastSpellFromTo(6, 1, 2, Point(8704, 2000, 686), Point(8704, 1965, 686)) -- Fireball
    CastSpellFromTo(136, 1, 2, Point(8704, 1965, 686), Point(8704, -2592, 686)) -- Cannonball
end, "Fire the Cannon !")

RegisterEvent(458, "Fire the center cannon", function()
    CastSpellFromTo(6, 1, 2, Point(15872, 1500, 686), Point(15872, 1440, 686)) -- Fireball
    CastSpellFromTo(136, 1, 2, Point(15872, 1440, 686), Point(15872, -3100, 686)) -- Cannonball
end, "Fire the Cannon !")

RegisterEvent(459, "Fire the east cannon", function()
    CastSpellFromTo(6, 1, 2, Point(18400, 3584, 652), Point(18522, 3584, 652)) -- Fireball
    CastSpellFromTo(136, 1, 2, Point(18522, 3584, 652), Point(22880, 3584, 100)) -- Cannonball
end, "Fire the Cannon !")

RegisterEvent(460, "Timer-driven defensive cannon fire", function()
    if IsQBitSet(QBIT_SIEGE_RESOLVED) then
        return
    end

    if not evt.CheckMonstersKilled(4, 8, 1, true) then -- Couatl
        CastSpellFromTo(6, 1, 2, Point(15872, 1500, 686), Point(15872, 1440, 686)) -- Fireball
        CastSpellFromTo(136, 1, 2, Point(15872, 1440, 686), Point(15872, -3100, 100)) -- Cannonball
    end

    if not evt.CheckMonstersKilled(4, 9, 1, true) then -- Winged Serpent
        CastSpellFromTo(6, 1, 2, Point(1536, 16400, 682), Point(1536, 16480, 682)) -- Fireball
        CastSpellFromTo(136, 1, 2, Point(1536, 16480, 682), Point(1536, 21528, 100)) -- Cannonball
    end
end)

RegisterEvent(461, "Fire the south cannon", function()
    CastSpellFromTo(6, 1, 2, Point(1536, 16400, 682), Point(1536, 16480, 682)) -- Fireball
    CastSpellFromTo(136, 1, 2, Point(1536, 16480, 682), Point(1536, 21528, 100)) -- Cannonball
end, "Fire the Cannon !")

RegisterEvent(462, "Fire the west cannon", function()
    CastSpellFromTo(6, 1, 2, Point(-520, 15360, 682), Point(-610, 15360, 682)) -- Fireball
    CastSpellFromTo(136, 1, 2, Point(-610, 15360, 682), Point(-6320, 15360, 100)) -- Cannonball
end, "Fire the Cannon !")

RegisterEvent(463, "Spawn reinforcements when each assault group falls", function()
    if IsQBitSet(QBIT_SIEGE_RESOLVED) then
        return
    end

    if evt.CheckMonstersKilled(1, 10, 0, true) then -- Regnan Bandit
        evt.SummonMonsters(2, 2, 3, 776, -66192, 0, 10, 0)
        evt.SummonMonsters(2, 2, 3, 0, -5608, 0, 10, 0)
        evt.SummonMonsters(2, 2, 3, -656, -5696, 23, 10, 0)
        evt.SummonMonsters(2, 2, 3, -1280, -5720, 0, 10, 0)
    end

    if evt.CheckMonstersKilled(1, 11, 0, true) then -- Regnan Pirate
        evt.SummonMonsters(2, 2, 3, -2744, 4864, 176, 11, 0)
        evt.SummonMonsters(2, 2, 3, -2984, 4208, 561, 11, 0)
        evt.SummonMonsters(2, 2, 3, -3624, 4280, 400, 11, 0)
        evt.SummonMonsters(2, 2, 3, -3504, 4992, 74, 11, 0)
    end

    if evt.CheckMonstersKilled(1, 12, 0, true) then -- Regnan Brigadier
        evt.SummonMonsters(1, 2, 3, 5208, -736, 46, 12, 0)
        evt.SummonMonsters(1, 2, 3, 3120, 800, 226, 12, 0)
        evt.SummonMonsters(1, 2, 3, 3480, -2656, 88, 12, 0)
        evt.SummonMonsters(1, 2, 3, 2080, -2248, 539, 12, 0)
    end

    if evt.CheckMonstersKilled(1, 13, 0, true) then -- Regnan Crossbowman
        evt.SummonMonsters(1, 2, 3, -896, 55504, 384, 13, 0)
        evt.SummonMonsters(1, 2, 3, -104, 5328, 384, 13, 0)
        evt.SummonMonsters(1, 2, 3, -880, 4464, 510, 13, 0)
        evt.SummonMonsters(1, 2, 3, -1256, 5296, 241, 13, 0)
    end
end)

RegisterEvent(465, "Activate the western teleporter", function()
    if IsQBitSet(QBIT_FIRST_TELEPORTER_POWERED) then
        MoveToMap({-12496, -9728, 160, 512, 0, 0, 0, 0}) -- Dagger Wound Island
        return
    end

    evt.ForPlayer(Players.All)

    if not HasItem(617) then -- Power Stone
        evt.StatusText("You need a power stone to operate this teleporter")
        return
    end

    if not IsQBitSet(QBIT_TELEPORTER_ACCESS_GRANTED) then
        return
    end

    RemoveItem(617) -- Power Stone
    SetQBit(QBIT_FIRST_TELEPORTER_POWERED)
    MoveToMap({-12496, -9728, 160, 512, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(466, "Activate the northern teleporter", function()
    if IsQBitSet(QBIT_SECOND_TELEPORTER_POWERED) then
        MoveToMap({-13912, 14096, 0, 512, 0, 0, 0, 0}) -- Dagger Wound Island
        return
    end

    evt.ForPlayer(Players.All)

    if not HasItem(618) then -- Power Stone
        evt.StatusText("You need a power stone to operate this teleporter")
        return
    end

    RemoveItem(618) -- Power Stone
    SetQBit(QBIT_SECOND_TELEPORTER_POWERED)
    MoveToMap({-13912, 14096, 0, 512, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(467, "Activate the eastern teleporter", function()
    if IsQBitSet(QBIT_SECOND_TELEPORTER_POWERED) then
        MoveToMap({-18952, 8608, 96, 1536, 0, 0, 0, 0}) -- Dagger Wound Island
        return
    end

    evt.ForPlayer(Players.All)

    if not HasItem(618) then -- Power Stone
        evt.StatusText("You need a power stone to operate this teleporter")
        return
    end

    RemoveItem(618) -- Power Stone
    SetQBit(QBIT_SECOND_TELEPORTER_POWERED)
    MoveToMap({-18952, 8608, 96, 1536, 0, 0, 0, 0}) -- Dagger Wound Island
end)

RegisterEvent(468, "Random bombardment from the northern battery", function()
    if IsQBitSet(QBIT_SIEGE_RESOLVED) then
        return
    end

    local target = PickRandomOption(468, 2, {
        Point(15920, 2850, 977),
        Point(14789, 3735, 705),
        Point(13056, 3752, 736),
        Point(15926, 1274, 420),
        false,
    })

    if target then
        CastSpellFromTo(6, 1, 2, Point(16433, -3164, 180), target) -- Fireball
    end
end)

RegisterEvent(469, "Random bombardment from the southern battery", function()
    if IsQBitSet(QBIT_SIEGE_RESOLVED) then
        return
    end

    local target = PickRandomOption(469, 2, {
        Point(15920, 2850, 977),
        Point(14789, 3735, 705),
        Point(13056, 3752, 736),
        Point(15926, 1274, 420),
        false,
    })

    if target then
        CastSpellFromTo(6, 1, 2, Point(1496, 21593, 180), target) -- Fireball
    end
end)

RegisterEvent(470, "Unused map trigger", function()
end)

RegisterEvent(471, "Use the temple return exit and unlock the back entrance", function()
    MoveToMap({8760, 4408, 736, 1536, 0, 0, 0, 0}) -- Dagger Wound Island

    if not IsQBitSet(QBIT_TEMPLE_BACK_EXIT_UNLOCKED) then
        SetQBit(QBIT_TEMPLE_BACK_EXIT_UNLOCKED)
    end
end)

RegisterEvent(472, "Use the temple back entrance if it has been unlocked", function()
    if IsQBitSet(QBIT_TEMPLE_BACK_EXIT_UNLOCKED) then
        MoveToMap({21216, 18680, 0, 1024, 0, 0, 0, 0}) -- Dagger Wound Island
    end
end)

RegisterEvent(479, "Legacy timer placeholder", function()
end)

RegisterEvent(494, "Harvest the palm tree once perception is high enough", function()
    if IsQBitSet(QBIT_PALM_TREE_HARVESTED) or not IsAtLeast(PerceptionSkill, 3) then
        return
    end

    local itemId = PickRandomOption(494, 3, {200, 205, 210, 215, 220})
    -- Widowsweep Berries, Phima Root, Poppy Pod, Mushroom, Potion Bottle
    evt.SummonItem(itemId, 3896, 8080, 544, 1000, 1, true)
    SetQBit(QBIT_PALM_TREE_HARVESTED)
end, "Palm tree")

RegisterEvent(495, "Harvest the flower once perception is high enough", function()
    if IsQBitSet(QBIT_FLOWER_HARVESTED) or not IsAtLeast(PerceptionSkill, 5) then
        return
    end

    local itemId = PickRandomOption(495, 3, {2138, 2139, 2140, 2141})
    -- Unresolved legacy summon payloads
    evt.SummonItem(itemId, -18832, 5840, 330, 1000, 1, true)
    SetQBit(QBIT_FLOWER_HARVESTED)
end, "Flower")

RegisterEvent(497, "Mark the north buoy as visited", function()
    if IsQBitSet(QBIT_NORTH_BUOY_VISITED) or not IsAtLeast(BaseLuck, 13) then
        return
    end

    SetQBit(QBIT_NORTH_BUOY_VISITED)
    AddValue(SkillPoints, 2)
end, "Buoy")

RegisterEvent(498, "Mark the south buoy as visited", function()
    if IsQBitSet(QBIT_SOUTH_BUOY_VISITED) or not IsAtLeast(BaseLuck, 20) then
        return
    end

    SetQBit(QBIT_SOUTH_BUOY_VISITED)
    AddValue(SkillPoints, 5)
end, "Buoy")

RegisterEvent(500, "Play the first story greeting with NPC 31", function()
    if IsQBitSet(QBIT_FIRST_STORY_GREETING_SHOWN) then
        return
    end

    evt.SpeakNPC(31) -- S'ton
    SetQBit(QBIT_FIRST_STORY_GREETING_SHOWN)
end)

RegisterEvent(501, "Enter the Abandoned Temple", function()
    MoveToMap({-3008, -1696, 2464, 512, 0, 0, 191, 0, "\1D05.blv"}) -- Abandoned Temple
end, "Enter the Abandoned Temple")

RegisterEvent(502, "Enter the Regnan Pirate Outpost", function()
    MoveToMap({-7, -714, 1, 512, 0, 0, 192, 0, "\1D06.blv"}) -- Pirate Outpost
end, "Enter the Regnan Pirate Outpost")

RegisterEvent(503, "Enter the Uplifted Library", function()
    MoveToMap({-592, 624, 0, 552, 0, 0, 0, 0, "\1d40.blv"}) -- Uplifted Library
end, "Enter the Uplifted Library")

RegisterEvent(504, "Enter the rear temple entrance", function()
    MoveToMap({12704, 2432, 385, 0, 0, 0, 244, 1, "\1d05.blv"}) -- Abandoned Temple
end, "Enter the Abandoned Temple")

RegisterEvent(505, "Enter the Plane of Earth", function()
    MoveToMap({0, 0, 49, 512, 0, 0, 221, 0, "\1ElemE.blv"}) -- Plane of Earth
end, "Enter the Plane of Earth")
