-- Ironsand Desert
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapFaceMask = 0x08000000,
    onLoad = {1, 2, 3, 4},
    onLeave = {6, 7, 8, 9, 10},
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
    contextActions = {
    [11] = { kind = "enter_house", source = "opcode", houseId = 752, targetName = "Overdune's House" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 559, targetName = "Pole's Hovel" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 558, targetName = "Hovel of Greenstorm" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 557, targetName = "Hobert's Hovel" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 556, targetName = "Hovel of Mist" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 555, targetName = "Talion's Hovel" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 553, targetName = "Stone's Hovel" },
    [25] = { kind = "enter_house", source = "opcode", houseId = 554, targetName = "Hearthsworn Hovel" },
    [27] = { kind = "enter_house", source = "opcode", houseId = 561, targetName = "Schmecker's Hovel" },
    [29] = { kind = "enter_house", source = "opcode", houseId = 560, targetName = "Tarent Hovel" },
    [31] = { kind = "enter_house", source = "opcode", houseId = 698, targetName = "Thistlebone Residence" },
    [81] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [82] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [83] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [84] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [85] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [86] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [87] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [88] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [89] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [90] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [91] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [92] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [93] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [94] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [95] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [96] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [97] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [98] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [99] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [100] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [101] = { kind = "well", source = "title" },
    [102] = { kind = "well", source = "title" },
    [103] = { kind = "well", source = "title" },
    [150] = { kind = "obelisk", source = "title" },
    [179] = { kind = "enter_house", source = "opcode", houseId = 187, targetName = "Self Study" },
    [181] = { kind = "enter_house", source = "opcode", houseId = 454, targetName = "Guild Caravans" },
    [189] = { kind = "enter_house", source = "opcode", houseId = 778, targetName = "Placeholder" },
    [191] = { kind = "enter_house", source = "opcode", houseId = 231, targetName = "Parched Throat" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "d13.blv", targetName = "Troll Tomb" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "d14.blv", targetName = "Cyclops Larder" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "d15.blv", targetName = "Chain of Fire" },
    [504] = { kind = "travel", source = "opcode", targetMap = "elemf.odm", targetName = "Plane of Fire" },
    [505] = { kind = "enter_dungeon", source = "opcode", targetMap = "d15.blv", targetName = "Chain of Fire" },
    [506] = { kind = "enter_dungeon", source = "opcode", targetMap = "d48.blv", targetName = "Ilsingore's Cave" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 479, sourceEventId = 479, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 20 },
    { eventId = 490, sourceEventId = 490, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 15 },
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(60)) then -- Party visits Ironsand After QuestBit 25 set.
        return
    elseif IsQBitSet(QBit(25)) then -- Find a witness to the lake of fire's formation. Bring him back to the merchant guild in Alvar. - Given and taken by Bastian Lourdrin (area 3).
        SetQBit(QBit(60)) -- Party visits Ironsand After QuestBit 25 set.
        return
    else
        return
    end
end)

RegisterNoOpEvent(2, nil)

RegisterNoOpEvent(3, nil)

RegisterNoOpEvent(4, nil)

RegisterNoOpEvent(6, nil)

RegisterNoOpEvent(7, nil)

RegisterNoOpEvent(8, nil)

RegisterNoOpEvent(9, nil)

RegisterNoOpEvent(10, nil)

RegisterEvent(11, "Overdune's House", function()
    evt.EnterHouse(752) -- Overdune's House
end, "Overdune's House")

RegisterEvent(12, "Overdune's House", nil, "Overdune's House")

RegisterEvent(13, "Pole's Hovel", function()
    evt.EnterHouse(559) -- Pole's Hovel
end, "Pole's Hovel")

RegisterEvent(14, "Pole's Hovel", nil, "Pole's Hovel")

RegisterEvent(15, "Hovel of Greenstorm", function()
    evt.EnterHouse(558) -- Hovel of Greenstorm
end, "Hovel of Greenstorm")

RegisterEvent(16, "Hovel of Greenstorm", nil, "Hovel of Greenstorm")

RegisterEvent(17, "Hobert's Hovel", function()
    evt.EnterHouse(557) -- Hobert's Hovel
end, "Hobert's Hovel")

