-- Free Haven
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {212, 214},
    onLeave = {},
    openedChestIds = {
    [120] = {1},
    [121] = {2},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    { eventId = 209, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterEvent(2, "Drink from Trough.", function()
    evt.EnterHouse(28) -- Placeholder
end, "Drink from Trough.")

RegisterEvent(3, "Drink from Trough.", nil, "Drink from Trough.")

RegisterEvent(4, "Hic…", function()
    evt.EnterHouse(29) -- Fearsome Fetishes
end, "Hic…")

RegisterEvent(5, "Hic…", nil, "Hic…")

RegisterEvent(6, "Darkmoor", function()
    evt.EnterHouse(67) -- Wind
end, "Darkmoor")

RegisterEvent(7, "Darkmoor", nil, "Darkmoor")

RegisterEvent(8, "Whitecap", function()
    evt.EnterHouse(72) -- Placeholder
end, "Whitecap")

RegisterEvent(9, "Whitecap", nil, "Whitecap")

RegisterEvent(10, "The Grog and Grub", function()
    evt.EnterHouse(107) -- The Grog and Grub
end, "The Grog and Grub")

RegisterEvent(11, "The Grog and Grub", nil, "The Grog and Grub")

RegisterEvent(12, "Legacy event 12", function()
    evt.EnterHouse(1259)
end)

RegisterEvent(13, "Legacy event 13", nil)

RegisterEvent(14, "Riverglass' House", function()
    evt.EnterHouse(472) -- Riverglass' House
end, "Riverglass' House")

RegisterEvent(15, "Riverglass' House", nil, "Riverglass' House")

RegisterEvent(16, "Clearcreek's House", function()
    evt.EnterHouse(473) -- Clearcreek's House
end, "Clearcreek's House")

RegisterEvent(17, "Clearcreek's House", nil, "Clearcreek's House")

RegisterEvent(18, "House 501", function()
    evt.EnterHouse(501) -- House 501
end, "House 501")

RegisterEvent(19, "Bombah Hall", function()
    if IsQBitSet(QBit(1131)) then -- Take the Sacred Chalice from the monks in their island temple east of Free Haven, return it to Temple Stone in Free Haven, and then return to Lord Stone at Castle Stone. - NPC
        evt.ForPlayer(Players.All)
        if HasItem(2054) then -- Sacred Chalice
            RemoveItem(2054) -- Sacred Chalice
            ClearQBit(QBit(1212)) -- Quest item bits for seer
            SetQBit(QBit(1132)) -- NPC
            evt.EnterHouse(326) -- Bombah Hall
        end
        evt.EnterHouse(326) -- Bombah Hall
        return
    elseif IsQBitSet(QBit(1130)) then -- NPC
        if not IsQBitSet(QBit(1129)) then -- Hire a Stonecutter and a Carpenter, bring them to Temple Stone in Free Haven to repair the Temple, and then return to Lord Anthony Stone at Castle Stone. - NPC
            evt.SimpleMessage("You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.")
            evt.EnterHouse(326) -- Bombah Hall
            return
        end
        evt.EnterHouse(1442)
        return
    elseif IsQBitSet(QBit(1708)) then -- Replacement for HasNPCProfession ¹64 ver. 6
        if IsQBitSet(QBit(1709)) then -- Replacement for HasNPCProfession ¹63 ver. 6
            SetQBit(QBit(1130)) -- NPC
            ClearQBit(QBit(1709)) -- Replacement for HasNPCProfession ¹63 ver. 6
            ClearQBit(QBit(1708)) -- Replacement for HasNPCProfession ¹64 ver. 6
            evt.SimpleMessage("The stone cutter and carpenter begin rebuilding the temple.")
        end
        evt.EnterHouse(1442)
        return
    else
        evt.EnterHouse(1442)
        return
    end
end, "Bombah Hall")

RegisterEvent(20, "Legacy event 20", function()
    evt.EnterHouse(1584)
end)

RegisterEvent(21, "Legacy event 21", nil)

RegisterEvent(22, "Botham Hall", function()
    evt.EnterHouse(273) -- Botham Hall
end, "Botham Hall")

RegisterEvent(23, "Botham Hall", nil, "Botham Hall")

RegisterEvent(24, "Guild of Bounty Hunters", function()
    evt.EnterHouse(272) -- Guild of Bounty Hunters
end, "Guild of Bounty Hunters")

RegisterEvent(25, "Guild of Bounty Hunters", nil, "Guild of Bounty Hunters")

RegisterEvent(26, "Neblick's House", function()
    evt.EnterHouse(274) -- Neblick's House
end, "Neblick's House")

RegisterEvent(27, "Neblick's House", nil, "Neblick's House")

RegisterEvent(28, "Steele Estate", function()
    evt.EnterHouse(300) -- Steele Estate
end, "Steele Estate")

RegisterEvent(29, "Steele Estate", nil, "Steele Estate")

RegisterEvent(30, "Placeholder", function()
    evt.EnterHouse(133) -- Placeholder
end, "Placeholder")

RegisterEvent(31, "Placeholder", nil, "Placeholder")

RegisterEvent(32, "Cures and Curses", function()
    evt.EnterHouse(139) -- Cures and Curses
end, "Cures and Curses")

RegisterEvent(33, "Cures and Curses", nil, "Cures and Curses")

RegisterEvent(34, "Guild of Mind", function()
    evt.EnterHouse(145) -- Guild of Mind
end, "Guild of Mind")

RegisterEvent(35, "Guild of Mind", nil, "Guild of Mind")

RegisterEvent(36, "Placeholder", function()
    evt.EnterHouse(151) -- Placeholder
end, "Placeholder")

RegisterEvent(37, "Placeholder", nil, "Placeholder")

RegisterEvent(38, "Placeholder", function()
    evt.EnterHouse(157) -- Placeholder
end, "Placeholder")

RegisterEvent(39, "Placeholder", nil, "Placeholder")

RegisterEvent(40, "Placeholder", function()
    evt.EnterHouse(163) -- Placeholder
end, "Placeholder")

RegisterEvent(41, "Placeholder", nil, "Placeholder")

RegisterEvent(42, "Placeholder", function()
    evt.EnterHouse(169) -- Placeholder
end, "Placeholder")

RegisterEvent(43, "Placeholder", nil, "Placeholder")

RegisterEvent(44, "Cyclops Larder", function()
    evt.EnterHouse(200) -- Cyclops Larder
end, "Cyclops Larder")

RegisterEvent(45, "Cyclops Larder", nil, "Cyclops Larder")

RegisterEvent(46, "Merchanthouse of Alvar", function()
    evt.EnterHouse(195) -- Merchanthouse of Alvar
end, "Merchanthouse of Alvar")

RegisterEvent(47, "Merchanthouse of Alvar", nil, "Merchanthouse of Alvar")

RegisterEvent(48, "Pole's Hovel", function()
    evt.EnterHouse(337) -- Pole's Hovel
end, "Pole's Hovel")

RegisterEvent(49, "Pirate Stronghold", function()
    evt.EnterHouse(209) -- Pirate Stronghold
end, "Pirate Stronghold")

RegisterEvent(50, "Pirate Stronghold", nil, "Pirate Stronghold")

RegisterEvent(52, "House 507", function()
    evt.EnterHouse(507) -- House 507
end, "House 507")

RegisterEvent(53, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
end, "Hovel of Mist")

RegisterEvent(54, "Placeholder", function()
    evt.EnterHouse(105) -- Placeholder
end, "Placeholder")

RegisterEvent(55, "Placeholder", nil, "Placeholder")

RegisterEvent(56, "Blackshire", function()
    evt.EnterHouse(1221)
end, "Blackshire")

RegisterEvent(57, "Guild of Mind", function()
    evt.EnterHouse(1236)
end, "Guild of Mind")

RegisterEvent(58, "The stone cutter and carpenter begin rebuilding the temple.", function()
    evt.EnterHouse(1251)
end, "The stone cutter and carpenter begin rebuilding the temple.")

RegisterEvent(59, "You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.", function()
    evt.EnterHouse(1266)
end, "You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.")

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1281)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1296)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1309)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1321)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1332)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1344)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.EnterHouse(1356)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.EnterHouse(1368)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.EnterHouse(1379)
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.EnterHouse(1390)
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.EnterHouse(1400)
end)

