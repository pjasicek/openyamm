-- Balthazar Lair
-- generated from legacy EVT/STR

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
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(23)) then
        evt.SetMonGroupBit(35, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(36, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(37, MonsterBits.Invisible, 0)
        evt.SetFacetBit(14, FacetBits.Invisible, 1)
        evt.SetFacetBit(14, FacetBits.Untouchable, 1)
        evt.SetFacetBit(15, FacetBits.Invisible, 0)
        evt.SetFacetBit(15, FacetBits.Untouchable, 0)
        evt.SetMonGroupBit(38, MonsterBits.Invisible, 0)
        evt.SetFacetBit(6, FacetBits.Invisible, 1)
        evt.SetFacetBit(6, FacetBits.Untouchable, 1)
        evt.SetFacetBit(7, FacetBits.Invisible, 1)
        evt.SetFacetBit(7, FacetBits.Untouchable, 1)
        evt.SetFacetBit(8, FacetBits.Invisible, 1)
        evt.SetFacetBit(8, FacetBits.Untouchable, 1)
        evt.SetFacetBit(9, FacetBits.Invisible, 1)
        evt.SetFacetBit(9, FacetBits.Untouchable, 1)
        evt.SetFacetBit(10, FacetBits.Invisible, 1)
        evt.SetFacetBit(10, FacetBits.Untouchable, 1)
        evt.SetFacetBit(11, FacetBits.Invisible, 1)
        evt.SetFacetBit(11, FacetBits.Untouchable, 1)
        evt.SetFacetBit(13, FacetBits.Invisible, 1)
        evt.SetFacetBit(13, FacetBits.Untouchable, 1)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        evt.SetFacetBit(2, FacetBits.Invisible, 1)
        evt.SetFacetBit(2, FacetBits.Untouchable, 1)
        evt.SetFacetBit(3, FacetBits.Invisible, 1)
        evt.SetFacetBit(3, FacetBits.Untouchable, 1)
        evt.SetFacetBit(4, FacetBits.Invisible, 1)
        evt.SetFacetBit(4, FacetBits.Untouchable, 1)
        evt.SetFacetBit(5, FacetBits.Invisible, 1)
        evt.SetFacetBit(5, FacetBits.Untouchable, 1)
        return
    elseif IsAtLeast(MapVar(11), 1) then
        evt.SetFacetBit(6, FacetBits.Invisible, 1)
        evt.SetFacetBit(6, FacetBits.Untouchable, 1)
        evt.SetFacetBit(7, FacetBits.Invisible, 1)
        evt.SetFacetBit(7, FacetBits.Untouchable, 1)
        evt.SetFacetBit(8, FacetBits.Invisible, 1)
        evt.SetFacetBit(8, FacetBits.Untouchable, 1)
        evt.SetFacetBit(9, FacetBits.Invisible, 1)
        evt.SetFacetBit(9, FacetBits.Untouchable, 1)
        evt.SetFacetBit(10, FacetBits.Invisible, 1)
        evt.SetFacetBit(10, FacetBits.Untouchable, 1)
        evt.SetFacetBit(11, FacetBits.Invisible, 1)
        evt.SetFacetBit(11, FacetBits.Untouchable, 1)
        evt.SetFacetBit(13, FacetBits.Invisible, 1)
        evt.SetFacetBit(13, FacetBits.Untouchable, 1)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        evt.SetFacetBit(2, FacetBits.Invisible, 1)
        evt.SetFacetBit(2, FacetBits.Untouchable, 1)
        evt.SetFacetBit(3, FacetBits.Invisible, 1)
        evt.SetFacetBit(3, FacetBits.Untouchable, 1)
        evt.SetFacetBit(4, FacetBits.Invisible, 1)
        evt.SetFacetBit(4, FacetBits.Untouchable, 1)
        evt.SetFacetBit(5, FacetBits.Invisible, 1)
        evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    else
        evt.SetMonGroupBit(35, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(36, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(37, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(38, MonsterBits.Invisible, 1)
    end
return
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(6, "Legacy event 6", function()
    if not IsQBitSet(QBit(23)) then return end
    evt.MoveNPC(13, 0)
    evt.MoveNPC(68, 175)
    return
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then
        return
    elseif IsAtLeast(MapVar(12), 1) then
        evt.SetFacetBit(1, FacetBits.Invisible, 0)
        evt.SetFacetBit(1, FacetBits.Untouchable, 0)
        evt.SetFacetBit(2, FacetBits.Invisible, 0)
        evt.SetFacetBit(2, FacetBits.Untouchable, 0)
        evt.SetFacetBit(3, FacetBits.Invisible, 0)
        evt.SetFacetBit(3, FacetBits.Untouchable, 0)
        evt.SetFacetBit(4, FacetBits.Invisible, 0)
        evt.SetFacetBit(4, FacetBits.Untouchable, 0)
        evt.SetFacetBit(5, FacetBits.Invisible, 0)
        evt.SetFacetBit(5, FacetBits.Untouchable, 0)
        evt.SetFacetBit(6, FacetBits.Invisible, 0)
        evt.SetFacetBit(6, FacetBits.Untouchable, 0)
        evt.SetFacetBit(7, FacetBits.Invisible, 0)
        evt.SetFacetBit(7, FacetBits.Untouchable, 0)
        evt.SetFacetBit(8, FacetBits.Invisible, 0)
        evt.SetFacetBit(8, FacetBits.Untouchable, 0)
        evt.SetFacetBit(9, FacetBits.Invisible, 0)
        evt.SetFacetBit(9, FacetBits.Untouchable, 0)
        evt.SetFacetBit(10, FacetBits.Invisible, 0)
        evt.SetFacetBit(10, FacetBits.Untouchable, 0)
        evt.SetFacetBit(11, FacetBits.Invisible, 0)
        evt.SetFacetBit(11, FacetBits.Untouchable, 0)
        evt.SetDoorState(1, 1)
        evt.SetDoorState(2, 1)
        evt.SetDoorState(3, 1)
        evt.SetDoorState(4, 1)
        evt.SetDoorState(5, 1)
        evt.SetDoorState(6, 1)
        evt.SetDoorState(7, 1)
        evt.SetDoorState(8, 1)
        evt.SetDoorState(9, 1)
        evt.SetDoorState(10, 1)
        evt.SetDoorState(11, 1)
        evt.SetDoorState(12, 1)
        SetValue(MapVar(12), 0)
    else
        evt.SetDoorState(1, 0)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        SetValue(MapVar(12), 1)
    end
return
end, "Lever")

RegisterEvent(12, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(2, 0)
    evt.SetFacetBit(2, FacetBits.Invisible, 1)
    evt.SetFacetBit(2, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(13, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(3, 0)
    evt.SetDoorState(4, 1)
    evt.SetFacetBit(3, FacetBits.Invisible, 1)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
    evt.SetFacetBit(4, FacetBits.Invisible, 0)
    evt.SetFacetBit(4, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(14, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(4, 0)
    evt.SetDoorState(3, 1)
    evt.SetFacetBit(4, FacetBits.Invisible, 1)
    evt.SetFacetBit(4, FacetBits.Untouchable, 1)
    evt.SetFacetBit(3, FacetBits.Invisible, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(15, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(5, 0)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(16, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, 0)
    evt.SetDoorState(7, 1)
    evt.SetDoorState(8, 1)
    evt.SetFacetBit(6, FacetBits.Invisible, 1)
    evt.SetFacetBit(6, FacetBits.Untouchable, 1)
    evt.SetFacetBit(7, FacetBits.Invisible, 0)
    evt.SetFacetBit(7, FacetBits.Untouchable, 0)
    evt.SetFacetBit(8, FacetBits.Invisible, 0)
    evt.SetFacetBit(8, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(17, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, 1)
    evt.SetDoorState(7, 0)
    evt.SetDoorState(8, 1)
    evt.SetFacetBit(6, FacetBits.Invisible, 0)
    evt.SetFacetBit(6, FacetBits.Untouchable, 0)
    evt.SetFacetBit(7, FacetBits.Invisible, 1)
    evt.SetFacetBit(7, FacetBits.Untouchable, 1)
    evt.SetFacetBit(8, FacetBits.Invisible, 0)
    evt.SetFacetBit(8, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(18, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, 1)
    evt.SetDoorState(7, 1)
    evt.SetDoorState(8, 0)
    evt.SetFacetBit(6, FacetBits.Invisible, 0)
    evt.SetFacetBit(6, FacetBits.Untouchable, 0)
    evt.SetFacetBit(7, FacetBits.Invisible, 0)
    evt.SetFacetBit(7, FacetBits.Untouchable, 0)
    evt.SetFacetBit(8, FacetBits.Invisible, 1)
    evt.SetFacetBit(8, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(19, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(9, 0)
    evt.SetDoorState(5, 1)
    evt.SetFacetBit(9, FacetBits.Invisible, 1)
    evt.SetFacetBit(9, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(20, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(10, 0)
    evt.SetDoorState(5, 1)
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(10, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(21, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(11, 0)
    evt.SetDoorState(5, 1)
    evt.SetFacetBit(11, FacetBits.Invisible, 1)
    evt.SetFacetBit(11, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
    return
end, "Lever")

RegisterEvent(22, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(12, 0)
    evt.SetDoorState(13, 0)
    evt.SetFacetBit(1, FacetBits.Invisible, 1)
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(2, FacetBits.Invisible, 1)
    evt.SetFacetBit(2, FacetBits.Untouchable, 1)
    evt.SetFacetBit(3, FacetBits.Invisible, 1)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
    evt.SetFacetBit(4, FacetBits.Invisible, 1)
    evt.SetFacetBit(4, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    evt.SetFacetBit(6, FacetBits.Invisible, 1)
    evt.SetFacetBit(6, FacetBits.Untouchable, 1)
    evt.SetFacetBit(7, FacetBits.Invisible, 1)
    evt.SetFacetBit(7, FacetBits.Untouchable, 1)
    evt.SetFacetBit(8, FacetBits.Invisible, 1)
    evt.SetFacetBit(8, FacetBits.Untouchable, 1)
    evt.SetFacetBit(9, FacetBits.Invisible, 1)
    evt.SetFacetBit(9, FacetBits.Untouchable, 1)
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(10, FacetBits.Untouchable, 1)
    evt.SetFacetBit(11, FacetBits.Invisible, 1)
    evt.SetFacetBit(11, FacetBits.Untouchable, 1)
    evt.SetFacetBit(13, FacetBits.Invisible, 1)
    evt.SetFacetBit(13, FacetBits.Untouchable, 1)
    ClearQBit(QBit(30))
    evt.ShowMovie("\"savemino\" ", false)
    SetValue(MapVar(11), 1)
    return
end, "Lever")

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

RegisterEvent(201, "Minotaur Leader's Room", function()
    evt.EnterHouse(183) -- Minotaur Leader's Room
    return
end, "Minotaur Leader's Room")

RegisterEvent(203, "Thanys' House", function()
    evt.EnterHouse(402) -- Thanys' House
    return
end, "Thanys' House")

RegisterEvent(204, "Thanys' House", function()
    return
end, "Thanys' House")

RegisterEvent(205, "Ferris' House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(403) -- Ferris' House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Ferris' House")

RegisterEvent(206, "Ferris' House", function()
    return
end, "Ferris' House")

RegisterEvent(207, "Flooded House", function()
    evt.EnterHouse(404) -- Flooded House
    return
end, "Flooded House")

RegisterEvent(208, "Flooded House", function()
    return
end, "Flooded House")

RegisterEvent(209, "Flooded House", function()
    evt.EnterHouse(404) -- Flooded House
    return
end, "Flooded House")

RegisterEvent(210, "Flooded House", function()
    return
end, "Flooded House")

RegisterEvent(211, "Weapon shop placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(406) -- Weapon shop placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Weapon shop placeholder")

RegisterEvent(212, "Weapon shop placeholder", function()
    return
end, "Weapon shop placeholder")

RegisterEvent(213, "Suretail House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(407) -- Suretail House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Suretail House")

RegisterEvent(214, "Suretail House", function()
    return
end, "Suretail House")

RegisterEvent(215, "Rionel's House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(408) -- Rionel's House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Rionel's House")

RegisterEvent(216, "Rionel's House", function()
    return
end, "Rionel's House")

RegisterEvent(217, "Armor shop placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(409) -- Armor shop placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Armor shop placeholder")

RegisterEvent(218, "Armor shop placeholder", function()
    return
end, "Armor shop placeholder")

RegisterEvent(219, "Magic shop placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(410) -- Magic shop placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Magic shop placeholder")

RegisterEvent(220, "Magic shop placeholder", function()
    return
end, "Magic shop placeholder")

RegisterEvent(221, "Spell shop placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(411) -- Spell shop placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Spell shop placeholder")

RegisterEvent(222, "Spell shop placeholder", function()
    return
end, "Spell shop placeholder")

RegisterEvent(223, "Ulbrecht's House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(412) -- Ulbrecht's House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Ulbrecht's House")

RegisterEvent(224, "Ulbrecht's House", function()
    return
end, "Ulbrecht's House")

RegisterEvent(225, "Senjac's House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(413) -- Senjac's House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Senjac's House")

RegisterEvent(226, "Senjac's House", function()
    return
end, "Senjac's House")

RegisterEvent(227, "Alchemist placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(414) -- Alchemist placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Alchemist placeholder")

RegisterEvent(228, "Alchemist placeholder", function()
    return
end, "Alchemist placeholder")

RegisterEvent(229, "Temple placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(415) -- Temple placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Temple placeholder")

RegisterEvent(230, "Temple placeholder", function()
    return
end, "Temple placeholder")

RegisterNoOpEvent(401, "Fountain", "Fountain")

RegisterEvent(451, "Drink from the Fountain", function()
    if not IsQBitSet(QBit(184)) then
        SetQBit(QBit(184))
    end
    if IsAtLeast(MaxHealth, 0) then return end
    AddValue(CurrentHealth, 25)
    evt.StatusText("Your wounds begin to heal")
    AddValue(IsIntellectMoreThanBase, 266)
    return
end, "Drink from the Fountain")

RegisterEvent(452, "Lotts' House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(416) -- Lotts' House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Lotts' House")

RegisterEvent(453, "Lotts' House", function()
    return
end, "Lotts' House")

RegisterEvent(454, "Hollyfield House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(417) -- Hollyfield House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Hollyfield House")

RegisterEvent(455, "Hollyfield House", function()
    return
end, "Hollyfield House")

RegisterEvent(456, "Tessalar's House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(418) -- Tessalar's House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Tessalar's House")

RegisterEvent(457, "Tessalar's House", function()
    return
end, "Tessalar's House")

RegisterEvent(458, "Stormeye's House", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(419) -- Stormeye's House
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Stormeye's House")

RegisterEvent(459, "Stormeye's House", function()
    return
end, "Stormeye's House")

RegisterEvent(460, "Bank placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(420) -- Bank placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Bank placeholder")

RegisterEvent(461, "Bank placeholder", function()
    return
end, "Bank placeholder")

RegisterEvent(462, "Training hall placeholder", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(421) -- Training hall placeholder
        return
    end
    evt.EnterHouse(404) -- Flooded House
    return
end, "Training hall placeholder")

RegisterEvent(463, "Training hall placeholder", function()
    return
end, "Training hall placeholder")

RegisterEvent(464, "Ayzar's Axes", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(6) -- Ayzar's Axes
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Ayzar's Axes")

RegisterEvent(465, "Ayzar's Axes", function()
    return
end, "Ayzar's Axes")

RegisterEvent(466, "Linked Mail", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(20) -- Linked Mail
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Linked Mail")

RegisterEvent(467, "Linked Mail", function()
    return
end, "Linked Mail")

RegisterEvent(468, "Amulets of Power", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(34) -- Amulets of Power
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Amulets of Power")

RegisterEvent(469, "Amulets of Power", function()
    return
end, "Amulets of Power")

RegisterEvent(470, "Perius' Powders", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(47) -- Perius' Powders
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Perius' Powders")

RegisterEvent(471, "Perius' Powders", function()
    return
end, "Perius' Powders")

RegisterEvent(472, "The Shaman", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(79) -- The Shaman
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "The Shaman")

RegisterEvent(473, "The Shaman", function()
    return
end, "The Shaman")

RegisterEvent(474, "Balthazar Academy", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(94) -- Balthazar Academy
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Balthazar Academy")

RegisterEvent(475, "Balthazar Academy", function()
    return
end, "Balthazar Academy")

RegisterEvent(476, "Bank of Balthazar", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(132) -- Bank of Balthazar
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Bank of Balthazar")

RegisterEvent(477, "Bank of Balthazar", function()
    return
end, "Bank of Balthazar")

RegisterEvent(478, "Guild of Mind", function()
    if IsQBitSet(QBit(23)) then
        evt.EnterHouse(145) -- Guild of Mind
        return
    end
    evt.EnterHouse(405) -- Flooded Shop
    return
end, "Guild of Mind")

RegisterEvent(479, "Guild of Mind", function()
    return
end, "Guild of Mind")

RegisterEvent(501, "Leave Balthazar Lair", function()
    evt.MoveToMap(-10869, -8850, 1985, 1024, 0, 0, 0, 0, "Out08.odm")
    return
end, "Leave Balthazar Lair")

RegisterEvent(502, "Leave Balthazar Lair", function()
    evt.MoveToMap(-12279, -12153, 2752, 1536, 0, 0, 0, 0, "Out08.odm")
    return
end, "Leave Balthazar Lair")

