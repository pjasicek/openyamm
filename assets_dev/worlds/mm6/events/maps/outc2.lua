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
    evt.EnterHouse(28) -- The Sharpening Stone
end, "Drink from Trough.")

RegisterEvent(3, "Drink from Trough.", nil, "Drink from Trough.")

RegisterEvent(4, "Hic…", function()
    evt.EnterHouse(29) -- Feathers and String
end, "Hic…")

RegisterEvent(5, "Hic…", nil, "Hic…")

RegisterEvent(6, "Darkmoor", function()
    evt.EnterHouse(67) -- The Foundry
end, "Darkmoor")

RegisterEvent(7, "Darkmoor", nil, "Darkmoor")

RegisterEvent(8, "Whitecap", function()
    evt.EnterHouse(72) -- The Footman's Friend
end, "Whitecap")

RegisterEvent(9, "Whitecap", nil, "Whitecap")

RegisterEvent(10, "Alchemy and Incantations", function()
    evt.EnterHouse(107) -- Alchemy and Incantations
end, "Alchemy and Incantations")

RegisterEvent(11, "Alchemy and Incantations", nil, "Alchemy and Incantations")

RegisterEvent(12, "Abdul's Discount Goods", function()
    evt.EnterHouse(1259) -- Abdul's Discount Goods
end, "Abdul's Discount Goods")

RegisterEvent(13, "Abdul's Discount Goods", nil, "Abdul's Discount Goods")

RegisterEvent(14, "Free Haven Travel East", function()
    evt.EnterHouse(472) -- Free Haven Travel East
end, "Free Haven Travel East")

RegisterEvent(15, "Free Haven Travel East", nil, "Free Haven Travel East")

RegisterEvent(16, "Free Haven Travel West", function()
    evt.EnterHouse(473) -- Free Haven Travel West
end, "Free Haven Travel West")

RegisterEvent(17, "Free Haven Travel West", nil, "Free Haven Travel West")

RegisterEvent(18, "Windrunner", function()
    evt.EnterHouse(501) -- Windrunner
end, "Windrunner")

RegisterEvent(19, "Free Haven Temple", function()
    if IsQBitSet(QBit(1131)) then -- Take the Sacred Chalice from the monks in their island temple east of Free Haven, return it to Temple Stone in Free Haven, and then return to Lord Stone at Castle Stone. - NPC
        evt.ForPlayer(Players.All)
        if HasItem(2054) then -- Sacred Chalice
            RemoveItem(2054) -- Sacred Chalice
            ClearQBit(QBit(1212)) -- Quest item bits for seer
            SetQBit(QBit(1132)) -- NPC
            evt.EnterHouse(326) -- Temple Stone
        end
        evt.EnterHouse(326) -- Temple Stone
        return
    elseif IsQBitSet(QBit(1130)) then -- NPC
        if not IsQBitSet(QBit(1129)) then -- Hire a Stonecutter and a Carpenter, bring them to Temple Stone in Free Haven to repair the Temple, and then return to Lord Anthony Stone at Castle Stone. - NPC
            evt.SimpleMessage("You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.")
            evt.EnterHouse(326) -- Temple Stone
            return
        end
        evt.EnterHouse(1442) -- Free Haven Temple
        return
    elseif IsQBitSet(QBit(1708)) then -- Replacement for HasNPCProfession ¹64 ver. 6
        if IsQBitSet(QBit(1709)) then -- Replacement for HasNPCProfession ¹63 ver. 6
            SetQBit(QBit(1130)) -- NPC
            ClearQBit(QBit(1709)) -- Replacement for HasNPCProfession ¹63 ver. 6
            ClearQBit(QBit(1708)) -- Replacement for HasNPCProfession ¹64 ver. 6
            evt.SimpleMessage("The stone cutter and carpenter begin rebuilding the temple.")
        end
        evt.EnterHouse(1442) -- Free Haven Temple
        return
    else
        evt.EnterHouse(1442) -- Free Haven Temple
        return
    end
end, "Free Haven Temple")

RegisterEvent(20, "Free Haven Academy", function()
    evt.EnterHouse(1584) -- Free Haven Academy
end, "Free Haven Academy")

RegisterEvent(21, "Free Haven Academy", nil, "Free Haven Academy")

RegisterEvent(22, "The Echoing Whisper", function()
    evt.EnterHouse(273) -- The Echoing Whisper
end, "The Echoing Whisper")

RegisterEvent(23, "The Echoing Whisper", nil, "The Echoing Whisper")

RegisterEvent(24, "Viktor's Hall", function()
    evt.EnterHouse(272) -- Viktor's Hall
end, "Viktor's Hall")

RegisterEvent(25, "Viktor's Hall", nil, "Viktor's Hall")

RegisterEvent(26, "Rockham's Pride", function()
    evt.EnterHouse(274) -- Rockham's Pride
end, "Rockham's Pride")