RegisterEvent(71, "Legacy event 71", function()
    evt.EnterHouse(1409)
end)

RegisterEvent(72, "Legacy event 72", function()
    evt.EnterHouse(1418)
end)

RegisterEvent(73, "Legacy event 73", function()
    evt.EnterHouse(1426)
end)

RegisterEvent(74, "Legacy event 74", function()
    evt.EnterHouse(1435)
end)

RegisterEvent(75, "Legacy event 75", function()
    evt.EnterHouse(1444)
end)

RegisterEvent(76, "Legacy event 76", function()
    evt.EnterHouse(1453)
end)

RegisterEvent(77, "Legacy event 77", function()
    evt.EnterHouse(1460)
end)

RegisterEvent(78, "Legacy event 78", function()
    evt.EnterHouse(1466)
end)

RegisterEvent(79, "Legacy event 79", function()
    evt.EnterHouse(1471)
end)

RegisterEvent(80, "Legacy event 80", function()
    evt.EnterHouse(1476)
end)

RegisterEvent(81, "Legacy event 81", function()
    evt.EnterHouse(1481)
end)

RegisterEvent(82, "Legacy event 82", function()
    evt.EnterHouse(1486)
end)

RegisterEvent(83, "Legacy event 83", function()
    evt.EnterHouse(1491)
end)

