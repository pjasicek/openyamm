-- The Lincoln
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"sfpnlon"},
    spriteNames = {},
    castSpellIds = {15},
    timers = {
    { eventId = 476, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 477, repeating = true, intervalGameMinutes = 1, remainingGameMinutes = 1 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    SetValue(MapVar(2), 2)
    SetValue(MapVar(3), 2)
    evt.SetLight(1, 0)
    evt.SetLight(2, 0)
end)

RegisterEvent(3, "Legacy event 3", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(10, DoorAction.Open)
        evt.SetDoorState(11, DoorAction.Open)
    end
end)

RegisterEvent(4, "Legacy event 4", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(11, DoorAction.Close)
    end
end)

RegisterEvent(6, "Legacy event 6", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(12, DoorAction.Open)
        evt.SetDoorState(13, DoorAction.Open)
    end
end)

RegisterEvent(7, "Legacy event 7", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(12, DoorAction.Close)
        evt.SetDoorState(13, DoorAction.Close)
    end
end)

RegisterEvent(8, "Legacy event 8", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(15, DoorAction.Trigger)
        evt.SetDoorState(16, DoorAction.Trigger)
    end
end)

RegisterEvent(9, "Legacy event 9", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(15, DoorAction.Close)
        evt.SetDoorState(16, DoorAction.Close)
    end
end)

RegisterEvent(10, "Legacy event 10", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(19, DoorAction.Open)
        evt.SetDoorState(20, DoorAction.Open)
    end
end)

RegisterEvent(11, "Legacy event 11", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(23, DoorAction.Open)
    end
end)

RegisterEvent(12, "Legacy event 12", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(23, DoorAction.Close)
    end
end)

RegisterEvent(13, "Legacy event 13", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(24, DoorAction.Open)
        evt.SetDoorState(25, DoorAction.Open)
    end
end)

RegisterEvent(14, "Legacy event 14", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(24, DoorAction.Close)
        evt.SetDoorState(25, DoorAction.Close)
    end
end)

RegisterEvent(15, "Legacy event 15", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(26, DoorAction.Open)
    end
end)

RegisterEvent(16, "Legacy event 16", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(26, DoorAction.Close)
    end
end)

RegisterEvent(17, "Legacy event 17", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(27, DoorAction.Open)
    end
end)

RegisterEvent(18, "Legacy event 18", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(28, DoorAction.Close)
        evt.SetDoorState(37, DoorAction.Close)
        evt.SetDoorState(27, DoorAction.Open)
    end
end)

RegisterEvent(19, "Legacy event 19", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(28, DoorAction.Open)
    end
end)

RegisterEvent(20, "Legacy event 20", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(27, DoorAction.Close)
        evt.SetDoorState(37, DoorAction.Open)
        evt.SetDoorState(28, DoorAction.Open)
    end
end)

RegisterEvent(21, "Legacy event 21", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(29, DoorAction.Open)
        evt.SetDoorState(30, DoorAction.Open)
    end
end)

RegisterEvent(22, "Legacy event 22", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(29, DoorAction.Close)
        evt.SetDoorState(30, DoorAction.Close)
    end
end)

RegisterEvent(23, "Legacy event 23", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(31, DoorAction.Open)
        evt.SetDoorState(32, DoorAction.Open)
    end
end)

RegisterEvent(24, "Legacy event 24", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(31, DoorAction.Close)
        evt.SetDoorState(32, DoorAction.Close)
    end
end)

RegisterEvent(25, "Legacy event 25", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(33, DoorAction.Open)
        evt.SetDoorState(34, DoorAction.Open)
    end
end)

RegisterEvent(26, "Legacy event 26", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(33, DoorAction.Close)
        evt.SetDoorState(34, DoorAction.Close)
    end
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(35, DoorAction.Open)
    evt.SetDoorState(36, DoorAction.Open)
end)

RegisterEvent(28, "Legacy event 28", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(35, DoorAction.Close)
        evt.SetDoorState(36, DoorAction.Close)
    end
end)

RegisterEvent(29, "Legacy event 29", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(37, DoorAction.Trigger)
    end
end)

RegisterEvent(30, "Legacy event 30", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(39, DoorAction.Open)
        evt.SetDoorState(40, DoorAction.Open)
    end
end)

RegisterEvent(31, "Legacy event 31", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(39, DoorAction.Close)
        evt.SetDoorState(40, DoorAction.Close)
    end
end)

RegisterEvent(32, "Legacy event 32", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(45, DoorAction.Open)
        evt.SetDoorState(46, DoorAction.Open)
    end
end)

RegisterEvent(33, "Legacy event 33", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(45, DoorAction.Close)
        evt.SetDoorState(46, DoorAction.Close)
    end
end)

RegisterEvent(34, "Legacy event 34", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(48, DoorAction.Open)
        evt.SetDoorState(49, DoorAction.Open)
        evt.SetDoorState(47, DoorAction.Close)
    end
end)

RegisterEvent(35, "Legacy event 35", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(48, DoorAction.Close)
        evt.SetDoorState(49, DoorAction.Close)
    end
end)

RegisterEvent(36, "Legacy event 36", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(51, DoorAction.Open)
    end
end)

RegisterEvent(37, "Legacy event 37", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(51, DoorAction.Open)
    end
end)

RegisterEvent(38, "Legacy event 38", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(59, DoorAction.Open)
    end
end)

RegisterEvent(39, "Legacy event 39", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(59, DoorAction.Close)
    end
end)

RegisterEvent(40, "Legacy event 40", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(60, DoorAction.Open)
    end
end)

RegisterEvent(41, "Legacy event 41", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(60, DoorAction.Close)
    end
end)

RegisterEvent(42, "Legacy event 42", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(61, DoorAction.Open)
        evt.SetDoorState(62, DoorAction.Open)
    end
end)

RegisterEvent(43, "Legacy event 43", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(61, DoorAction.Close)
        evt.SetDoorState(62, DoorAction.Close)
    end
end)

RegisterEvent(44, "Legacy event 44", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(63, DoorAction.Open)
        evt.SetDoorState(64, DoorAction.Open)
    end
end)

RegisterEvent(45, "Legacy event 45", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(63, DoorAction.Close)
        evt.SetDoorState(64, DoorAction.Close)
    end
end)

RegisterEvent(46, "Legacy event 46", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(65, DoorAction.Open)
        evt.SetDoorState(66, DoorAction.Open)
    end
end)

RegisterEvent(47, "Legacy event 47", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(65, DoorAction.Close)
        evt.SetDoorState(66, DoorAction.Close)
    end
end)

RegisterEvent(49, "Legacy event 49", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(67, DoorAction.Open)
        evt.SetDoorState(68, DoorAction.Open)
    end
end)

RegisterEvent(50, "Legacy event 50", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(67, DoorAction.Close)
        evt.SetDoorState(68, DoorAction.Close)
    end
end)

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(73, DoorAction.Open)
        evt.SetDoorState(74, DoorAction.Open)
    end
end)

