-- Abandoned Temple
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
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
    textureNames = {"t65a05bl", "t65a05br", "t65b11b", "t65b11c"},
    spriteNames = {},
    castSpellIds = {2, 24},
    timers = {
    { eventId = 110, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(403)) then return end -- Roster Character In Party 4
    evt.SpeakNPC(264) -- Simon Templar
end)

RegisterEvent(2, "Legacy event 2", function()
    if not IsAtLeast(MapVar(12), 15) then
        evt.SetDoorState(108, DoorAction.Close)
        evt.SetDoorState(109, DoorAction.Close)
        SetValue(MapVar(2), 0)
        SetValue(MapVar(3), 0)
        SetValue(MapVar(4), 0)
        SetValue(MapVar(5), 0)
        SetValue(MapVar(6), 0)
        SetValue(MapVar(7), 0)
        SetValue(MapVar(8), 0)
        SetValue(MapVar(9), 0)
        SetValue(MapVar(12), 0)
        evt.SetDoorState(110, DoorAction.Close)
        evt.SetDoorState(111, DoorAction.Close)
        evt.SetDoorState(112, DoorAction.Close)
        evt.SetDoorState(113, DoorAction.Close)
        return
    end
    evt.SetDoorState(108, DoorAction.Open)
    evt.SetDoorState(109, DoorAction.Open)
    evt.SetDoorState(110, DoorAction.Close)
    evt.SetDoorState(111, DoorAction.Close)
    evt.SetDoorState(112, DoorAction.Close)
    evt.SetDoorState(113, DoorAction.Close)
end)

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    evt.ForPlayer(Players.All)
    if HasItem(626) then -- Prophecies of the Sun
        SetQBit(QBit(218)) -- Prophesies of the Sun - I lost it
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterEvent(10, "Legacy event 10", function()
    if IsQBitSet(QBit(136)) then -- Found Prophiecies of the Snake
        return
    elseif HasItem(652) then -- Prophecies of the Snake
        SetQBit(QBit(136)) -- Found Prophiecies of the Snake
        ClearQBit(QBit(135)) -- Find the Prophecies of the Snake for Pascella Tisk.
        return
    else
        return
    end
end)

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetTexture(10, "t65a05bl")
    evt.SetTexture(11, "t65a05br")
end, "Door")