RegisterEvent(84, "Legacy event 84", function()
    evt.EnterHouse(1496)
end)

RegisterEvent(85, "Legacy event 85", function()
    evt.EnterHouse(1501)
end)

RegisterEvent(86, "Legacy event 86", function()
    evt.EnterHouse(1505)
end)

RegisterEvent(87, "Legacy event 87", function()
    evt.EnterHouse(1509)
end)

RegisterEvent(88, "Legacy event 88", function()
    evt.EnterHouse(1513)
end)

RegisterEvent(89, "Legacy event 89", function()
    evt.EnterHouse(1516)
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.EnterHouse(1519)
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.EnterHouse(1522)
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.EnterHouse(1524)
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.EnterHouse(1526)
end)

RegisterEvent(94, "Legacy event 94", function()
    evt.EnterHouse(1528)
end)

RegisterEvent(95, "Legacy event 95", function()
    evt.EnterHouse(1530)
end)

RegisterEvent(96, "Legacy event 96", function()
    evt.EnterHouse(1532)
end)

RegisterEvent(97, "Legacy event 97", function()
    evt.EnterHouse(1534)
end)

RegisterEvent(98, "Legacy event 98", function()
    evt.EnterHouse(1536)
end)

RegisterEvent(99, "Legacy event 99", function()
    evt.EnterHouse(1538)
end)

RegisterEvent(100, "Legacy event 100", function()
    evt.EnterHouse(1540)
end)

RegisterEvent(101, "Legacy event 101", function()
    evt.EnterHouse(1542)
end)

RegisterEvent(102, "Legacy event 102", function()
    evt.EnterHouse(1544)
end)

RegisterEvent(103, "Legacy event 103", function()
    evt.EnterHouse(1546)
end)

RegisterEvent(104, "Legacy event 104", function()
    evt.EnterHouse(1548)
end)

RegisterEvent(105, "Legacy event 105", function()
    evt.EnterHouse(1549)
end)

RegisterEvent(106, "Legacy event 106", function()
    evt.EnterHouse(1550)
end)

RegisterEvent(107, "Drink from Trough.", function()
    evt.EnterHouse(1551)
end, "Drink from Trough.")

RegisterEvent(108, "Hic…", function()
    evt.EnterHouse(1552)
end, "Hic…")

RegisterEvent(109, "Refreshing!", function()
    evt.EnterHouse(1553)
end, "Refreshing!")

RegisterEvent(110, "Free Haven", function()
    evt.EnterHouse(1554)
end, "Free Haven")

RegisterEvent(111, "Shrine of Accuracy", function()
    evt.EnterHouse(1555)
end, "Shrine of Accuracy")

RegisterEvent(112, "You pray at the shrine.", function()
    evt.EnterHouse(1556)
end, "You pray at the shrine.")

RegisterEvent(113, "+10 Accuracy permanent", function()
    evt.EnterHouse(1557)
end, "+10 Accuracy permanent")

RegisterEvent(114, "+3 Accuracy permanent", function()
    evt.EnterHouse(1558)
end, "+3 Accuracy permanent")

RegisterEvent(115, "The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            lg____gtS_cln;__", function()
    evt.EnterHouse(1559)
end, "The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            lg____gtS_cln;__")

RegisterEvent(116, "Obelisk", function()
    evt.EnterHouse(1560)
end, "Obelisk")

RegisterEvent(117, "Free Haven", function()
    evt.EnterHouse(1561)
end, "Free Haven")

RegisterEvent(118, "Castle Temper", function()
    evt.EnterHouse(1562)
end, "Castle Temper")

RegisterEvent(119, "Temple of Baa", function()
    evt.EnterHouse(1563)
end, "Temple of Baa")

