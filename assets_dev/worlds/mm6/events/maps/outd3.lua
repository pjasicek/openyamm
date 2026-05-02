-- Castle Ironfist
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {225},
    onLeave = {},
    openedChestIds = {
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    [80] = {6},
    [81] = {1},
    },
    textureNames = {},
    spriteNames = {"swrdstx"},
    castSpellIds = {98},
    timers = {
    { eventId = 200, repeating = true, intervalGameMinutes = 30, remainingGameMinutes = 30 },
    },
})

RegisterEvent(2, "Keep Off!", function()
    evt.EnterHouse(24) -- Placeholder
end, "Keep Off!")

RegisterEvent(3, "Keep Off!", nil, "Keep Off!")

RegisterEvent(4, "+10 Hit Points restored.", function()
    evt.EnterHouse(64) -- The Dauntless
end, "+10 Hit Points restored.")

RegisterEvent(5, "+10 Hit Points restored.", nil, "+10 Hit Points restored.")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(101) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Empty House", function()
    evt.EnterHouse(471) -- Empty House
end, "Empty House")

RegisterEvent(9, "Empty House", nil, "Empty House")

RegisterEvent(10, "Legacy event 10", function()
    evt.EnterHouse(1589)
end)

RegisterEvent(11, "Legacy event 11", nil)

RegisterEvent(12, "Laraselle Estate", function()
    evt.EnterHouse(264) -- Laraselle Estate
end, "Laraselle Estate")

RegisterEvent(13, "Laraselle Estate", nil, "Laraselle Estate")

RegisterEvent(14, "Bank of Balthazar", function()
    evt.EnterHouse(132) -- Bank of Balthazar
end, "Bank of Balthazar")

RegisterEvent(15, "Bank of Balthazar", nil, "Bank of Balthazar")

RegisterEvent(16, "Hovel of Greenstorm", function()
    evt.EnterHouse(336) -- Hovel of Greenstorm
end, "Hovel of Greenstorm")

RegisterEvent(17, "Hovel of Greenstorm", nil, "Hovel of Greenstorm")

RegisterEvent(18, "Nedlon's House", function()
    evt.EnterHouse(450) -- Nedlon's House
end, "Nedlon's House")

RegisterEvent(19, "Hearthsworn Hovel", function()
    evt.EnterHouse(332) -- Hearthsworn Hovel
end, "Hearthsworn Hovel")

RegisterEvent(40, "New Sorpigal", function()
    evt.StatusText("New Sorpigal")
end, "New Sorpigal")

RegisterEvent(41, "Ironfist Castle", function()
    evt.StatusText("Ironfist Castle")
end, "Ironfist Castle")

RegisterEvent(42, "Legacy event 42", function()
    if not IsQBitSet(QBit(1201)) then -- NPC
        evt.EnterHouse(1215)
        return
    end
    evt.EnterHouse(0)
end)

RegisterEvent(43, "Gateway to the Plane of Air", function()
    if IsQBitSet(QBit(1114)) then -- Entertain Nicolai. - Paul
        if not IsQBitSet(QBit(1700)) then -- Replacement for NPCs ¹13 ver. 6
            evt.SimpleMessage("The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!")
        end
        evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
        evt.EnterHouse(222) -- Gateway to the Plane of Air
        return
    elseif IsQBitSet(QBit(1119)) then -- Find and return Prince Nicolai to Castle Ironfist. - Walt
        if IsQBitSet(QBit(1700)) then -- Replacement for NPCs ¹13 ver. 6
            evt.MoveNPC(798, 222) -- Nicolai Ironfist -> Gateway to the Plane of Air
            ClearQBit(QBit(1700)) -- Replacement for NPCs ¹13 ver. 6
            ClearQBit(QBit(1119)) -- Find and return Prince Nicolai to Castle Ironfist. - Walt
            evt.SimpleMessage("\"Well, thanks for sneaking me out of the Castle.  Sorry about the circus thing—I hope I wasn’t too much trouble to find.  I’ll go in myself so no one will see that it was you who kidnapped me.  Thanks again, and goodbye.  I’ll remember this, and I owe you a favor! \"")
            evt.ForPlayer(Players.All)
            AddValue(Experience, 7500)
            evt.SetNPCTopic(798, 0, 1337) -- Nicolai Ironfist topic 0: The Circus
            evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
            evt.EnterHouse(222) -- Gateway to the Plane of Air
            return
        end
        evt.SimpleMessage("The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!")
    else
        evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
        evt.EnterHouse(222) -- Gateway to the Plane of Air
        return
    end
end, "Gateway to the Plane of Air")