RegisterEvent(18, "Hobert's Hovel", nil, "Hobert's Hovel")

RegisterEvent(19, "Hovel of Mist", function()
    evt.EnterHouse(556) -- Hovel of Mist
end, "Hovel of Mist")

RegisterEvent(20, "Hovel of Mist", nil, "Hovel of Mist")

RegisterEvent(21, "Talion's Hovel", function()
    evt.EnterHouse(555) -- Talion's Hovel
end, "Talion's Hovel")

RegisterEvent(22, "Talion's Hovel", nil, "Talion's Hovel")

RegisterEvent(23, "Stone's Hovel", function()
    evt.EnterHouse(553) -- Stone's Hovel
end, "Stone's Hovel")

RegisterEvent(24, "Stone's Hovel", nil, "Stone's Hovel")

RegisterEvent(25, "Hearthsworn Hovel", function()
    evt.EnterHouse(554) -- Hearthsworn Hovel
end, "Hearthsworn Hovel")

RegisterEvent(26, "Hearthsworn Hovel", nil, "Hearthsworn Hovel")

RegisterEvent(27, "Schmecker's Hovel", function()
    evt.EnterHouse(561) -- Schmecker's Hovel
end, "Schmecker's Hovel")

RegisterEvent(28, "Schmecker's Hovel", nil, "Schmecker's Hovel")

RegisterEvent(29, "Tarent Hovel", function()
    evt.EnterHouse(560) -- Tarent Hovel
end, "Tarent Hovel")

RegisterEvent(30, "Tarent Hovel", nil, "Tarent Hovel")

RegisterEvent(31, "Thistlebone Residence", function()
    evt.EnterHouse(698) -- Thistlebone Residence
end, "Thistlebone Residence")

RegisterEvent(32, "Thistlebone Residence", nil, "Thistlebone Residence")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Rock", function()
    evt.OpenChest(11)
end, "Rock")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(BaseEndurance, 16) then
        AddValue(BaseEndurance, 2)
        evt.StatusText("Endurance +2 (Permanent)")
        SetAutonote(215) -- Well in the village of Rust gives a permanent Endurance bonus up to an Endurance of 16.
        return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(102, "Drink from the well", function()
    if not IsAtLeast(MapVar(31), 2) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing")
            return
        elseif IsAtLeast(BankGold, 99) then
            evt.StatusText("Refreshing")
        else
            AddValue(Gold, 200)
            AddValue(MapVar(31), 1)
            SetAutonote(216) -- Fountain in the village of Rust in the Ironsand Desert gives 200 gold if the total gold on party and in the bank is less than 100.
        end
    return
    end
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
end, "Drink from the well")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(189)) then return end -- Obelisk Area 4
    evt.StatusText("thornskey")
    SetAutonote(10) -- Obelisk message #3: thornskey
    SetQBit(QBit(189)) -- Obelisk Area 4
end, "Obelisk")

RegisterEvent(179, "Self Study", function()
    evt.EnterHouse(187) -- Self Study
end, "Self Study")

RegisterEvent(180, "Self Study", nil, "Self Study")