RegisterEvent(120, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(121, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(122, "Free Haven", function()
    evt.StatusText("Free Haven")
end, "Free Haven")

RegisterEvent(123, "Castle Temper", function()
    evt.StatusText("Castle Temper")
end, "Castle Temper")

RegisterEvent(124, "Temple of Baa", function()
    evt.StatusText("Temple of Baa")
end, "Temple of Baa")

RegisterEvent(125, "Free Haven", function()
    evt.StatusText("Free Haven")
end, "Free Haven")

RegisterEvent(126, "Darkmoor", function()
    evt.StatusText("Darkmoor")
end, "Darkmoor")

RegisterEvent(127, "Castle Temper", function()
    evt.StatusText("Castle Temper")
end, "Castle Temper")

RegisterEvent(128, "Guild of Water", function()
    evt.StatusText("Guild of Water")
end, "Guild of Water")

RegisterEvent(129, "Armory", function()
    evt.StatusText("Armory")
end, "Armory")

RegisterEvent(130, "Temple", function()
    evt.StatusText("Temple")
end, "Temple")

RegisterEvent(131, "Free Haven", function()
    evt.StatusText("Free Haven")
end, "Free Haven")

RegisterEvent(132, "Rockham", function()
    evt.StatusText("Rockham")
end, "Rockham")

RegisterEvent(133, "Blackshire", function()
    evt.StatusText("Blackshire")
end, "Blackshire")

RegisterEvent(134, "Rockham", function()
    evt.StatusText("Rockham")
end, "Rockham")

RegisterEvent(135, "Guild of Mind", function()
    evt.StatusText("Guild of Mind")
end, "Guild of Mind")

RegisterEvent(136, "Legacy event 136", function()
    evt.StatusText(" ")
end)

RegisterEvent(137, "Free Haven", function()
    evt.StatusText("Free Haven")
end, "Free Haven")

RegisterEvent(138, "Whitecap", function()
    evt.StatusText("Whitecap")
end, "Whitecap")

RegisterEvent(139, "Castle Stone", function()
    evt.StatusText("Castle Stone")
end, "Castle Stone")

RegisterEvent(150, "Legacy event 150", function()
    evt.MoveToMap(-2, -128, 1, 512, 0, 0, 183, 1, "6d10.blv")
end)

RegisterEvent(151, "Legacy event 151", function()
    evt.MoveToMap(-118, -1640, 1, 512, 0, 0, 187, 1, "6d14.blv")
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.MoveToMap(0, -2135, 125, 512, 0, 0, 175, 1, "6t5.blv")
end)

RegisterEvent(153, "Legacy event 153", function()
    evt.MoveToMap(7059, -6153, 1, 128, 0, 0, 195, 1, "oracle.blv")
end)

RegisterEvent(161, "Drink from Well.", function()
    if not IsAtLeast(BaseMight, 15) then
        if not IsAtLeast(MapVar(2), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(2), 1)
        AddValue(BaseMight, 2)
        evt.StatusText("+2 Might permanent")
        SetAutonote(418) -- 2 Points of permanent might from the fountain in the northeast of Free Haven.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(162, "Drink from Well.", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.SummonMonsters(1, 3, 2, -13168, 19504, 160, 0, 0) -- encounter slot 1 "BArcher" tier C, count 2, pos=(-13168, 19504, 160), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 2, -13696, 17408, 160, 0, 0) -- encounter slot 1 "BArcher" tier C, count 2, pos=(-13696, 17408, 160), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 2, -10960, 18016, 160, 0, 0) -- encounter slot 1 "BArcher" tier C, count 2, pos=(-10960, 18016, 160), actor group 0, no unique actor name
        evt.SummonMonsters(1, 3, 2, -9840, 19280, 160, 0, 0) -- encounter slot 1 "BArcher" tier C, count 2, pos=(-9840, 19280, 160), actor group 0, no unique actor name
        SetValue(MapVar(6), 1)
        evt.StatusText("Look Out!")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(163, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(419) -- 25 Hit points restored from the central fountain in Free Haven.
        return
    end
    SubtractValue(MapVar(3), 1)
    AddValue(CurrentHealth, 25)
    evt.StatusText("+25 Hit points restored.")
    SetAutonote(419) -- 25 Hit points restored from the central fountain in Free Haven.
end, "Drink from Fountain")

RegisterEvent(164, "Drink from Trough.", function()
    SetValue(PoisonedGreen, 0)
    evt.StatusText("Hic…")
end, "Drink from Trough.")

RegisterEvent(209, "Legacy event 209", function()
    if IsQBitSet(QBit(1183)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, 3823, 10974, 2700, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(210, "Legacy event 210", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1183)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1183)) -- NPC
        evt.ShowMovie("Name", true)
    else
        return
    end
end)

RegisterEvent(211, "Hiss' Hut", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 81, 1, "0.")
    evt.EnterHouse(224) -- Hiss' Hut
end, "Hiss' Hut")

RegisterEvent(212, "Legacy event 212", function()
    if IsQBitSet(QBit(1202)) then return end -- NPC
    SetQBit(QBit(1202)) -- NPC
end)

RegisterEvent(213, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            lg____gtS_cln;__")
    SetQBit(QBit(1391)) -- NPC
    SetAutonote(449) -- Obelisk Message # 8: lg____gtS_cln;__
end, "Obelisk")

RegisterEvent(214, "Legacy event 214", function()
    if IsQBitSet(QBit(1183)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Accuracy", function()
    if not IsAtLeast(MonthIs, 4) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1235)) then -- NPC
            SetQBit(QBit(1235)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseAccuracy, 10)
            evt.StatusText("+10 Accuracy permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseAccuracy, 3)
        evt.StatusText("+3 Accuracy permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Accuracy")

