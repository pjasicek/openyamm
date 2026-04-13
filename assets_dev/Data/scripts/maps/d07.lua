-- Smuggler's Cove
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
    castSpellIds = {41},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(10)) then
        if not IsQBitSet(QBit(231)) then
            evt.SetMonGroupBit(8, MonsterBits.Hostile, 0)
            evt.SetMonGroupBit(10, MonsterBits.Hostile, 0)
            ClearQBit(QBit(231))
            evt.SetMonGroupBit(8, MonsterBits.Invisible, 1)
            evt.SetMonGroupBit(11, MonsterBits.Invisible, 0)
            evt.SetMonGroupBit(11, MonsterBits.Hostile, 0)
            return
        end
        if not IsAtLeast(Counter(8), 1344) then
            evt.SetMonGroupBit(8, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
            SetValue(MapVar(11), 2)
            evt.SetMonGroupBit(8, MonsterBits.Invisible, 0)
            evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)
            return
        end
        evt.SetMonGroupBit(8, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 0)
        ClearQBit(QBit(231))
        evt.SetMonGroupBit(8, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(11, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(11, MonsterBits.Hostile, 0)
        return
    end
    evt.SetMonGroupBit(8, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(8, MonsterBits.Invisible, 0)
    evt.SetMonGroupBit(11, MonsterBits.Invisible, 1)
    return
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(231)) then
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(231))
        SetValue(Counter(8), 0)
        return
    else
        return
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, 0)
    return
end, "Door")

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

RegisterEvent(61, "Door", function()
    evt.SetDoorState(51, 0)
    evt.SetDoorState(52, 0)
    return
end, "Door")

RegisterEvent(62, "Door", function()
    evt.SetDoorState(53, 0)
    evt.SetDoorState(54, 0)
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

RegisterEvent(102, "Legacy event 102", function()
    evt.CastSpell(41, 2, 3, 9450, -13428, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(103, "Legacy event 103", function()
    evt.CastSpell(41, 2, 3, 9735, -12749, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(104, "Legacy event 104", function()
    evt.CastSpell(41, 2, 3, 10321, -12444, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(105, "Legacy event 105", function()
    evt.CastSpell(41, 2, 3, 10970, -12100, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(106, "Legacy event 106", function()
    evt.CastSpell(41, 2, 3, 10626, -11544, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(107, "Legacy event 107", function()
    evt.CastSpell(41, 2, 3, 10835, -10496, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(108, "Legacy event 108", function()
    evt.CastSpell(41, 2, 3, 10775, -9791, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(109, "Legacy event 109", function()
    evt.CastSpell(41, 2, 3, 9986, -9446, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(110, "Legacy event 110", function()
    evt.CastSpell(41, 2, 3, 11194, -9332, 832, 0, 0, 0) -- Rock Blast
    return
end)

RegisterEvent(201, "Wererat Smuggler Leader", function()
    evt.EnterHouse(174) -- Wererat Smuggler Leader
    evt.SetMonGroupBit(8, MonsterBits.Hostile, 0)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 0)
    SetValue(MapVar(11), 0)
    evt.SetMonGroupBit(8, MonsterBits.Invisible, 1)
    return
end, "Wererat Smuggler Leader")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(316, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    evt.SpeakNPC(41) -- Guard
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
    return
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(11), 2) then return end
    evt.SetMonGroupBit(8, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
    SetValue(MapVar(11), 2)
    evt.SetMonGroupBit(8, MonsterBits.Invisible, 0)
    evt.SetMonGroupBit(11, MonsterBits.Hostile, 1)
    return
end)

RegisterEvent(501, "Leave Smuggler's Cove", function()
    evt.MoveToMap(-22473, -11218, 2, 0, 0, 0, 0, 0, "Out02.odm")
    return
end, "Leave Smuggler's Cove")

