-- Balthazar Lair
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
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.SetMonGroupBit(35, MonsterBits.Invisible, 0) -- actor group 35: Minotaur Peasant
        evt.SetMonGroupBit(36, MonsterBits.Invisible, 0) -- actor group 36: Minotaur Peasant
        evt.SetMonGroupBit(37, MonsterBits.Invisible, 0) -- actor group 37: Minotaur Peasant
        evt.SetFacetBit(14, FacetBits.Invisible, 1)
        evt.SetFacetBit(14, FacetBits.Untouchable, 1)
        evt.SetFacetBit(15, FacetBits.Invisible, 0)
        evt.SetFacetBit(15, FacetBits.Untouchable, 0)
        evt.SetMonGroupBit(38, MonsterBits.Invisible, 0) -- actor group 38: Minotaur Warrior
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
        evt.SetMonGroupBit(35, MonsterBits.Invisible, 1) -- actor group 35: Minotaur Peasant
        evt.SetMonGroupBit(36, MonsterBits.Invisible, 1) -- actor group 36: Minotaur Peasant
        evt.SetMonGroupBit(37, MonsterBits.Invisible, 1) -- actor group 37: Minotaur Peasant
        evt.SetMonGroupBit(38, MonsterBits.Invisible, 1) -- actor group 38: Minotaur Warrior
    end
return
end)

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.MoveNPC(13, 0) -- Masul -> removed
        evt.MoveNPC(55, 751) -- Masul -> Council Chamber Door
    end
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
        evt.SetDoorState(1, DoorAction.Close)
        evt.SetDoorState(2, DoorAction.Close)
        evt.SetDoorState(3, DoorAction.Close)
        evt.SetDoorState(4, DoorAction.Close)
        evt.SetDoorState(5, DoorAction.Close)
        evt.SetDoorState(6, DoorAction.Close)
        evt.SetDoorState(7, DoorAction.Close)
        evt.SetDoorState(8, DoorAction.Close)
        evt.SetDoorState(9, DoorAction.Close)
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(11, DoorAction.Close)
        evt.SetDoorState(12, DoorAction.Close)
        SetValue(MapVar(12), 0)
    else
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        SetValue(MapVar(12), 1)
    end
return
end, "Lever")

RegisterEvent(12, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetFacetBit(2, FacetBits.Invisible, 1)
    evt.SetFacetBit(2, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(13, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Close)
    evt.SetFacetBit(3, FacetBits.Invisible, 1)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
    evt.SetFacetBit(4, FacetBits.Invisible, 0)
    evt.SetFacetBit(4, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(14, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Close)
    evt.SetFacetBit(4, FacetBits.Invisible, 1)
    evt.SetFacetBit(4, FacetBits.Untouchable, 1)
    evt.SetFacetBit(3, FacetBits.Invisible, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(15, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(16, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, DoorAction.Open)
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetFacetBit(6, FacetBits.Invisible, 1)
    evt.SetFacetBit(6, FacetBits.Untouchable, 1)
    evt.SetFacetBit(7, FacetBits.Invisible, 0)
    evt.SetFacetBit(7, FacetBits.Untouchable, 0)
    evt.SetFacetBit(8, FacetBits.Invisible, 0)
    evt.SetFacetBit(8, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(17, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetFacetBit(6, FacetBits.Invisible, 0)
    evt.SetFacetBit(6, FacetBits.Untouchable, 0)
    evt.SetFacetBit(7, FacetBits.Invisible, 1)
    evt.SetFacetBit(7, FacetBits.Untouchable, 1)
    evt.SetFacetBit(8, FacetBits.Invisible, 0)
    evt.SetFacetBit(8, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(18, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(6, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetFacetBit(6, FacetBits.Invisible, 0)
    evt.SetFacetBit(6, FacetBits.Untouchable, 0)
    evt.SetFacetBit(7, FacetBits.Invisible, 0)
    evt.SetFacetBit(7, FacetBits.Untouchable, 0)
    evt.SetFacetBit(8, FacetBits.Invisible, 1)
    evt.SetFacetBit(8, FacetBits.Untouchable, 1)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(19, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetFacetBit(9, FacetBits.Invisible, 1)
    evt.SetFacetBit(9, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(20, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetFacetBit(10, FacetBits.Invisible, 1)
    evt.SetFacetBit(10, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(21, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetFacetBit(11, FacetBits.Invisible, 1)
    evt.SetFacetBit(11, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 0)
    evt.SetFacetBit(5, FacetBits.Untouchable, 0)
    SetValue(MapVar(12), 1)
end, "Lever")

RegisterEvent(22, "Lever", function()
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Open)
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
    ClearQBit(QBit(30)) -- Rescue the Minotaurs trapped in their lair in Ravage Roaming. - Given by MINOTAUR CLUE GUY (area 8). Turned off when minotaur leader is reached in Minotaur lair dungeon.
    evt.ShowMovie("\"savemino\"", true)
    SetValue(MapVar(11), 1)
end, "Lever")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, DoorAction.Open)
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(16, DoorAction.Open)
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, DoorAction.Open)
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, DoorAction.Open)
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, DoorAction.Open)
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, DoorAction.Open)
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, DoorAction.Open)
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, DoorAction.Open)
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, DoorAction.Open)
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, DoorAction.Open)
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, DoorAction.Open)
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, DoorAction.Open)
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, DoorAction.Open)
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, DoorAction.Open)
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, DoorAction.Open)
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, DoorAction.Open)
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, DoorAction.Open)
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, DoorAction.Open)
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, DoorAction.Open)
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, DoorAction.Open)
end, "Door")

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