RegisterEvent(12, "Legacy event 12", function()
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(13, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(20, "Button", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(53, DoorAction.Close)
end, "Button")

RegisterEvent(21, "Button", function()
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(53, DoorAction.Open)
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(52, DoorAction.Close)
end, "Button")

RegisterEvent(22, "Button", function()
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(54, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Close)
    evt.SetDoorState(55, DoorAction.Close)
end, "Button")

RegisterEvent(23, "Button", function()
    if not IsAtLeast(MapVar(22), 1) then
        evt.SummonMonsters(1, 3, 1, 8000, 640, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8000, 640, -640), actor group 0, no unique actor name
        evt.SetDoorState(13, DoorAction.Open)
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetDoorState(12, DoorAction.Close)
        evt.SetDoorState(54, DoorAction.Close)
        SetValue(MapVar(22), 1)
        return
    end
    evt.SetDoorState(13, DoorAction.Open)
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(12, DoorAction.Close)
    evt.SetDoorState(54, DoorAction.Close)
    SetValue(MapVar(22), 1)
end, "Button")

RegisterEvent(24, "Button", function()
    evt.SetDoorState(14, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(57, DoorAction.Close)
end, "Button")

RegisterEvent(25, "Button", function()
    evt.SetDoorState(15, DoorAction.Open)
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(14, DoorAction.Close)
    evt.SetDoorState(56, DoorAction.Close)
end, "Button")

RegisterEvent(26, "Button", function()
    evt.SetDoorState(16, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(59, DoorAction.Close)
end, "Button")

RegisterEvent(27, "Button", function()
    evt.SetDoorState(17, DoorAction.Open)
    evt.SetDoorState(59, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Close)
    evt.SetDoorState(58, DoorAction.Close)
end, "Button")

RegisterEvent(28, "Button", function()
    if not IsAtLeast(MapVar(21), 1) then
        evt.SummonMonsters(1, 3, 1, 9600, -192, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9600, -192, -640), actor group 0, no unique actor name
        evt.SetDoorState(18, DoorAction.Open)
        evt.SetDoorState(60, DoorAction.Open)
        evt.SetDoorState(19, DoorAction.Close)
        evt.SetDoorState(61, DoorAction.Close)
        SetValue(MapVar(21), 1)
        return
    end
    evt.SetDoorState(18, DoorAction.Open)
    evt.SetDoorState(60, DoorAction.Open)
    evt.SetDoorState(19, DoorAction.Close)
    evt.SetDoorState(61, DoorAction.Close)
    SetValue(MapVar(21), 1)
end, "Button")

RegisterEvent(29, "Button", function()
    evt.SetDoorState(19, DoorAction.Open)
    evt.SetDoorState(61, DoorAction.Open)
    evt.SetDoorState(18, DoorAction.Close)
    evt.SetDoorState(60, DoorAction.Close)
end, "Button")

RegisterEvent(30, "Button", function()
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(62, DoorAction.Open)
    evt.SetDoorState(21, DoorAction.Close)
    evt.SetDoorState(63, DoorAction.Close)
end, "Button")

RegisterEvent(31, "Button", function()
    if not IsAtLeast(MapVar(23), 1) then
        evt.SummonMonsters(1, 3, 1, 6784, -896, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(6784, -896, -640), actor group 0, no unique actor name
        evt.SetDoorState(21, DoorAction.Open)
        evt.SetDoorState(63, DoorAction.Open)
        evt.SetDoorState(20, DoorAction.Close)
        evt.SetDoorState(62, DoorAction.Close)
        SetValue(MapVar(23), 1)
        return
    end
    evt.SetDoorState(21, DoorAction.Open)
    evt.SetDoorState(63, DoorAction.Open)
    evt.SetDoorState(20, DoorAction.Close)
    evt.SetDoorState(62, DoorAction.Close)
    SetValue(MapVar(23), 1)
end, "Button")

RegisterEvent(32, "Button", function()
    evt.SetDoorState(22, DoorAction.Open)
    evt.SetDoorState(64, DoorAction.Open)
    evt.SetDoorState(23, DoorAction.Close)
    evt.SetDoorState(65, DoorAction.Close)
end, "Button")

RegisterEvent(33, "Button", function()
    if not IsAtLeast(MapVar(24), 1) then
        evt.SummonMonsters(1, 3, 1, 8256, -896, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8256, -896, -640), actor group 0, no unique actor name
        evt.SetDoorState(23, DoorAction.Open)
        evt.SetDoorState(65, DoorAction.Open)
        evt.SetDoorState(22, DoorAction.Close)
        evt.SetDoorState(64, DoorAction.Close)
        SetValue(MapVar(24), 1)
        return
    end
    evt.SetDoorState(23, DoorAction.Open)
    evt.SetDoorState(65, DoorAction.Open)
    evt.SetDoorState(22, DoorAction.Close)
    evt.SetDoorState(64, DoorAction.Close)
    SetValue(MapVar(24), 1)
end, "Button")

RegisterEvent(34, "Button", function()
    if not IsAtLeast(MapVar(25), 1) then
        evt.SummonMonsters(1, 3, 1, 8832, -960, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8832, -960, -640), actor group 0, no unique actor name
        evt.SetDoorState(24, DoorAction.Open)
        evt.SetDoorState(66, DoorAction.Open)
        evt.SetDoorState(25, DoorAction.Close)
        evt.SetDoorState(67, DoorAction.Close)
        SetValue(MapVar(25), 1)
        return
    end
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(66, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(67, DoorAction.Close)
    SetValue(MapVar(25), 1)
end, "Button")

RegisterEvent(35, "Button", function()
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(67, DoorAction.Open)
    evt.SetDoorState(24, DoorAction.Close)
    evt.SetDoorState(66, DoorAction.Close)
end, "Button")

RegisterEvent(36, "Button", function()
    if not IsAtLeast(MapVar(26), 1) then
        evt.SummonMonsters(1, 3, 1, 9792, -960, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9792, -960, -640), actor group 0, no unique actor name
        evt.SetDoorState(26, DoorAction.Open)
        evt.SetDoorState(68, DoorAction.Open)
        evt.SetDoorState(27, DoorAction.Close)
        evt.SetDoorState(69, DoorAction.Close)
        SetValue(MapVar(26), 1)
        return
    end
    evt.SetDoorState(26, DoorAction.Open)
    evt.SetDoorState(68, DoorAction.Open)
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(69, DoorAction.Close)
    SetValue(MapVar(26), 1)
end, "Button")

RegisterEvent(37, "Button", function()
    if not IsAtLeast(MapVar(27), 1) then
        evt.SummonMonsters(1, 3, 1, 10176, -960, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(10176, -960, -640), actor group 0, no unique actor name
        evt.SetDoorState(27, DoorAction.Open)
        evt.SetDoorState(69, DoorAction.Open)
        evt.SetDoorState(26, DoorAction.Close)
        evt.SetDoorState(68, DoorAction.Close)
        SetValue(MapVar(27), 1)
        return
    end
    evt.SetDoorState(27, DoorAction.Open)
    evt.SetDoorState(69, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(68, DoorAction.Close)
    SetValue(MapVar(27), 1)
end, "Button")

RegisterEvent(38, "Button", function()
    if not IsAtLeast(MapVar(28), 1) then
        evt.SummonMonsters(1, 3, 1, 6208, -1664, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(6208, -1664, -640), actor group 0, no unique actor name
        evt.SetDoorState(28, DoorAction.Open)
        evt.SetDoorState(70, DoorAction.Open)
        evt.SetDoorState(29, DoorAction.Close)
        evt.SetDoorState(71, DoorAction.Close)
        SetValue(MapVar(28), 1)
        return
    end
    evt.SetDoorState(28, DoorAction.Open)
    evt.SetDoorState(70, DoorAction.Open)
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(71, DoorAction.Close)
    SetValue(MapVar(28), 1)
end, "Button")

RegisterEvent(39, "Button", function()
    if not IsAtLeast(MapVar(29), 1) then
        evt.SummonMonsters(1, 3, 1, 6592, -1664, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(6592, -1664, -640), actor group 0, no unique actor name
        evt.SetDoorState(29, DoorAction.Open)
        evt.SetDoorState(71, DoorAction.Open)
        evt.SetDoorState(28, DoorAction.Close)
        evt.SetDoorState(70, DoorAction.Close)
        SetValue(MapVar(29), 1)
        return
    end
    evt.SetDoorState(29, DoorAction.Open)
    evt.SetDoorState(71, DoorAction.Open)
    evt.SetDoorState(28, DoorAction.Close)
    evt.SetDoorState(70, DoorAction.Close)
    SetValue(MapVar(29), 1)
end, "Button")

RegisterEvent(40, "Button", function()
    evt.SetDoorState(30, DoorAction.Open)
    evt.SetDoorState(72, DoorAction.Open)
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(73, DoorAction.Close)
end, "Button")

RegisterEvent(41, "Button", function()
    evt.SetDoorState(31, DoorAction.Open)
    evt.SetDoorState(73, DoorAction.Open)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(72, DoorAction.Close)
end, "Button")

RegisterEvent(42, "Button", function()
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(74, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(35, DoorAction.Close)
    evt.SetDoorState(75, DoorAction.Close)
    evt.SetDoorState(76, DoorAction.Close)
    evt.SetDoorState(77, DoorAction.Close)
end, "Button")

RegisterEvent(43, "Button", function()
    if not IsAtLeast(MapVar(32), 1) then
        evt.SummonMonsters(1, 3, 1, 9024, -1728, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9024, -1728, -640), actor group 0, no unique actor name
        evt.SetDoorState(32, DoorAction.Close)
        evt.SetDoorState(33, DoorAction.Open)
        evt.SetDoorState(34, DoorAction.Close)
        evt.SetDoorState(35, DoorAction.Close)
        evt.SetDoorState(74, DoorAction.Close)
        evt.SetDoorState(75, DoorAction.Open)
        evt.SetDoorState(76, DoorAction.Close)
        evt.SetDoorState(77, DoorAction.Close)
        SetValue(MapVar(32), 1)
        return
    end
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(33, DoorAction.Open)
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(35, DoorAction.Close)
    evt.SetDoorState(74, DoorAction.Close)
    evt.SetDoorState(75, DoorAction.Open)
    evt.SetDoorState(76, DoorAction.Close)
    evt.SetDoorState(77, DoorAction.Close)
    SetValue(MapVar(32), 1)
end, "Button")

RegisterEvent(44, "Button", function()
    if not IsAtLeast(MapVar(33), 1) then
        evt.SummonMonsters(1, 3, 1, 9408, -1728, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9408, -1728, -640), actor group 0, no unique actor name
        evt.SetDoorState(32, DoorAction.Close)
        evt.SetDoorState(33, DoorAction.Close)
        evt.SetDoorState(34, DoorAction.Open)
        evt.SetDoorState(35, DoorAction.Close)
        evt.SetDoorState(74, DoorAction.Close)
        evt.SetDoorState(75, DoorAction.Close)
        evt.SetDoorState(76, DoorAction.Open)
        evt.SetDoorState(77, DoorAction.Close)
        SetValue(MapVar(33), 1)
        return
    end
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Open)
    evt.SetDoorState(35, DoorAction.Close)
    evt.SetDoorState(74, DoorAction.Close)
    evt.SetDoorState(75, DoorAction.Close)
    evt.SetDoorState(76, DoorAction.Open)
    evt.SetDoorState(77, DoorAction.Close)
    SetValue(MapVar(33), 1)
end, "Button")

RegisterEvent(45, "Button", function()
    evt.SetDoorState(32, DoorAction.Close)
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(35, DoorAction.Open)
    evt.SetDoorState(74, DoorAction.Close)
    evt.SetDoorState(75, DoorAction.Close)
    evt.SetDoorState(76, DoorAction.Close)
    evt.SetDoorState(77, DoorAction.Open)
    SetValue(MapVar(33), 0)
end, "Button")

RegisterEvent(46, "Button", function()
    if not IsAtLeast(MapVar(34), 1) then
        evt.SummonMonsters(1, 3, 1, 7104, -2432, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(7104, -2432, -640), actor group 0, no unique actor name
        evt.SetDoorState(36, DoorAction.Open)
        evt.SetDoorState(78, DoorAction.Open)
        evt.SetDoorState(37, DoorAction.Close)
        evt.SetDoorState(79, DoorAction.Close)
        SetValue(MapVar(34), 1)
        return
    end
    evt.SetDoorState(36, DoorAction.Open)
    evt.SetDoorState(78, DoorAction.Open)
    evt.SetDoorState(37, DoorAction.Close)
    evt.SetDoorState(79, DoorAction.Close)
    SetValue(MapVar(34), 1)
end, "Button")

RegisterEvent(47, "Button", function()
    if not IsAtLeast(MapVar(35), 1) then
        evt.SummonMonsters(1, 3, 1, 7488, -2432, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(7488, -2432, -640), actor group 0, no unique actor name
        evt.SetDoorState(37, DoorAction.Open)
        evt.SetDoorState(79, DoorAction.Open)
        evt.SetDoorState(36, DoorAction.Close)
        evt.SetDoorState(78, DoorAction.Close)
        SetValue(MapVar(35), 1)
        return
    end
    evt.SetDoorState(37, DoorAction.Open)
    evt.SetDoorState(79, DoorAction.Open)
    evt.SetDoorState(36, DoorAction.Close)
    evt.SetDoorState(78, DoorAction.Close)
    SetValue(MapVar(35), 1)
end, "Button")

RegisterEvent(48, "Button", function()
    evt.SetDoorState(38, DoorAction.Open)
    evt.SetDoorState(80, DoorAction.Open)
    evt.SetDoorState(39, DoorAction.Close)
    evt.SetDoorState(81, DoorAction.Close)
end, "Button")

RegisterEvent(49, "Button", function()
    if not IsAtLeast(MapVar(36), 1) then
        evt.SummonMonsters(1, 3, 1, 8832, -2496, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8832, -2496, -640), actor group 0, no unique actor name
        evt.SetDoorState(39, DoorAction.Open)
        evt.SetDoorState(81, DoorAction.Open)
        evt.SetDoorState(38, DoorAction.Close)
        evt.SetDoorState(80, DoorAction.Close)
        SetValue(MapVar(36), 1)
        return
    end
    evt.SetDoorState(39, DoorAction.Open)
    evt.SetDoorState(81, DoorAction.Open)
    evt.SetDoorState(38, DoorAction.Close)
    evt.SetDoorState(80, DoorAction.Close)
    SetValue(MapVar(36), 1)
end, "Button")

RegisterEvent(50, "Button", function()
    if not IsAtLeast(MapVar(37), 1) then
        evt.SummonMonsters(1, 3, 1, 9600, -2496, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9600, -2496, -640), actor group 0, no unique actor name
        evt.SetDoorState(40, DoorAction.Open)
        evt.SetDoorState(82, DoorAction.Open)
        evt.SetDoorState(41, DoorAction.Close)
        evt.SetDoorState(83, DoorAction.Close)
        SetValue(MapVar(37), 1)
        return
    end
    evt.SetDoorState(40, DoorAction.Open)
    evt.SetDoorState(82, DoorAction.Open)
    evt.SetDoorState(41, DoorAction.Close)
    evt.SetDoorState(83, DoorAction.Close)
    SetValue(MapVar(37), 1)
end, "Button")

RegisterEvent(51, "Button", function()
    if not IsAtLeast(MapVar(38), 1) then
        evt.SummonMonsters(1, 3, 1, 9984, -2496, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9984, -2496, -640), actor group 0, no unique actor name
        evt.SetDoorState(41, DoorAction.Open)
        evt.SetDoorState(83, DoorAction.Open)
        evt.SetDoorState(40, DoorAction.Close)
        evt.SetDoorState(82, DoorAction.Close)
        SetValue(MapVar(38), 1)
        return
    end
    evt.SetDoorState(41, DoorAction.Open)
    evt.SetDoorState(83, DoorAction.Open)
    evt.SetDoorState(40, DoorAction.Close)
    evt.SetDoorState(82, DoorAction.Close)
    SetValue(MapVar(38), 1)
end, "Button")

RegisterEvent(52, "Button", function()
    evt.SetDoorState(42, DoorAction.Open)
    evt.SetDoorState(43, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(84, DoorAction.Open)
    evt.SetDoorState(85, DoorAction.Close)
    evt.SetDoorState(86, DoorAction.Close)
    evt.SetDoorState(87, DoorAction.Close)
    evt.SetDoorState(88, DoorAction.Close)
    evt.SetDoorState(89, DoorAction.Close)
end, "Button")

RegisterEvent(53, "Button", function()
    if not IsAtLeast(MapVar(39), 1) then
        evt.SummonMonsters(1, 3, 1, 7872, -3264, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(7872, -3264, -640), actor group 0, no unique actor name
        evt.SetDoorState(42, DoorAction.Close)
        evt.SetDoorState(43, DoorAction.Open)
        evt.SetDoorState(44, DoorAction.Close)
        evt.SetDoorState(45, DoorAction.Close)
        evt.SetDoorState(46, DoorAction.Close)
        evt.SetDoorState(47, DoorAction.Close)
        evt.SetDoorState(84, DoorAction.Close)
        evt.SetDoorState(85, DoorAction.Open)
        evt.SetDoorState(86, DoorAction.Close)
        evt.SetDoorState(87, DoorAction.Close)
        evt.SetDoorState(88, DoorAction.Close)
        evt.SetDoorState(89, DoorAction.Close)
        SetValue(MapVar(39), 1)
        return
    end
    evt.SetDoorState(42, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Open)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(84, DoorAction.Close)
    evt.SetDoorState(85, DoorAction.Open)
    evt.SetDoorState(86, DoorAction.Close)
    evt.SetDoorState(87, DoorAction.Close)
    evt.SetDoorState(88, DoorAction.Close)
    evt.SetDoorState(89, DoorAction.Close)
    SetValue(MapVar(39), 1)
end, "Button")

RegisterEvent(54, "Button", function()
    if not IsAtLeast(MapVar(40), 1) then
        evt.SummonMonsters(1, 3, 1, 8256, -3264, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8256, -3264, -640), actor group 0, no unique actor name
        evt.SetDoorState(42, DoorAction.Close)
        evt.SetDoorState(43, DoorAction.Close)
        evt.SetDoorState(44, DoorAction.Open)
        evt.SetDoorState(45, DoorAction.Close)
        evt.SetDoorState(46, DoorAction.Close)
        evt.SetDoorState(47, DoorAction.Close)
        evt.SetDoorState(84, DoorAction.Close)
        evt.SetDoorState(85, DoorAction.Close)
        evt.SetDoorState(86, DoorAction.Open)
        evt.SetDoorState(87, DoorAction.Close)
        evt.SetDoorState(88, DoorAction.Close)
        evt.SetDoorState(89, DoorAction.Close)
        SetValue(MapVar(40), 1)
        return
    end
    evt.SetDoorState(42, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Open)
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(84, DoorAction.Close)
    evt.SetDoorState(85, DoorAction.Close)
    evt.SetDoorState(86, DoorAction.Open)
    evt.SetDoorState(87, DoorAction.Close)
    evt.SetDoorState(88, DoorAction.Close)
    evt.SetDoorState(89, DoorAction.Close)
    SetValue(MapVar(40), 1)
end, "Button")

RegisterEvent(55, "Button", function()
    evt.SetDoorState(42, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Open)
    evt.SetDoorState(46, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(84, DoorAction.Close)
    evt.SetDoorState(85, DoorAction.Close)
    evt.SetDoorState(86, DoorAction.Close)
    evt.SetDoorState(87, DoorAction.Open)
    evt.SetDoorState(88, DoorAction.Close)
    evt.SetDoorState(89, DoorAction.Close)
end, "Button")

RegisterEvent(56, "Button", function()
    if not IsAtLeast(MapVar(41), 1) then
        evt.SummonMonsters(1, 3, 1, 9024, -3264, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(9024, -3264, -640), actor group 0, no unique actor name
        evt.SetDoorState(42, DoorAction.Close)
        evt.SetDoorState(43, DoorAction.Close)
        evt.SetDoorState(44, DoorAction.Close)
        evt.SetDoorState(45, DoorAction.Close)
        evt.SetDoorState(46, DoorAction.Open)
        evt.SetDoorState(47, DoorAction.Close)
        evt.SetDoorState(84, DoorAction.Close)
        evt.SetDoorState(85, DoorAction.Close)
        evt.SetDoorState(86, DoorAction.Close)
        evt.SetDoorState(87, DoorAction.Close)
        evt.SetDoorState(88, DoorAction.Open)
        evt.SetDoorState(89, DoorAction.Close)
        SetValue(MapVar(41), 1)
        return
    end
    evt.SetDoorState(42, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Open)
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(84, DoorAction.Close)
    evt.SetDoorState(85, DoorAction.Close)
    evt.SetDoorState(86, DoorAction.Close)
    evt.SetDoorState(87, DoorAction.Close)
    evt.SetDoorState(88, DoorAction.Open)
    evt.SetDoorState(89, DoorAction.Close)
    SetValue(MapVar(41), 1)
end, "Button")

RegisterEvent(57, "Button", function()
    evt.SetDoorState(42, DoorAction.Close)
    evt.SetDoorState(43, DoorAction.Close)
    evt.SetDoorState(44, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
    evt.SetDoorState(47, DoorAction.Open)
    evt.SetDoorState(84, DoorAction.Close)
    evt.SetDoorState(85, DoorAction.Close)
    evt.SetDoorState(86, DoorAction.Close)
    evt.SetDoorState(87, DoorAction.Close)
    evt.SetDoorState(88, DoorAction.Close)
    evt.SetDoorState(89, DoorAction.Open)
end, "Button")

RegisterEvent(58, "Button", function()
    if not IsAtLeast(MapVar(42), 1) then
        evt.SummonMonsters(1, 3, 1, 7296, -4032, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(7296, -4032, -640), actor group 0, no unique actor name
        evt.SetDoorState(48, DoorAction.Open)
        evt.SetDoorState(90, DoorAction.Open)
        evt.SetDoorState(49, DoorAction.Close)
        evt.SetDoorState(91, DoorAction.Close)
        SetValue(MapVar(42), 1)
        return
    end
    evt.SetDoorState(48, DoorAction.Open)
    evt.SetDoorState(90, DoorAction.Open)
    evt.SetDoorState(49, DoorAction.Close)
    evt.SetDoorState(91, DoorAction.Close)
    SetValue(MapVar(42), 1)
end, "Button")

RegisterEvent(59, "Button", function()
    if not IsAtLeast(MapVar(43), 1) then
        evt.SummonMonsters(1, 3, 1, 7680, -4032, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(7680, -4032, -640), actor group 0, no unique actor name
        evt.SetDoorState(49, DoorAction.Open)
        evt.SetDoorState(91, DoorAction.Open)
        evt.SetDoorState(48, DoorAction.Close)
        evt.SetDoorState(90, DoorAction.Close)
        SetValue(MapVar(43), 1)
        return
    end
    evt.SetDoorState(49, DoorAction.Open)
    evt.SetDoorState(91, DoorAction.Open)
    evt.SetDoorState(48, DoorAction.Close)
    evt.SetDoorState(90, DoorAction.Close)
    SetValue(MapVar(43), 1)
end, "Button")

RegisterEvent(60, "Button", function()
    if not IsAtLeast(MapVar(44), 1) then
        evt.SummonMonsters(1, 3, 1, 8448, -4032, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8448, -4032, -640), actor group 0, no unique actor name
        evt.SetDoorState(50, DoorAction.Open)
        evt.SetDoorState(92, DoorAction.Open)
        evt.SetDoorState(51, DoorAction.Close)
        evt.SetDoorState(93, DoorAction.Close)
        SetValue(MapVar(44), 1)
        return
    end
    evt.SetDoorState(50, DoorAction.Open)
    evt.SetDoorState(92, DoorAction.Open)
    evt.SetDoorState(51, DoorAction.Close)
    evt.SetDoorState(93, DoorAction.Close)
    SetValue(MapVar(44), 1)
end, "Button")

RegisterEvent(61, "Button", function()
    if not IsAtLeast(MapVar(45), 1) then
        evt.SummonMonsters(1, 3, 1, 8832, -4032, -640, 0, 0) -- encounter slot 1 "Serpentmen" tier C, count 1, pos=(8832, -4032, -640), actor group 0, no unique actor name
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(93, DoorAction.Open)
        evt.SetDoorState(50, DoorAction.Close)
        evt.SetDoorState(92, DoorAction.Close)
        SetValue(MapVar(45), 1)
        return
    end
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(93, DoorAction.Open)
    evt.SetDoorState(50, DoorAction.Close)
    evt.SetDoorState(92, DoorAction.Close)
    SetValue(MapVar(45), 1)
end, "Button")

RegisterEvent(62, "Door", function()
    evt.SetDoorState(108, DoorAction.Open)
end, "Door")

RegisterEvent(63, "Door", function()
    if IsAtLeast(MapVar(12), 1) then return end
    evt.SetDoorState(109, DoorAction.Close)
    evt.SetDoorState(108, DoorAction.Close)
    evt.SetDoorState(110, DoorAction.Open)
    evt.SetDoorState(111, DoorAction.Open)
    evt.SetDoorState(112, DoorAction.Open)
    evt.SetDoorState(113, DoorAction.Open)
    evt.SetTexture(1, "t65b11c")
    evt.SetTexture(2, "t65b11c")
    evt.SetTexture(3, "t65b11c")
    evt.SetTexture(4, "t65b11c")
    evt.SetTexture(5, "t65b11c")
    evt.SetTexture(6, "t65b11c")
    evt.SetTexture(7, "t65b11c")
    evt.SetTexture(8, "t65b11c")
    evt.SetLight(1, 1)
    evt.SetLight(2, 1)
    evt.SetLight(3, 1)
    evt.SetLight(4, 1)
    evt.SetLight(5, 1)
    evt.SetLight(6, 1)
    evt.SetLight(7, 1)
    evt.SetLight(8, 1)
    AddValue(MapVar(12), 1)
end, "Door")

RegisterEvent(64, "Leave the Abandoned Temple", function()
    evt.SetDoorState(109, DoorAction.Open)
end, "Leave the Abandoned Temple")

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

RegisterEvent(101, "Legacy event 101", function()
    evt.ForPlayer(Players.All)
    SetValue(Eradicated, 0)
end)

RegisterEvent(102, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(2), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(1, "t65b11b")
        evt.SetLight(1, 0)
        return
    end
    SetValue(MapVar(2), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(1, "t65b11c")
    evt.SetLight(1, 1)
end, "Button")

RegisterEvent(103, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(3), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(2, "t65b11b")
        evt.SetLight(2, 0)
        return
    end
    SetValue(MapVar(3), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(2, "t65b11c")
    evt.SetLight(2, 1)
end, "Button")

RegisterEvent(104, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(3, "t65b11b")
        evt.SetLight(3, 0)
        return
    end
    SetValue(MapVar(4), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(3, "t65b11c")
    evt.SetLight(3, 1)
end, "Button")

RegisterEvent(105, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(5), 1) then
        SetValue(MapVar(5), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(4, "t65b11b")
        evt.SetLight(4, 0)
        return
    end
    SetValue(MapVar(5), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(4, "t65b11c")
    evt.SetLight(4, 1)
end, "Button")

RegisterEvent(106, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(6), 1) then
        SetValue(MapVar(6), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(5, "t65b11b")
        evt.SetLight(5, 0)
        return
    end
    SetValue(MapVar(6), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(5, "t65b11c")
    evt.SetLight(5, 1)
end, "Button")

RegisterEvent(107, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(7), 1) then
        SetValue(MapVar(7), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(6, "t65b11b")
        evt.SetLight(6, 0)
        return
    end
    SetValue(MapVar(7), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(6, "t65b11c")
    evt.SetLight(6, 1)
end, "Button")

RegisterEvent(108, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(8), 1) then
        SetValue(MapVar(8), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(7, "t65b11b")
        evt.SetLight(7, 0)
        return
    end
    SetValue(MapVar(8), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(7, "t65b11c")
    evt.SetLight(7, 1)
end, "Button")

RegisterEvent(109, "Button", function()
    if IsAtLeast(MapVar(12), 15) then return end
    if not IsAtLeast(MapVar(12), 1) then return end
    if not IsAtLeast(MapVar(9), 1) then
        SetValue(MapVar(9), 1)
        AddValue(MapVar(12), 1)
        evt.SetTexture(8, "t65b11b")
        evt.SetLight(8, 0)
        return
    end
    SetValue(MapVar(9), 0)
    SubtractValue(MapVar(12), 1)
    evt.SetTexture(8, "t65b11c")
    evt.SetLight(8, 1)
end, "Button")

RegisterEvent(110, "Legacy event 110", function()
    if IsAtLeast(MapVar(12), 15) then
        return
    elseif IsAtLeast(MapVar(12), 9) then
        evt.StopDoor(110)
        evt.StopDoor(111)
        evt.StopDoor(112)
        evt.StopDoor(113)
        evt.SetDoorState(108, DoorAction.Open)
        evt.SetDoorState(109, DoorAction.Open)
        SetValue(MapVar(12), 15)
        return
    else
        return
    end
end)

RegisterEvent(111, "Legacy event 111", function()
    evt.CastSpell(24, 10, 1, 13184, 2848, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13088, 2944, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13184, 3040, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13280, 2944, -464, 0, 0, 0) -- Poison Spray
end)

RegisterEvent(112, "Legacy event 112", function()
    evt.CastSpell(24, 10, 1, 13184, 1824, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13088, 1920, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13184, 2016, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 13280, 1920, -464, 0, 0, 0) -- Poison Spray
end)

RegisterEvent(113, "Legacy event 113", function()
    evt.CastSpell(24, 10, 1, 10368, 2016, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10464, 1920, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10368, 1824, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10272, 1920, -464, 0, 0, 0) -- Poison Spray
end)

RegisterEvent(114, "Legacy event 114", function()
    evt.CastSpell(24, 10, 1, 10368, 3040, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10464, 2944, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10368, 2848, -464, 0, 0, 0) -- Poison Spray
    evt.CastSpell(24, 10, 1, 10272, 2944, -464, 0, 0, 0) -- Poison Spray
end)

RegisterEvent(115, "Legacy event 115", function()
    evt.CastSpell(2, 10, 1, 11840, 2496, -448, 0, 0, 0) -- Fire Bolt
    evt.CastSpell(2, 10, 1, 11840, 2368, -448, 0, 0, 0) -- Fire Bolt
    evt.CastSpell(2, 10, 1, 11712, 2368, -448, 0, 0, 0) -- Fire Bolt
    evt.CastSpell(2, 10, 1, 11712, 2496, -448, 0, 0, 0) -- Fire Bolt
end)

RegisterEvent(402, "Legacy event 402", nil)

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(14), 1) then
        return
    end
    if IsAtLeast(MapVar(13), 3) then
        return
    end
    if not IsAtLeast(MapVar(13), 2) then
        AddValue(MapVar(13), 1)
        SetValue(MapVar(14), 1)
        return
    end
    evt.SetFacetBit(15, FacetBits.IsSecret, 1)
    AddValue(MapVar(13), 1)
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(14), 1) then
        SetValue(MapVar(14), 0)
    end
end)

RegisterEvent(453, "Legacy event 453", function()
    evt.SetDoorState(115, DoorAction.Open)
end)

RegisterEvent(501, "Leave the Abandoned Temple", function()
    evt.MoveToMap(-12789, 18734, 1857, 1536, 0, 0, 0, 1, "out01.odm") -- Dagger Wound Island
end, "Leave the Abandoned Temple")

RegisterEvent(502, "Leave the Abandoned Temple", function()
    evt.MoveToMap(21519, 21106, 97, 1024, 0, 0, 0, 1, "out01.odm") -- Dagger Wound Island
end, "Leave the Abandoned Temple")

RegisterEvent(506, "Legacy event 506", function()
    evt.SetDoorState(94, DoorAction.Open)
end)

RegisterEvent(507, "Legacy event 507", function()
    evt.SetDoorState(95, DoorAction.Open)
end)

RegisterEvent(508, "Legacy event 508", function()
    evt.SetDoorState(96, DoorAction.Open)
end)

RegisterEvent(509, "Legacy event 509", function()
    evt.SetDoorState(97, DoorAction.Open)
end)

RegisterEvent(510, "Legacy event 510", function()
    evt.SetDoorState(98, DoorAction.Open)
end)

RegisterEvent(511, "Legacy event 511", function()
    evt.SetDoorState(99, DoorAction.Open)
end)

RegisterEvent(512, "Legacy event 512", function()
    evt.SetDoorState(94, DoorAction.Close)
    evt.SetDoorState(95, DoorAction.Close)
    evt.SetDoorState(96, DoorAction.Close)
    evt.SetDoorState(97, DoorAction.Close)
    evt.SetDoorState(98, DoorAction.Close)
    evt.SetDoorState(99, DoorAction.Close)
end)

RegisterEvent(513, "Button", function()
    if IsAtLeast(MapVar(31), 1) then return end
    evt.SetDoorState(100, DoorAction.Close)
    evt.SetDoorState(101, DoorAction.Open)
    evt.SetFacetBit(100, FacetBits.Untouchable, 1)
    evt.SetFacetBit(101, FacetBits.MoveByDoor, 1)
    SetValue(MapVar(31), 1)
end, "Button")

RegisterEvent(514, "Button", function()
    if IsAtLeast(MapVar(31), 2) then
        return
    end
    if not IsAtLeast(MapVar(31), 1) then
        evt.StatusText("The button will not move")
        return
    end
    evt.SetDoorState(102, DoorAction.Close)
    evt.SetDoorState(103, DoorAction.Open)
    evt.SetFacetBit(101, FacetBits.Untouchable, 1)
    evt.SetFacetBit(101, FacetBits.MoveByDoor, 0)
    evt.SetFacetBit(102, FacetBits.MoveByDoor, 1)
    SetValue(MapVar(31), 2)
end, "Button")

RegisterEvent(515, "Button", function()
    if IsAtLeast(MapVar(31), 3) then
        return
    end
    if not IsAtLeast(MapVar(31), 2) then
        evt.StatusText("The button will not move")
        return
    end
    evt.SetDoorState(104, DoorAction.Close)
    evt.SetDoorState(105, DoorAction.Open)
    evt.SetFacetBit(102, FacetBits.Untouchable, 1)
    evt.SetFacetBit(102, FacetBits.MoveByDoor, 0)
    evt.SetFacetBit(103, FacetBits.MoveByDoor, 1)
    SetValue(MapVar(31), 3)
end, "Button")

RegisterEvent(516, "Button", function()
    if IsAtLeast(MapVar(31), 4) then
        return
    end
    if not IsAtLeast(MapVar(31), 3) then
        evt.StatusText("The button will not move")
        return
    end
    evt.SetDoorState(106, DoorAction.Close)
    evt.SetDoorState(107, DoorAction.Open)
    evt.SetFacetBit(103, FacetBits.Untouchable, 1)
    evt.SetFacetBit(103, FacetBits.MoveByDoor, 0)
    SetValue(MapVar(31), 4)
end, "Button")

RegisterEvent(517, "Legacy event 517", function()
    evt.SetDoorState(114, DoorAction.Open)
end)