RegisterEvent(181, "Guild Caravans", function()
    evt.EnterHouse(454) -- Guild Caravans
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(189, "Placeholder", function()
    evt.EnterHouse(778) -- Placeholder
end, "Placeholder")

RegisterEvent(190, "Placeholder", nil, "Placeholder")

RegisterEvent(191, "Parched Throat", function()
    evt.EnterHouse(231) -- Parched Throat
end, "Parched Throat")

RegisterEvent(192, "Parched Throat", nil, "Parched Throat")

RegisterEvent(401, "Troll Tomb", nil, "Troll Tomb")

RegisterEvent(402, "Cyclops Larder", nil, "Cyclops Larder")

RegisterEvent(403, "Chain of Fire", nil, "Chain of Fire")

RegisterEvent(404, "A Cave", nil, "A Cave")

RegisterEvent(405, "Gate to the Plane of Fire", nil, "Gate to the Plane of Fire")

RegisterEvent(406, "Destroyed Building", nil, "Destroyed Building")

RegisterEvent(479, nil, function()
    local randomStep = PickRandomOption(479, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.PlaySound(327, -8128, -2496)
    elseif randomStep == 4 then
        evt.PlaySound(327, -2048, 1344)
    elseif randomStep == 6 then
        evt.PlaySound(327, -1216, -7680)
    elseif randomStep == 8 then
        evt.PlaySound(327, -10528, -15168)
    elseif randomStep == 10 then
        evt.PlaySound(327, 3520, -14112)
    end
end)

RegisterEvent(490, nil, function()
    local randomStep = PickRandomOption(490, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, -6848, 3776)
    end
end)

RegisterEvent(494, "Cactus", function()
    if IsQBitSet(QBit(278)) then -- Reagant spout area 4
        return
    elseif IsAtLeast(DisarmTrapSkill, 3) then
        local randomStep = PickRandomOption(494, 4, {5, 7, 9, 11, 13})
        if randomStep == 5 then
            evt.SummonItem(200, -7616, -4160, 504, 1000, 1, true) -- Widowsweep Berries
        elseif randomStep == 7 then
            evt.SummonItem(205, -7616, -4160, 504, 1000, 1, true) -- Phima Root
        elseif randomStep == 9 then
            evt.SummonItem(210, -7616, -4160, 504, 1000, 1, true) -- Poppy Pod
        elseif randomStep == 11 then
            evt.SummonItem(215, -7616, -4160, 504, 1000, 1, true) -- Mushroom
        elseif randomStep == 13 then
            evt.SummonItem(220, -7616, -4160, 504, 1000, 1, true) -- Potion Bottle
        end
        SetQBit(QBit(278)) -- Reagant spout area 4
        return
    else
        return
    end
end, "Cactus")

RegisterEvent(495, "Rock", function()
    if IsQBitSet(QBit(277)) then return end -- Reagant spout area 4
    if not IsAtLeast(DisarmTrapSkill, 5) then return end
    local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11})
    if randomStep == 5 then
        evt.SummonItem(2138, 1728, -3776, 1008, 1000, 1, true) -- Diary Page
    elseif randomStep == 7 then
        evt.SummonItem(2139, 1728, -3776, 1008, 1000, 1, true) -- Page from Agar's Journal
    elseif randomStep == 9 then
        evt.SummonItem(2140, 1728, -3776, 1008, 1000, 1, true) -- Remains of a Journal
    elseif randomStep == 11 then
        evt.SummonItem(2141, 1728, -3776, 1008, 1000, 1, true) -- Letter from the Dragon Riders
    end
    SetQBit(QBit(277)) -- Reagant spout area 4
end, "Rock")

RegisterEvent(501, "Enter the Troll Tomb", function()
    evt.MoveToMap(-672, 768, -28, 256, 0, 0, 358, 1, "d13.blv") -- Troll Tomb
end, "Enter the Troll Tomb")

RegisterEvent(502, "Enter the Cyclops Larder", function()
    evt.MoveToMap(0, 0, 1, 1536, 0, 0, 359, 1, "d14.blv") -- Cyclops Larder
end, "Enter the Cyclops Larder")

RegisterEvent(503, "Enter the Chain of Fire", function()
    evt.MoveToMap(-288, -768, 0, 520, 0, 0, 360, 1, "d15.blv") -- Chain of Fire
end, "Enter the Chain of Fire")

RegisterEvent(504, "Enter the Plane of Fire", function()
    evt.MoveToMap(99, -22056, 3057, 512, 0, 0, 350, 1, "elemf.odm") -- Plane of Fire
end, "Enter the Plane of Fire")

RegisterEvent(505, "Enter the Chain of Fire", function()
    evt.MoveToMap(-12423, 4347, -135, 1544, 0, 0, 360, 1, "d15.blv") -- Chain of Fire
end, "Enter the Chain of Fire")

RegisterEvent(506, "Enter the Cave", function()
    evt.MoveToMap(2116, 9631, 1, 1296, 0, 0, 0, 3, "d48.blv") -- Ilsingore's Cave
end, "Enter the Cave")

