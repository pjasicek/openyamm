-- Plane of Earth
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

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(244)) then return end
    evt.ForPlayer(Players.All)
    if not HasItem(609) then return end -- Heart of Earth
    SetQBit(QBit(244))
    AddValue(Experience, 100000)
    SetQBit(QBit(208))
    return
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

RegisterEvent(71, "Legacy event 71", function()
    evt.SetDoorState(71, 2)
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

RegisterEvent(201, "Loamwalker's House", function()
    evt.EnterHouse(457) -- Loamwalker's House
    return
end, "Loamwalker's House")

RegisterEvent(202, "Loamwalker's House", nil, "Loamwalker's House")

RegisterEvent(203, "Soil's House", function()
    evt.EnterHouse(458) -- Soil's House
    return
end, "Soil's House")

RegisterEvent(204, "Soil's House", nil, "Soil's House")

RegisterEvent(205, "Empty House", function()
    evt.EnterHouse(459) -- Empty House
    return
end, "Empty House")

RegisterEvent(206, "Empty House", nil, "Empty House")

RegisterEvent(207, "Empty House", function()
    evt.EnterHouse(460) -- Empty House
    return
end, "Empty House")

RegisterEvent(208, "Empty House", nil, "Empty House")

RegisterEvent(209, "Empty House", function()
    evt.EnterHouse(461) -- Empty House
    return
end, "Empty House")

RegisterEvent(210, "Empty House", nil, "Empty House")

RegisterEvent(211, "Empty House", function()
    evt.EnterHouse(462) -- Empty House
    return
end, "Empty House")

RegisterEvent(212, "Empty House", nil, "Empty House")

RegisterEvent(213, "Empty House", function()
    evt.EnterHouse(463) -- Empty House
    return
end, "Empty House")

RegisterEvent(214, "Empty House", nil, "Empty House")

RegisterEvent(215, "Empty House", function()
    evt.EnterHouse(464) -- Empty House
    return
end, "Empty House")

RegisterEvent(216, "Empty House", nil, "Empty House")

RegisterEvent(217, "Empty House", function()
    evt.EnterHouse(465) -- Empty House
    return
end, "Empty House")

RegisterEvent(218, "Empty House", nil, "Empty House")

RegisterEvent(219, "Empty House", function()
    evt.EnterHouse(466) -- Empty House
    return
end, "Empty House")

RegisterEvent(220, "Empty House", nil, "Empty House")

RegisterEvent(223, "Griven's House", function()
    evt.EnterHouse(477) -- Griven's House
    return
end, "Griven's House")

RegisterEvent(224, "Griven's House", nil, "Griven's House")

RegisterEvent(401, "Gate out of the Plane of Earth", nil, "Gate out of the Plane of Earth")

RegisterEvent(451, "Take a Drink", function()
    if not IsAtLeast(EarthResistance, 10) then
        AddValue(EarthResistance, 2)
        evt.StatusText("Earth Resistance +10 (Permanent)")
        AddValue(IsIntellectMoreThanBase, 267)
        return
    end
    evt.StatusText("Refreshing")
    return
end, "Take a Drink")

RegisterEvent(505, "Leave the Plane of Earth", function()
    evt.MoveToMap(19776, -14112, 867, 512, 0, 0, 0, 0, "Out01.odm")
    return
end, "Leave the Plane of Earth")