RegisterEvent(44, "House 497", function()
    evt.EnterHouse(497) -- House 497
end, "House 497")

RegisterEvent(45, "House 498", function()
    evt.EnterHouse(498) -- House 498
end, "House 498")

RegisterEvent(46, "Ironfist Castle", function()
    evt.EnterHouse(25) -- Placeholder
end, "Ironfist Castle")

RegisterEvent(47, "Ironfist Castle", nil, "Ironfist Castle")

RegisterEvent(48, "+3 Electricity resistance permanent", function()
    evt.EnterHouse(68) -- Spindrift
end, "+3 Electricity resistance permanent")

RegisterEvent(49, "+3 Electricity resistance permanent", nil, "+3 Electricity resistance permanent")

RegisterEvent(50, "Hillsman Cottage", function()
    evt.EnterHouse(265) -- Hillsman Cottage
end, "Hillsman Cottage")

RegisterEvent(51, "Hillsman Cottage", nil, "Hillsman Cottage")

RegisterEvent(52, "Placeholder", function()
    evt.EnterHouse(156) -- Placeholder
end, "Placeholder")

RegisterEvent(53, "Placeholder", nil, "Placeholder")

RegisterEvent(54, "Placeholder", function()
    evt.EnterHouse(162) -- Placeholder
end, "Placeholder")

RegisterEvent(55, "Placeholder", nil, "Placeholder")

RegisterEvent(56, "Placeholder", function()
    evt.EnterHouse(168) -- Placeholder
end, "Placeholder")

RegisterEvent(57, "Placeholder", nil, "Placeholder")

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1225)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1240)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1255)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1285)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1300)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1313)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1325)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1359)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.EnterHouse(1371)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.EnterHouse(1382)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.EnterHouse(1393)
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.EnterHouse(1412)
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.EnterHouse(1421)
end)

RegisterEvent(71, "Legacy event 71", function()
    evt.EnterHouse(1270)
    evt.EnterHouse(1336)
end)

RegisterEvent(72, "Legacy event 72", function()
    evt.EnterHouse(1348)
end)

RegisterEvent(73, "Legacy event 73", function()
    evt.EnterHouse(1403)
end)

RegisterEvent(74, "Legacy event 74", function()
    evt.EnterHouse(1429)
end)

RegisterEvent(75, "Legacy event 75", function()
    evt.EnterHouse(1438)
end)

RegisterEvent(76, "Crate", function()
    evt.OpenChest(2)
end, "Crate")

RegisterEvent(77, "Crate", function()
    evt.OpenChest(3)
end, "Crate")

RegisterEvent(78, "Crate", function()
    evt.OpenChest(4)
end, "Crate")

RegisterEvent(79, "Crate", function()
    evt.OpenChest(5)
end, "Crate")

RegisterEvent(80, "Crate", function()
    evt.OpenChest(6)
end, "Crate")

RegisterEvent(81, "Crate", function()
    evt.OpenChest(1)
end, "Crate")

RegisterEvent(82, "Dragon Hunter Camp", function()
    evt.EnterHouse(202) -- Dragon Hunter Camp
end, "Dragon Hunter Camp")