RegisterEvent(52, "Legacy event 52", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(75, DoorAction.Open)
        evt.SetDoorState(76, DoorAction.Open)
    end
end)

RegisterEvent(53, "Legacy event 53", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(69, DoorAction.Open)
        evt.SetDoorState(70, DoorAction.Open)
    end
end)

RegisterEvent(54, "Legacy event 54", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(71, DoorAction.Open)
        evt.SetDoorState(72, DoorAction.Open)
    end
end)

RegisterEvent(55, "Legacy event 55", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(69, DoorAction.Close)
        evt.SetDoorState(70, DoorAction.Close)
        evt.SetDoorState(73, DoorAction.Close)
        evt.SetDoorState(74, DoorAction.Close)
    end
end)

RegisterEvent(56, "Legacy event 56", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(71, DoorAction.Close)
        evt.SetDoorState(72, DoorAction.Close)
        evt.SetDoorState(75, DoorAction.Close)
        evt.SetDoorState(76, DoorAction.Close)
    end
end)

RegisterEvent(151, "Legacy event 151", function()
    if not IsAtLeast(MapVar(4), 1) then return end
    if not IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(9, DoorAction.Open)
        evt.SetDoorState(38, DoorAction.Open)
        SetValue(MapVar(2), 2)
        return
    end
    evt.SetDoorState(9, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Close)
    SetValue(MapVar(2), 1)
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.SetDoorState(17, DoorAction.Trigger)
end)

RegisterEvent(153, "Legacy event 153", function()
    evt.SetDoorState(18, DoorAction.Trigger)
    if not IsAtLeast(MapVar(4), 1) then return end
    evt.SetDoorState(47, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
end)

RegisterEvent(154, "Legacy event 154", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(47, DoorAction.Open)
        evt.SetDoorState(48, DoorAction.Close)
        evt.SetDoorState(49, DoorAction.Close)
    end
end)

RegisterEvent(155, "Legacy event 155", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(50, DoorAction.Close)
        evt.SetDoorState(51, DoorAction.Close)
    end
end)

RegisterEvent(156, "Legacy event 156", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(50, DoorAction.Open)
        evt.SetDoorState(26, DoorAction.Close)
    end
end)

RegisterEvent(157, "Legacy event 157", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(77, DoorAction.Open)
    end
end)

RegisterEvent(158, "Legacy event 158", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(78, DoorAction.Open)
    end
end)

RegisterEvent(159, "Legacy event 159", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(79, DoorAction.Open)
    end
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(376, "Legacy event 376", function()
    if not IsQBitSet(QBit(633)) then -- Got the sci-fi part
        if not IsAtLeast(MapVar(4), 1) then return end
        if not HasItem(1407) then -- Oscillation Overthruster
            AddValue(InventoryItem(1407), 1407) -- Oscillation Overthruster
            SetQBit(QBit(633)) -- Got the sci-fi part
            SetQBit(QBit(748)) -- Final Part - I lost it
            evt.SetDoorState(80, DoorAction.Close)
            SetValue(MapVar(5), 1)
        end
    end
    evt.SetLight(1, 0)
    evt.SetLight(2, 1)
end)

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(1, DoorAction.Trigger)
        evt.SetDoorState(5, DoorAction.Trigger)
    end
end)

RegisterEvent(452, "Legacy event 452", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(2, DoorAction.Trigger)
        evt.SetDoorState(6, DoorAction.Trigger)
    end
end)

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(3, DoorAction.Trigger)
        evt.SetDoorState(7, DoorAction.Trigger)
    end
end)