RegisterEvent(201, "Minotaur Leader's Room", function()
    evt.EnterHouse(755) -- Minotaur Leader's Room
end, "Minotaur Leader's Room")

RegisterEvent(203, "Thanys' House", function()
    evt.EnterHouse(624) -- Thanys' House
end, "Thanys' House")

RegisterEvent(204, "Thanys' House", nil, "Thanys' House")

RegisterEvent(205, "Ferris' House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(625) -- Ferris' House
end, "Ferris' House")

RegisterEvent(206, "Ferris' House", nil, "Ferris' House")

RegisterEvent(207, "Flooded House", function()
    evt.EnterHouse(626) -- Flooded House
end, "Flooded House")

RegisterEvent(208, "Flooded House", nil, "Flooded House")

RegisterEvent(209, "Flooded House", function()
    evt.EnterHouse(626) -- Flooded House
end, "Flooded House")

RegisterEvent(210, "Flooded House", nil, "Flooded House")

RegisterEvent(211, "Weapon shop placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(628) -- Weapon shop placeholder
end, "Weapon shop placeholder")

RegisterEvent(212, "Weapon shop placeholder", nil, "Weapon shop placeholder")

RegisterEvent(213, "Suretail House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(629) -- Suretail House
end, "Suretail House")

RegisterEvent(214, "Suretail House", nil, "Suretail House")

RegisterEvent(215, "Rionel's House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(630) -- Rionel's House
end, "Rionel's House")

RegisterEvent(216, "Rionel's House", nil, "Rionel's House")

RegisterEvent(217, "Armor shop placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(631) -- Armor shop placeholder
end, "Armor shop placeholder")

RegisterEvent(218, "Armor shop placeholder", nil, "Armor shop placeholder")

RegisterEvent(219, "Magic shop placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(632) -- Magic shop placeholder
end, "Magic shop placeholder")

RegisterEvent(220, "Magic shop placeholder", nil, "Magic shop placeholder")

RegisterEvent(221, "Spell shop placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(633) -- Spell shop placeholder
end, "Spell shop placeholder")

RegisterEvent(222, "Spell shop placeholder", nil, "Spell shop placeholder")

RegisterEvent(223, "Ulbrecht's House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(634) -- Ulbrecht's House
end, "Ulbrecht's House")

RegisterEvent(224, "Ulbrecht's House", nil, "Ulbrecht's House")

RegisterEvent(225, "Senjac's House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(635) -- Senjac's House
end, "Senjac's House")

RegisterEvent(226, "Senjac's House", nil, "Senjac's House")

RegisterEvent(227, "Alchemist placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(636) -- Alchemist placeholder
end, "Alchemist placeholder")

RegisterEvent(228, "Alchemist placeholder", nil, "Alchemist placeholder")