RegisterEvent(83, "Castle Ironfist", function()
    evt.EnterHouse(1387)
end, "Castle Ironfist")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(-130, -1408, 1, 512, 0, 0, 169, 1, "6d03.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.MoveToMap(1664, -1896, 1, 1024, 0, 0, 174, 1, "6d05.blv")
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.MoveToMap(2716, -256, 1, 1024, 0, 0, 176, 1, "6d06.blv")
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.MoveToMap(128, -151, 1, 512, 0, 0, 184, 1, "6d11.blv")
end)

RegisterEvent(94, "Legacy event 94", function()
    evt.MoveToMap(-15592, 120, -191, 0, 0, 0, 162, 1, "6t1.blv")
end)

RegisterEvent(97, "Hovel of Mist", function()
    evt.EnterHouse(334) -- Hovel of Mist
end, "Hovel of Mist")

RegisterEvent(100, "Drink from Fountain", function()
    if not IsAtLeast(SpeedBonus, 10) then
        SetValue(SpeedBonus, 10)
        evt.StatusText("+10 Speed temporary.")
        SetAutonote(408) -- 10 Points of temporary speed from the east fountain at Castle Ironfist.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(101, "Drink from Fountain", function()
    if IsAtLeast(AccuracyBonus, 10) then return end
    SetValue(AccuracyBonus, 10)
    evt.StatusText("+10 Accuracy temporary.")
    SetAutonote(407) -- 10 Points of temporary accuracy from the west fountain at Castle Ironfist.
end, "Drink from Fountain")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(26), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(409) -- 10 Hit points restored from the fountain in the Arena.
        return
    end
    SubtractValue(MapVar(26), 1)
    AddValue(CurrentHealth, 10)
    evt.StatusText("+10 Hit Points restored.")
    SetAutonote(409) -- 10 Hit points restored from the fountain in the Arena.
end, "Drink from Fountain")

RegisterEvent(200, "Legacy event 200", function()
    if IsAtLeast(MapVar(3), 8) then
        return
    elseif IsAtLeast(MapVar(2), 1) then
        evt.SummonObject(8080, -12024, -3784, 400, 512, 1, true)
        evt.SummonObject(8080, -12032, -4744, 400, 512, 1, true)
        evt.SummonObject(8080, -12040, -2712, 640, 750, 1, true)
        evt.SummonMonsters(1, 1, 2, -13040, -2424, 645, 0, 0) -- encounter slot 1 "LizardArch" tier A, count 2, pos=(-13040, -2424, 645), actor group 0, no unique actor name
        evt.SummonMonsters(1, 2, 2, -10392, -2224, 645, 0, 0) -- encounter slot 1 "LizardArch" tier B, count 2, pos=(-10392, -2224, 645), actor group 0, no unique actor name
        evt.SummonMonsters(3, 1, 2, -12752, -3856, 640, 0, 0) -- encounter slot 3 "PeasantM3" tier A, count 2, pos=(-12752, -3856, 640), actor group 0, no unique actor name
        evt.SummonMonsters(3, 2, 2, -11328, -3808, 640, 0, 0) -- encounter slot 3 "PeasantM3" tier B, count 2, pos=(-11328, -3808, 640), actor group 0, no unique actor name
        AddValue(MapVar(3), 1)
    else
        return
    end
end)

RegisterEvent(201, "Keep Off!", function()
    SetValue(MapVar(2), 1)
    evt.MoveToMap(-12045, -6073, 2, 512, 0, 0, 0, 0)
end, "Keep Off!")

RegisterEvent(202, "Keep Off!", function()
    SetValue(MapVar(2), 0)
end, "Keep Off!")

RegisterEvent(203, "Keep Off!", function()
    evt.SetSnow(1, 0)
    evt.MoveToMap(17920, 14344, 2080, 1024, 0, 0, 0, 0)
end, "Keep Off!")