RegisterEvent(454, "Legacy event 454", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(4, DoorAction.Trigger)
        evt.SetDoorState(8, DoorAction.Trigger)
    end
end)

RegisterEvent(455, "Legacy event 455", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(14, DoorAction.Trigger)
    end
end)

RegisterEvent(456, "Legacy event 456", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(44, DoorAction.Trigger)
    end
end)

RegisterEvent(457, "Legacy event 457", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(7165, -1629, 1037, 1536, 0, 0, 0, 0)
    end
end)

RegisterEvent(458, "Legacy event 458", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.MoveToMap(1536, -1909, 1037, 1536, 0, 0, 0, 0)
    end
end)

RegisterEvent(459, "Legacy event 459", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(52, DoorAction.Open)
    end
end)

RegisterEvent(460, "Legacy event 460", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(52, DoorAction.Close)
    end
end)

RegisterEvent(461, "Legacy event 461", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(53, DoorAction.Open)
    end
end)

RegisterEvent(462, "Legacy event 462", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(53, DoorAction.Close)
    end
end)

RegisterEvent(463, "Legacy event 463", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(54, DoorAction.Open)
    end
end)

RegisterEvent(464, "Legacy event 464", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(54, DoorAction.Close)
    end
end)

RegisterEvent(465, "Legacy event 465", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(55, DoorAction.Open)
    end
end)

RegisterEvent(466, "Legacy event 466", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(55, DoorAction.Close)
    end
end)

RegisterEvent(467, "Legacy event 467", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(56, DoorAction.Open)
    end
end)

RegisterEvent(468, "Legacy event 468", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(56, DoorAction.Close)
    end
end)

RegisterEvent(469, "Legacy event 469", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(57, DoorAction.Open)
    end
end)

RegisterEvent(470, "Legacy event 470", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(57, DoorAction.Close)
    end
end)

RegisterEvent(471, "Legacy event 471", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(58, DoorAction.Open)
    end
end)

RegisterEvent(472, "Legacy event 472", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(58, DoorAction.Close)
    end
end)

RegisterEvent(473, "Legacy event 473", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(50, DoorAction.Close)
        evt.SetDoorState(47, DoorAction.Open)
        evt.SetDoorState(26, DoorAction.Open)
    end
end)

RegisterEvent(474, "Legacy event 474", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.SetDoorState(50, DoorAction.Open)
        evt.SetDoorState(51, DoorAction.Open)
    end
end)

RegisterEvent(475, "Legacy event 475", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    evt.SetLight(1, 1)
    evt.SetTexture(15, "sfpnlon")
    evt.StatusText("Power Restored")
end)

RegisterEvent(476, "Legacy event 476", function()
    if IsAtLeast(MapVar(5), 1) then
        evt.CastSpell(15, 20, 3, 4448, -9376, 2272, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 2816, -8480, 1792, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 3104, -5600, 1888, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 3104, -1888, 320, 0, 0, 0) -- Sparks
    end
end)

RegisterEvent(477, "Legacy event 477", function()
    if IsAtLeast(MapVar(5), 1) then
        evt.CastSpell(15, 20, 3, 224, 1376, 992, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 5856, -8512, 1792, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 5600, -5664, 1888, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 4896, -3808, 1888, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 3104, -3680, 320, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 512, -736, 992, 0, 0, 0) -- Sparks
        evt.CastSpell(15, 20, 3, 512, 1344, 992, 0, 0, 0) -- Sparks
    end
end)

RegisterEvent(501, "Leave the Lincoln", function()
    evt.ForPlayer(Players.Member0)
    if HasItem(1406) then -- Wetsuit
        evt.ForPlayer(Players.Member1)
        if HasItem(1406) then -- Wetsuit
            evt.ForPlayer(Players.Member2)
            if HasItem(1406) then -- Wetsuit
                evt.ForPlayer(Players.Member3)
                if HasItem(1406) then -- Wetsuit
                    evt.ForPlayer(Players.Current)
                    if HasItem(1406) then -- Wetsuit
                        evt.MoveToMap(-7005, 7856, 225, 128, 0, 0, 0, 0, "7out15.odm")
                        return
                    end
                end
            end
        end
    end
    evt.StatusText("You must all be wearing your wetsuits to exit the ship")
end, "Leave the Lincoln")

