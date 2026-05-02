-- Abandoned Pirate Keep
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
    if IsQBitSet(QBit(224)) then return end -- Cannonball of Dominion - I lost it
    evt.ForPlayer(Players.All)
    if HasItem(662) then -- Cannonball of Dominion
        SetQBit(QBit(224)) -- Cannonball of Dominion - I lost it
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

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
    evt.SetDoorState(6, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Open)
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

RegisterEvent(20, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
end, "Door")

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

RegisterEvent(61, "Door", function()
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(52, DoorAction.Open)
end, "Door")

RegisterEvent(62, "Door", function()
    evt.SetDoorState(53, DoorAction.Open)
    evt.SetDoorState(54, DoorAction.Open)
end, "Door")

RegisterEvent(63, "Door", function()
    evt.SetDoorState(55, DoorAction.Open)
    evt.SetDoorState(56, DoorAction.Open)
end, "Door")

RegisterEvent(64, "Door", function()
    evt.SetDoorState(57, DoorAction.Open)
    evt.SetDoorState(58, DoorAction.Open)
end, "Door")

RegisterEvent(65, "Door", function()
    evt.SetDoorState(59, DoorAction.Open)
    evt.SetDoorState(60, DoorAction.Open)
end, "Door")

RegisterEvent(66, "Door", function()
    evt.SetDoorState(61, DoorAction.Open)
    evt.SetDoorState(62, DoorAction.Open)
end, "Door")

RegisterEvent(67, "Door", function()
    evt.SetDoorState(63, DoorAction.Open)
    evt.SetDoorState(64, DoorAction.Open)
end, "Door")

RegisterEvent(68, "Door", function()
    evt.SetDoorState(65, DoorAction.Open)
    evt.SetDoorState(66, DoorAction.Open)
end, "Door")

RegisterEvent(69, "Door", function()
    evt.SetDoorState(67, DoorAction.Open)
    evt.SetDoorState(68, DoorAction.Open)
end, "Door")

RegisterEvent(70, "Door", function()
    evt.SetDoorState(69, DoorAction.Open)
    evt.SetDoorState(70, DoorAction.Open)
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

RegisterEvent(131, "Ship", function()
    if IsAtLeast(MapVar(11), 1) then return end
    if IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        evt.SetDoorState(100, DoorAction.Close)
        SetValue(MapVar(11), 1)
        evt.StatusText("The ship begins to sink")
    end
end, "Ship")

RegisterEvent(132, "Ship", function()
    if IsAtLeast(MapVar(12), 1) then return end
    if IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        evt.SetDoorState(101, DoorAction.Close)
        SetValue(MapVar(12), 1)
        evt.StatusText("The ship begins to sink")
    end
end, "Ship")

RegisterEvent(133, "Ship", function()
    if IsAtLeast(MapVar(13), 1) then return end
    if IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        evt.SetDoorState(102, DoorAction.Close)
        SetValue(MapVar(13), 1)
        evt.StatusText("The ship begins to sink")
    end
end, "Ship")

RegisterEvent(134, "Ship", function()
    if IsAtLeast(MapVar(14), 1) then return end
    if IsQBitSet(QBit(36)) then -- Sink the Regnan Fleet. Return to the Ravenshore council chamber. - Given and taken at Ravenshore council chamber.
        evt.SetDoorState(103, DoorAction.Close)
        SetValue(MapVar(14), 1)
        evt.StatusText("The ship begins to sink")
    end
end, "Ship")

RegisterEvent(451, "Door", function()
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Door")

RegisterEvent(501, "Leave the Abandoned Pirate Keep", function()
    evt.MoveToMap(-15291, 10754, 1248, 0, 0, 0, 0, 1, "out13.odm") -- Regna
end, "Leave the Abandoned Pirate Keep")

RegisterEvent(502, "Leave the Abandoned Pirate Keep", function()
    evt.MoveToMap(-7200, 13792, -14, 1, 0, 0, 0, 1, "d33.blv") -- Passage Under Regna
end, "Leave the Abandoned Pirate Keep")