RegisterEvent(210, "Legacy event 210", function(continueStep)
    if continueStep == 8 then
        evt.AskQuestion(210, 9, 8, 14, 10, 10, "Refreshing!", {"Crate", "Crate"})
        return nil
    end
    if continueStep == 9 then
        if not IsAtLeast(Gold, 100) then
            evt.SimpleMessage("Well")
            evt.MoveToMap(4856, 10288, 0, 500, 0, 0, 0, 0)
            return
        end
        SubtractValue(Gold, 100)
        SetValue(MapVar(6), 0)
    end
    if continueStep == 9 then
        if not IsAtLeast(Gold, 100) then
            evt.SimpleMessage("Well")
            evt.MoveToMap(4856, 10288, 0, 500, 0, 0, 0, 0)
            return
        end
        SubtractValue(Gold, 100)
        SetValue(MapVar(6), 0)
    end
    if continueStep == 14 then
        evt.SummonMonsters(1, 2, 5, 4920, 12976, 0, 0, 0) -- encounter slot 1 "LizardArch" tier B, count 5, pos=(4920, 12976, 0), actor group 0, no unique actor name
        SetValue(MapVar(6), 0)
    end
    if continueStep ~= nil then return end
    if IsAtLeast(MapVar(6), 0) then return end
    evt.CastSpell(98, 1, 1, 5784, 11584, 512, 5784, 11584, 0) -- Armageddon
    evt.CastSpell(98, 1, 1, 4312, 11600, 512, 4312, 11600, 0) -- Armageddon
    evt.SimpleMessage("All Hit points restored.")
    evt.SimpleMessage("Chest")
    evt.AskQuestion(210, 8, 8, 9, 9, 9, "Refreshing!", {"The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!", "The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!"})
    return nil
end)

RegisterEvent(220, "Legacy event 220", function()
    if not IsAtLeast(MapVar(11), 1) then
        SetValue(MapVar(11), 1)
        evt.SetFacetBit(1, FacetBits.Invisible, 1)
        return
    end
    SetValue(MapVar(11), 0)
    evt.SetFacetBit(1, FacetBits.Invisible, 0)
end)

RegisterEvent(221, "Legacy event 221", function()
    if not IsAtLeast(MapVar(16), 1) then
        SetValue(MapVar(16), 1)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        return
    end
    SetValue(MapVar(16), 0)
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
end)

RegisterEvent(225, "Legacy event 225", function()
    if IsQBitSet(QBit(1327)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 40) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1327)) -- NPC
    evt.GiveItem(4, 23, 1609) -- Barbarian Flamberge
    evt.SetSprite(232, 1, "swrdstx")
end)

RegisterEvent(230, "Legacy event 230", function()
    if IsAtLeast(MapVar(21), 1) then return end
    AddValue(InventoryItem(1810), 1810) -- Meteor Shower
    SetValue(MapVar(21), 1)
end)

RegisterEvent(231, "Well", function()
    if IsQBitSet(QBit(1329)) then return end -- NPC
    if IsQBitSet(QBit(1120)) then -- Find the Third Eye and bring it to Prince Nicolai in Castle Ironfist. - Walt
        AddValue(InventoryItem(2066), 2066) -- The Third Eye
        SetQBit(QBit(1329)) -- NPC
        SetQBit(QBit(1220)) -- Quest item bits for seer
    end
end, "Well")

RegisterEvent(232, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _t_staoi_on_oiz_")
    SetQBit(QBit(1395)) -- NPC
    SetAutonote(453) -- Obelisk Message # 12: _t_staoi_on_oiz_
end, "Obelisk")

RegisterEvent(261, "Shrine of Electricity", function()
    if not IsAtLeast(MonthIs, 8) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1239)) then -- NPC
            SetQBit(QBit(1239)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(AirResistance, 10)
            evt.StatusText("+10 Electricity resistance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(AirResistance, 3)
        evt.StatusText("+3 Electricity resistance permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Electricity")

