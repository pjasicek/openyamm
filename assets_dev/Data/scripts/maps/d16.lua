-- Dragon Hunter's Camp
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
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    if IsQBitSet(QBit(22)) then
        evt.SetMonGroupBit(22, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(23, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(43, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        return
    elseif IsQBitSet(QBit(234)) then
        if not IsAtLeast(Counter(9), 1344) then
            evt.SetMonGroupBit(22, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(23, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(43, MonsterBits.Hostile, 1)
            SetValue(MapVar(11), 2)
            return
        end
        evt.SetMonGroupBit(22, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(23, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(43, MonsterBits.Hostile, 0)
        ClearQBit(QBit(234))
    else
        evt.SetMonGroupBit(22, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(23, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(43, MonsterBits.Hostile, 0)
        ClearQBit(QBit(234))
    end
return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterEvent(9, "Legacy event 9", function()
    if IsQBitSet(QBit(21)) then
        return
    elseif IsQBitSet(QBit(158)) then
        return
    else
        if not evt.CheckMonstersKilled(2, 42, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 43, 0, false) then return end
        if not evt.CheckMonstersKilled(2, 44, 0, false) then return end
        if not IsQBitSet(QBit(159)) then
            SetQBit(QBit(159))
            evt.SummonMonsters(1, 1, 64, 1888, 1, 0, 1, 0)
            evt.SetMonGroupBit(1, MonsterBits.Invisible, 1)
            return
        end
        SetQBit(QBit(158))
        SetQBit(QBit(225))
        ClearQBit(QBit(225))
        evt.StatusText("You have killed all of the Dragon Hunters")
        return
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if IsQBitSet(QBit(21)) then
        evt.MoveNPC(19, 0)
        evt.MoveNPC(65, 175)
        evt.MoveNPC(64, 179)
        if IsQBitSet(QBit(234)) then
            return
        elseif IsAtLeast(MapVar(11), 2) then
            SetQBit(QBit(234))
            SetValue(Counter(9), 0)
            return
        else
            return
        end
    elseif IsQBitSet(QBit(234)) then
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(234))
        SetValue(Counter(9), 0)
        return
    else
        return
    end
end)

RegisterEvent(11, "Bookshelf", function()
    evt.SetDoorState(1, 0)
    return
end, "Bookshelf")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(2, 0)
    return
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(3, 0)
    return
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(4, 0)
    return
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(5, 0)
    return
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, 0)
    return
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(7, 0)
    return
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(8, 0)
    return
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(9, 0)
    return
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(10, 0)
    return
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(11, 0)
    return
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(12, 0)
    return
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, 0)
    return
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, 0)
    return
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, 0)
    return
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(16, 0)
    return
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(17, 0)
    return
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, 0)
    return
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, 0)
    return
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, 0)
    return
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, 0)
    return
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, 0)
    return
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, 0)
    return
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, 0)
    return
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, 0)
    return
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, 0)
    return
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, 0)
    return
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, 0)
    return
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, 0)
    return
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, 0)
    return
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, 0)
    return
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, 0)
    return
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, 0)
    return
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, 0)
    return
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, 0)
    return
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, 0)
    return
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, 0)
    return
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, 0)
    return
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, 0)
    return
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, 0)
    return
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, 0)
    return
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, 0)
    return
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, 0)
    return
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, 0)
    return
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, 0)
    return
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, 0)
    return
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, 0)
    return
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, 0)
    return
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, 0)
    return
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, 0)
    return
end, "Door")

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

RegisterEvent(201, "Charles Quixote's House", function()
    evt.EnterHouse(179) -- Charles Quixote's House
    return
end, "Charles Quixote's House")

RegisterEvent(401, "Crate", nil, "Crate")

RegisterEvent(402, "Bookshelf", nil, "Bookshelf")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(316, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    evt.SpeakNPC(40) -- Guard
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
    return
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(22, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(23, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(43, MonsterBits.Hostile, 1)
    SetValue(MapVar(11), 2)
    return
end)

RegisterEvent(501, "Leave the Dragon Hunter's Camp", function()
    evt.MoveToMap(8909, -15194, 640, 512, 0, 0, 0, 0, "Out05.odm")
    return
end, "Leave the Dragon Hunter's Camp")