RegisterEvent(27, "Rockham's Pride", nil, "Rockham's Pride")

RegisterEvent(28, "Foreign Exchange", function()
    evt.EnterHouse(300) -- Foreign Exchange
end, "Foreign Exchange")

RegisterEvent(29, "Foreign Exchange", nil, "Foreign Exchange")

RegisterEvent(30, "Adept Guild of Fire", function()
    evt.EnterHouse(133) -- Adept Guild of Fire
end, "Adept Guild of Fire")

RegisterEvent(31, "Adept Guild of Fire", nil, "Adept Guild of Fire")

RegisterEvent(32, "Adept Guild of Air", function()
    evt.EnterHouse(139) -- Adept Guild of Air
end, "Adept Guild of Air")

RegisterEvent(33, "Adept Guild of Air", nil, "Adept Guild of Air")

RegisterEvent(34, "Adept Guild of Water", function()
    evt.EnterHouse(145) -- Adept Guild of Water
end, "Adept Guild of Water")

RegisterEvent(35, "Adept Guild of Water", nil, "Adept Guild of Water")

RegisterEvent(36, "Adept Guild of Earth", function()
    evt.EnterHouse(151) -- Adept Guild of Earth
end, "Adept Guild of Earth")

RegisterEvent(37, "Adept Guild of Earth", nil, "Adept Guild of Earth")

RegisterEvent(38, "Adept Guild of Spirit", function()
    evt.EnterHouse(157) -- Adept Guild of Spirit
end, "Adept Guild of Spirit")

RegisterEvent(39, "Adept Guild of Spirit", nil, "Adept Guild of Spirit")

RegisterEvent(40, "Adept Guild of Mind", function()
    evt.EnterHouse(163) -- Adept Guild of Mind
end, "Adept Guild of Mind")

RegisterEvent(41, "Adept Guild of Mind", nil, "Adept Guild of Mind")

RegisterEvent(42, "Adept Guild of Body", function()
    evt.EnterHouse(169) -- Adept Guild of Body
end, "Adept Guild of Body")

RegisterEvent(43, "Adept Guild of Body", nil, "Adept Guild of Body")

RegisterEvent(44, "Duelists' Edge", function()
    evt.EnterHouse(200) -- Duelists' Edge
end, "Duelists' Edge")

RegisterEvent(45, "Duelists' Edge", nil, "Duelists' Edge")

RegisterEvent(46, "Smugglers' Guild", function()
    evt.EnterHouse(195) -- Smugglers' Guild
end, "Smugglers' Guild")

RegisterEvent(47, "Smugglers' Guild", nil, "Smugglers' Guild")

RegisterEvent(48, "Castle Temper", function()
    evt.EnterHouse(337) -- Castle Temper
end, "Castle Temper")

RegisterEvent(49, "High Council", function()
    evt.EnterHouse(209) -- High Council
end, "High Council")

RegisterEvent(50, "High Council", nil, "High Council")

RegisterEvent(52, "Enterprise", function()
    evt.EnterHouse(507) -- Enterprise
end, "Enterprise")

RegisterEvent(53, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

RegisterEvent(54, "The Sorcerer's Shoppe", function()
    evt.EnterHouse(105) -- The Sorcerer's Shoppe
end, "The Sorcerer's Shoppe")

RegisterEvent(55, "The Sorcerer's Shoppe", nil, "The Sorcerer's Shoppe")

RegisterEvent(56, "Blackshire", function()
    evt.EnterHouse(1221) -- House
end, "Blackshire")

RegisterEvent(57, "Guild of Mind", function()
    evt.EnterHouse(1236) -- House
end, "Guild of Mind")

RegisterEvent(58, "The stone cutter and carpenter begin rebuilding the temple.", function()
    evt.EnterHouse(1251) -- House
end, "The stone cutter and carpenter begin rebuilding the temple.")

RegisterEvent(59, "You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.", function()
    evt.EnterHouse(1266) -- House
end, "You hand the Sacred Chalice to the monks of the temple who ensconce it in the main altar.")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1281) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1296) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1309) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1321) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1332) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1344) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1356) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1368) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1379) -- House
end, "House")

RegisterEvent(69, "House", function()
    evt.EnterHouse(1390) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1400) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1409) -- House
end, "House")

RegisterEvent(72, "House", function()
    evt.EnterHouse(1418) -- House
end, "House")

RegisterEvent(73, "House", function()
    evt.EnterHouse(1426) -- House
end, "House")

RegisterEvent(74, "House", function()
    evt.EnterHouse(1435) -- House
end, "House")

RegisterEvent(75, "House", function()
    evt.EnterHouse(1444) -- House
end, "House")

RegisterEvent(76, "House", function()
    evt.EnterHouse(1453) -- House
end, "House")

RegisterEvent(77, "House", function()
    evt.EnterHouse(1460) -- House
end, "House")

