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
    evt.EnterHouse(177) -- Overdune's House
    return
end, "Overdune's House")

RegisterEvent(12, "Overdune's House", nil, "Overdune's House")

RegisterEvent(13, "Pole's Hovel", function()
    evt.EnterHouse(337) -- Pole's Hovel
    return
end, "Pole's Hovel")

RegisterEvent(14, "Pole's Hovel", nil, "Pole's Hovel")

RegisterEvent(15, "Hovel of Greenstorm", function()
    evt.EnterHouse(336) -- Hovel of Greenstorm
    return
end, "Hovel of Greenstorm")

RegisterEvent(16, "Hovel of Greenstorm", nil, "Hovel of Greenstorm")

RegisterEvent(17, "Hobert's Hovel", function()
    evt.EnterHouse(335) -- Hobert's Hovel
    return
end, "Hobert's Hovel")

RegisterEvent(18, "Hobert's Hovel", nil, "Hobert's Hovel")

RegisterEvent(19, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
    return
end, "Hovel of Mist")

RegisterEvent(20, "Hovel of Mist", nil, "Hovel of Mist")

RegisterEvent(21, "Talion's Hovel", function()
    evt.EnterHouse(333) -- Talion's Hovel
    return
end, "Talion's Hovel")

RegisterEvent(22, "Talion's Hovel", nil, "Talion's Hovel")

RegisterEvent(23, "Stone's Hovel", function()
    evt.EnterHouse(331) -- Stone's Hovel
    return
end, "Stone's Hovel")

RegisterEvent(24, "Stone's Hovel", nil, "Stone's Hovel")

RegisterEvent(25, "Hearthsworn Hovel", function()
    evt.EnterHouse(332) -- Hearthsworn Hovel
    return
end, "Hearthsworn Hovel")

RegisterEvent(26, "Hearthsworn Hovel", nil, "Hearthsworn Hovel")

RegisterEvent(27, "Schmecker's Hovel", function()
    evt.EnterHouse(339) -- Schmecker's Hovel
    return
end, "Schmecker's Hovel")

RegisterEvent(28, "Schmecker's Hovel", nil, "Schmecker's Hovel")

RegisterEvent(29, "Tarent Hovel", function()
    evt.EnterHouse(338) -- Tarent Hovel
    return
end, "Tarent Hovel")

RegisterEvent(30, "Tarent Hovel", nil, "Tarent Hovel")

RegisterEvent(31, "Thistlebone Residence", function()
    evt.EnterHouse(479) -- Thistlebone Residence
    return
end, "Thistlebone Residence")

RegisterEvent(32, "Thistlebone Residence", nil, "Thistlebone Residence")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Rock", function()
    evt.OpenChest(11)
    return
end, "Rock")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
end, "Chest")

RegisterEvent(101, "Drink from the well", function()
    if not IsAtLeast(BaseEndurance, 16) then
        AddValue(BaseEndurance, 2)
        evt.StatusText("Endurance +2 (Permanent)")
        SetAutonote(254) -- Well in the village of Rust gives a permanent Endurance bonus up to an Endurance of 16.
        return
    end
    evt.StatusText("Refreshing")
    return
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
            SetAutonote(255) -- Fountain in the village of Rust in the Ironsand Desert gives 200 gold if the total gold on party and in the bank is less than 100.
        end
    return
    end
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(103, "Drink from the well", function()
    evt.StatusText("Refreshing")
    return
end, "Drink from the well")

RegisterEvent(150, "Obelisk", function()
    if IsQBitSet(QBit(189)) then return end -- Obelisk Area 4
    evt.StatusText("thornskey")
    SetAutonote(19) -- Obelisk message #3: thornskey
    SetQBit(QBit(189)) -- Obelisk Area 4
    return
end, "Obelisk")

RegisterEvent(179, "Self Study", function()
    evt.EnterHouse(141) -- Self Study
    return
end, "Self Study")

RegisterEvent(180, "Self Study", nil, "Self Study")

RegisterEvent(181, "Guild Caravans", function()
    evt.EnterHouse(56) -- Guild Caravans
    return
end, "Guild Caravans")

RegisterEvent(182, "Guild Caravans", nil, "Guild Caravans")

RegisterEvent(189, "Placeholder", function()
    evt.EnterHouse(104) -- Placeholder
    return
end, "Placeholder")

RegisterEvent(190, "Placeholder", nil, "Placeholder")

RegisterEvent(191, "Parched Throat", function()
    evt.EnterHouse(110) -- Parched Throat
    return
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
    return
end)

RegisterEvent(490, "Legacy event 490", function()
    local randomStep = PickRandomOption(490, 2, {2, 2, 3, 3, 3, 3})
    if randomStep == 2 then
        evt.PlaySound(325, -6848, 3776)
    end
    return
end)

RegisterEvent(494, "Cactus", function()
    if IsQBitSet(QBit(278)) then -- Reagant spout area 4
        return
    elseif IsAtLeast(PerceptionSkill, 3) then
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
    if not IsAtLeast(PerceptionSkill, 5) then return end
    local randomStep = PickRandomOption(495, 4, {5, 7, 9, 11})
    if randomStep == 5 then
        evt.SummonItem(2138, 1728, -3776, 1008, 1000, 1, true)
    elseif randomStep == 7 then
        evt.SummonItem(2139, 1728, -3776, 1008, 1000, 1, true)
    elseif randomStep == 9 then
        evt.SummonItem(2140, 1728, -3776, 1008, 1000, 1, true)
    elseif randomStep == 11 then
        evt.SummonItem(2141, 1728, -3776, 1008, 1000, 1, true)
    end
    SetQBit(QBit(277)) -- Reagant spout area 4
    return
end, "Rock")

RegisterEvent(501, "Enter the Troll Tomb", function()
    evt.MoveToMap(-672, 768, -28, 256, 0, 0, 199, 0, "d13.blv")
    return
end, "Enter the Troll Tomb")

RegisterEvent(502, "Enter the Cyclops Larder", function()
    evt.MoveToMap(0, 0, 1, 1536, 0, 0, 200, 0, "d14.blv")
    return
end, "Enter the Cyclops Larder")

RegisterEvent(503, "Enter the Chain of Fire", function()
    evt.MoveToMap(-288, -768, 0, 520, 0, 0, 201, 0, "d15.blv")
    return
end, "Enter the Chain of Fire")

RegisterEvent(504, "Enter the Plane of Fire", function()
    evt.MoveToMap(99, -22056, 3057, 512, 0, 0, 220, 0, "ElemF.odm")
    return
end, "Enter the Plane of Fire")

RegisterEvent(505, "Enter the Chain of Fire", function()
    evt.MoveToMap(-12423, 4347, -135, 1544, 0, 0, 201, 0, "d15.blv")
    return
end, "Enter the Chain of Fire")

RegisterEvent(506, "Enter the Cave", function()
    evt.MoveToMap(2116, 9631, 1, 1296, 0, 0, 0, 0, "D48.blv")
    return
end, "Enter the Cave")
