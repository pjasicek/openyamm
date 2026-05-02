-- Ironsand Desert
-- generated from legacy EVT/STR

SetMapMetadata({
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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 479, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    { eventId = 490, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(60)) then -- Party visits Ironsand After QuestBit 25 set.
        return
    elseif IsQBitSet(QBit(25)) then -- Find a witness to the lake of fire's formation. Bring him back to the merchant guild in Alvar. - Given and taken by Bastian Lourdrin (area 3).
        SetQBit(QBit(60)) -- Party visits Ironsand After QuestBit 25 set.
        return
    else
        return
    end
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

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

RegisterEvent(479, "Legacy event 479", function()
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

RegisterEvent(490, "Legacy event 490", function()
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
            evt.SummonItem(200, -7616, -4160, 504, 1000, 1, true) -- Fae dust
        elseif randomStep == 7 then
            evt.SummonItem(205, -7616, -4160, 504, 1000, 1, true) -- Vial of Ooze endoplasm
        elseif randomStep == 9 then
            evt.SummonItem(210, -7616, -4160, 504, 1000, 1, true) -- Yellow Potion
        elseif randomStep == 11 then
            evt.SummonItem(215, -7616, -4160, 504, 1000, 1, true) -- Green Potion
        elseif randomStep == 13 then
            evt.SummonItem(220, -7616, -4160, 504, 1000, 1, true) -- Blue and Orange Potion
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