RegisterEvent(78, "House", function()
    evt.EnterHouse(1466) -- House
end, "House")

RegisterEvent(79, "House", function()
    evt.EnterHouse(1471) -- House
end, "House")

RegisterEvent(80, "House", function()
    evt.EnterHouse(1476) -- House
end, "House")

RegisterEvent(81, "House", function()
    evt.EnterHouse(1481) -- House
end, "House")

RegisterEvent(82, "House", function()
    evt.EnterHouse(1486) -- House
end, "House")

RegisterEvent(83, "House", function()
    evt.EnterHouse(1491) -- House
end, "House")

RegisterEvent(84, "House", function()
    evt.EnterHouse(1496) -- House
end, "House")

RegisterEvent(85, "House", function()
    evt.EnterHouse(1501) -- House
end, "House")

RegisterEvent(86, "House", function()
    evt.EnterHouse(1505) -- House
end, "House")

RegisterEvent(87, "House", function()
    evt.EnterHouse(1509) -- House
end, "House")

RegisterEvent(88, "House", function()
    evt.EnterHouse(1513) -- House
end, "House")

RegisterEvent(89, "House", function()
    evt.EnterHouse(1516) -- House
end, "House")

RegisterEvent(90, "House", function()
    evt.EnterHouse(1519) -- House
end, "House")

RegisterEvent(91, "House", function()
    evt.EnterHouse(1522) -- House
end, "House")

RegisterEvent(92, "House", function()
    evt.EnterHouse(1524) -- House
end, "House")

RegisterEvent(93, "House", function()
    evt.EnterHouse(1526) -- House
end, "House")

RegisterEvent(94, "House", function()
    evt.EnterHouse(1528) -- House
end, "House")

RegisterEvent(95, "House", function()
    evt.EnterHouse(1530) -- House
end, "House")

RegisterEvent(96, "House", function()
    evt.EnterHouse(1532) -- House
end, "House")

RegisterEvent(97, "House", function()
    evt.EnterHouse(1534) -- House
end, "House")

RegisterEvent(98, "House", function()
    evt.EnterHouse(1536) -- House
end, "House")

RegisterEvent(99, "House", function()
    evt.EnterHouse(1538) -- House
end, "House")

RegisterEvent(100, "House", function()
    evt.EnterHouse(1540) -- House
end, "House")

RegisterEvent(101, "House", function()
    evt.EnterHouse(1542) -- House
end, "House")

RegisterEvent(102, "House", function()
    evt.EnterHouse(1544) -- House
end, "House")

RegisterEvent(103, "House", function()
    evt.EnterHouse(1546) -- House
end, "House")

RegisterEvent(104, "House", function()
    evt.EnterHouse(1548) -- House
end, "House")

RegisterEvent(105, "House", function()
    evt.EnterHouse(1549) -- House
end, "House")

RegisterEvent(106, "House", function()
    evt.EnterHouse(1550) -- House
end, "House")

RegisterEvent(107, "Drink from Trough.", function()
    evt.EnterHouse(1551) -- House
end, "Drink from Trough.")

RegisterEvent(108, "Hic…", function()
    evt.EnterHouse(1552) -- House
end, "Hic…")

RegisterEvent(109, "Refreshing!", function()
    evt.EnterHouse(1553) -- House
end, "Refreshing!")

RegisterEvent(110, "Free Haven", function()
    evt.EnterHouse(1554) -- House
end, "Free Haven")

RegisterEvent(111, "Shrine of Accuracy", function()
    evt.EnterHouse(1555) -- House
end, "Shrine of Accuracy")

RegisterEvent(112, "You pray at the shrine.", function()
    evt.EnterHouse(1556) -- House
end, "You pray at the shrine.")

RegisterEvent(113, "+10 Accuracy permanent", function()
    evt.EnterHouse(1557) -- House
end, "+10 Accuracy permanent")

RegisterEvent(114, "+3 Accuracy permanent", function()
    evt.EnterHouse(1558) -- House
end, "+3 Accuracy permanent")

RegisterEvent(115, "The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            lg____gtS_cln;__", function()
    evt.EnterHouse(1559) -- House
end, "The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            lg____gtS_cln;__")

RegisterEvent(116, "Obelisk", function()
    evt.EnterHouse(1560) -- House
end, "Obelisk")

RegisterEvent(117, "Free Haven", function()
    evt.EnterHouse(1561) -- House
end, "Free Haven")

RegisterEvent(118, "Castle Temper", function()
    evt.EnterHouse(1562) -- House
end, "Castle Temper")

RegisterEvent(119, "Temple of Baa", function()
    evt.EnterHouse(1563) -- House
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

RegisterEvent(211, "Throne Room", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 81, 1, "0.")
    evt.EnterHouse(224) -- Throne Room
end, "Throne Room")

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