RegisterEvent(229, "Temple placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(637) -- Temple placeholder
end, "Temple placeholder")

RegisterEvent(230, "Temple placeholder", nil, "Temple placeholder")

RegisterEvent(401, "Fountain", nil, "Fountain")

RegisterEvent(451, "Drink from the Fountain", function()
    if not IsQBitSet(QBit(184)) then -- Balthazar Town Portal
        SetQBit(QBit(184)) -- Balthazar Town Portal
    end
    if IsAtLeast(MaxHealth, 0) then return end
    AddValue(CurrentHealth, 25)
    evt.StatusText("Your wounds begin to heal")
    SetAutonote(227) -- Fountain in Balthazar Lair restores Hit Points.
end, "Drink from the Fountain")

RegisterEvent(452, "Lotts' House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(638) -- Lotts' House
end, "Lotts' House")

RegisterEvent(453, "Lotts' House", nil, "Lotts' House")

RegisterEvent(454, "Hollyfield House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(639) -- Hollyfield House
end, "Hollyfield House")

RegisterEvent(455, "Hollyfield House", nil, "Hollyfield House")

RegisterEvent(456, "Tessalar's House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(640) -- Tessalar's House
end, "Tessalar's House")

RegisterEvent(457, "Tessalar's House", nil, "Tessalar's House")

RegisterEvent(458, "Stormeye's House", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(641) -- Stormeye's House
end, "Stormeye's House")

RegisterEvent(459, "Stormeye's House", nil, "Stormeye's House")

RegisterEvent(460, "Bank placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(642) -- Bank placeholder
end, "Bank placeholder")

RegisterEvent(461, "Bank placeholder", nil, "Bank placeholder")

RegisterEvent(462, "Training hall placeholder", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(626) -- Flooded House
        return
    end
    evt.EnterHouse(643) -- Training hall placeholder
end, "Training hall placeholder")

RegisterEvent(463, "Training hall placeholder", nil, "Training hall placeholder")

RegisterEvent(464, "Ayzar's Axes", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(6) -- Ayzar's Axes
end, "Ayzar's Axes")

RegisterEvent(465, "Ayzar's Axes", nil, "Ayzar's Axes")

RegisterEvent(466, "Linked Mail", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(41) -- Linked Mail
end, "Linked Mail")

RegisterEvent(467, "Linked Mail", nil, "Linked Mail")

RegisterEvent(468, "Amulets of Power", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(81) -- Amulets of Power
end, "Amulets of Power")

RegisterEvent(469, "Amulets of Power", nil, "Amulets of Power")

RegisterEvent(470, "Perius' Powders", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(115) -- Perius' Powders
end, "Perius' Powders")

RegisterEvent(471, "Perius' Powders", nil, "Perius' Powders")

RegisterEvent(472, "The Shaman", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(308) -- The Shaman
end, "The Shaman")

RegisterEvent(473, "The Shaman", nil, "The Shaman")

RegisterEvent(474, "Balthazar Academy", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(1569) -- Balthazar Academy
end, "Balthazar Academy")

RegisterEvent(475, "Balthazar Academy", nil, "Balthazar Academy")

RegisterEvent(476, "Bank of Balthazar", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(285) -- Bank of Balthazar
end, "Bank of Balthazar")

RegisterEvent(477, "Bank of Balthazar", nil, "Bank of Balthazar")

RegisterEvent(478, "Guild of Mind", function()
    if not IsQBitSet(QBit(23)) then -- Allied with Minotaurs. Rescue the Minotaurs done.
        evt.EnterHouse(627) -- Flooded Shop
        return
    end
    evt.EnterHouse(188) -- Guild of Mind
end, "Guild of Mind")

RegisterEvent(479, "Guild of Mind", nil, "Guild of Mind")

RegisterEvent(501, "Leave Balthazar Lair", function()
    evt.MoveToMap(-10869, -8850, 1985, 1024, 0, 0, 0, 1, "out08.odm") -- Ravage Roaming
end, "Leave Balthazar Lair")

RegisterEvent(502, "Leave Balthazar Lair", function()
    evt.MoveToMap(-12279, -12153, 2752, 1536, 0, 0, 0, 1, "out08.odm") -- Ravage Roaming
end, "Leave Balthazar Lair")

