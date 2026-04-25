-- Dragon Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
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
    if IsQBitSet(QBit(21)) then
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 1)
        return
    elseif IsQBitSet(QBit(233)) then
        if not IsAtLeast(88080640, 1344) then
            evt.SetMonGroupBit(44, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(11, MonsterBits.Invisible, 0)
            evt.SetMonGroupBit(11, MonsterBits.Hostile, 1)
            SetValue(MapVar(11), 2)
            evt.SetMonGroupBit(45, MonsterBits.Hostile, 1)
            return
        end
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0)
        ClearQBit(QBit(233))
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 0)
    else
        evt.SetMonGroupBit(44, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0)
        ClearQBit(QBit(233))
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(45, MonsterBits.Hostile, 0)
    end
return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterEvent(8, "Legacy event 8", function()
    if IsQBitSet(QBit(233)) then
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(233))
        SetValue(256, 0)
        return
    else
        return
    end
end)

RegisterEvent(9, "Legacy event 9", function()
    if IsQBitSet(QBit(22)) then
        return
    elseif IsQBitSet(QBit(155)) then
        return
    else
        if not evt.CheckMonstersKilled(2, 189, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 190, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 191, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 69, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 70, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 71, 0, false) then return end
        if not IsQBitSet(QBit(156)) then
            SetQBit(QBit(156))
            evt.SummonMonsters(2, 1, 223, -8, 170, 0, 1, 0)
            evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
            return
        end
        SetQBit(QBit(155))
        SetQBit(QBit(225))
        ClearQBit(QBit(225))
        evt.StatusText("You have killed all of the Dragons")
        return
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if not IsQBitSet(QBit(22)) then return end
    evt.MoveNPC(21, 0)
    evt.MoveNPC(66, 175)
    return
end)

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

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

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

RegisterEvent(131, "Cave Entrance", function()
    evt.EnterHouse(350) -- Ishton's Cave
    return
end, "Cave Entrance")

RegisterEvent(132, "Cave Entrance", function()
    evt.EnterHouse(351) -- Ithilgore's Cave
    return
end, "Cave Entrance")

RegisterEvent(133, "Cave Entrance", function()
    evt.EnterHouse(352) -- Scarwing's Cave
    return
end, "Cave Entrance")

RegisterEvent(201, "Dragon Leader's Cavern ", function()
    evt.EnterHouse(178) -- Dragon Leader's Cavern
    return
end, "Dragon Leader's Cavern ")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(316, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(39) -- Guard
    SetValue(MapVar(11), 1)
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
    return
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(44, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 0)
    evt.SetMonGroupBit(11, MonsterBits.Hostile, 1)
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(45, MonsterBits.Hostile, 1)
    return
end)

RegisterEvent(501, "Leave the dragon cave", function()
    evt.MoveToMap(6376, 12420, 1616, 0, 0, 0, 0, 0, "Out05.odm")
    return
end, "Leave the dragon cave")

