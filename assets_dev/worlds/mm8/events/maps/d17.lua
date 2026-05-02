-- Dragon Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
    onLeave = {6, 7, 8, 65535, 10},
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
    { eventId = 9, repeating = true, intervalGameMinutes = 10, remainingGameMinutes = 10 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    if IsQBitSet(QBit(21)) then -- Allied with Charles Quioxte's Dragon Hunters. Return Dragon Egg to Quixote done.
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        SetValue(MapVar(11), 2)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
        return
    elseif IsQBitSet(QBit(233)) then -- You have Pissed of the Dragons
        if not IsAtLeast(Counter(10), 1344) then
            evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
            evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
            evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
            SetValue(MapVar(11), 2)
            evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
            return
        end
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 0) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
        ClearQBit(QBit(233)) -- You have Pissed of the Dragons
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 0) -- actor group 45: spawn Wimpy Dragon A
        return
    else
        return
    end
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterEvent(8, "Legacy event 8", function()
    if IsQBitSet(QBit(233)) then -- You have Pissed of the Dragons
        return
    end
    if not IsAtLeast(MapVar(11), 2) then
        SetValue(MapVar(11), 0)
        return
    end
    SetQBit(QBit(233)) -- You have Pissed of the Dragons
    SetValue(Counter(10), 0)
end)

RegisterNoOpEvent(9, "Legacy event 9")

RegisterEvent(10, "Legacy event 10", function()
    if IsQBitSet(QBit(22)) then -- Allied with Dragons. Return Dragon Egg to Dragons done.
        evt.MoveNPC(17, 0) -- Deftclaw Redreaver -> removed
        evt.MoveNPC(53, 751) -- Deftclaw Redreaver -> Council Chamber Door
    end
end)

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

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

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

RegisterEvent(131, "Cave Entrance", function()
    evt.EnterHouse(572) -- Ishton's Cave
end, "Cave Entrance")

RegisterEvent(132, "Cave Entrance", function()
    evt.EnterHouse(573) -- Ithilgore's Cave
end, "Cave Entrance")

RegisterEvent(133, "Cave Entrance", function()
    evt.EnterHouse(574) -- Scarwing's Cave
end, "Cave Entrance")

RegisterEvent(201, "Dragon Leader's Cavern ", function()
    evt.EnterHouse(774) -- Dragon Leader's Cavern
end, "Dragon Leader's Cavern ")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(35) -- Guard
    SetValue(MapVar(11), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(44, MonsterBits.Hostile, 1) -- actor group 44: Dragon Flightleader, Great Wyrm, spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 0) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    evt.SetMonGroupBit(11, MonsterBits.Hostile, 1) -- actor group 11: spawn Dragon A, spawn Wimpy Dragon A
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(45, MonsterBits.Hostile, 1) -- actor group 45: spawn Wimpy Dragon A
end)

RegisterEvent(501, "Leave the dragon cave", function()
    evt.MoveToMap(6376, 12420, 1616, 0, 0, 0, 0, 1, "out05.odm") -- Garrote Gorge
end, "Leave the dragon cave")

RegisterEvent(65535, "", function()
end)

