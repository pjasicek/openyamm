-- Castle Ironfist
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535},
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
    evt.EnterHouse(24) -- Fine Blades
end, "Keep Off!")

RegisterEvent(3, "Keep Off!", nil, "Keep Off!")

RegisterEvent(4, "+10 Hit Points restored.", function()
    evt.EnterHouse(64) -- Metalweave Armory
end, "+10 Hit Points restored.")

RegisterEvent(5, "+10 Hit Points restored.", nil, "+10 Hit Points restored.")

RegisterEvent(6, "Eye of Newt", function()
    evt.EnterHouse(101) -- Eye of Newt
end, "Eye of Newt")

RegisterEvent(7, "Eye of Newt", nil, "Eye of Newt")

RegisterEvent(8, "Royal Lines ", function()
    evt.EnterHouse(471) -- Royal Lines
end, "Royal Lines ")

RegisterEvent(9, "Royal Lines ", nil, "Royal Lines ")

RegisterEvent(10, "Royal Gymnasium", function()
    evt.EnterHouse(1589) -- Royal Gymnasium
end, "Royal Gymnasium")

RegisterEvent(11, "Royal Gymnasium", nil, "Royal Gymnasium")

RegisterEvent(12, "The King's Crown", function()
    evt.EnterHouse(264) -- The King's Crown
end, "The King's Crown")

RegisterEvent(13, "The King's Crown", nil, "The King's Crown")

RegisterEvent(14, "Initiate Guild of Fire", function()
    evt.EnterHouse(132) -- Initiate Guild of Fire
end, "Initiate Guild of Fire")

RegisterEvent(15, "Initiate Guild of Fire", nil, "Initiate Guild of Fire")

RegisterEvent(16, "Castle Newton", function()
    evt.EnterHouse(336) -- Castle Newton
end, "Castle Newton")

RegisterEvent(17, "Castle Newton", nil, "Castle Newton")

RegisterEvent(18, "The Seer", function()
    evt.EnterHouse(450) -- The Seer
end, "The Seer")

RegisterEvent(19, "King's Temple", function()
    evt.EnterHouse(332) -- King's Temple
end, "King's Temple")

RegisterEvent(40, "New Sorpigal", function()
    evt.StatusText("New Sorpigal")
end, "New Sorpigal")

RegisterEvent(41, "Ironfist Castle", function()
    evt.StatusText("Ironfist Castle")
end, "Ironfist Castle")

RegisterEvent(42, "King's Library", function()
    if not IsQBitSet(QBit(1201)) then -- NPC
        evt.EnterHouse(1215) -- King's Library
        return
    end
    evt.EnterHouse(0)
end, "King's Library")

RegisterEvent(43, "Throne Room", function()
    if IsQBitSet(QBit(1114)) then -- Entertain Nicolai. - Paul
        if not IsQBitSet(QBit(1700)) then -- Replacement for NPCs ¹13 ver. 6
            evt.SimpleMessage("The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!")
        end
        evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
        evt.EnterHouse(222) -- Throne Room
        return
    elseif IsQBitSet(QBit(1119)) then -- Find and return Prince Nicolai to Castle Ironfist. - Walt
        if IsQBitSet(QBit(1700)) then -- Replacement for NPCs ¹13 ver. 6
            evt.MoveNPC(798, 222) -- Nicolai Ironfist -> Throne Room
            ClearQBit(QBit(1700)) -- Replacement for NPCs ¹13 ver. 6
            ClearQBit(QBit(1119)) -- Find and return Prince Nicolai to Castle Ironfist. - Walt
            evt.SimpleMessage("\"Well, thanks for sneaking me out of the Castle.  Sorry about the circus thing—I hope I wasn’t too much trouble to find.  I’ll go in myself so no one will see that it was you who kidnapped me.  Thanks again, and goodbye.  I’ll remember this, and I owe you a favor! \"")
            evt.ForPlayer(Players.All)
            AddValue(Experience, 7500)
            evt.SetNPCTopic(798, 0, 1337) -- Nicolai Ironfist topic 0: The Circus
            evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
            evt.EnterHouse(222) -- Throne Room
            return
        end
        evt.SimpleMessage("The prince has been kidnapped!  No visitors will be admitted until this crisis has been resolved!")
    else
        evt.MoveToMap(0, 0, 0, 0, 0, 0, 79, 1, "0.")
        evt.EnterHouse(222) -- Throne Room
        return
    end
end, "Throne Room")

RegisterEvent(44, "Zephyr", function()
    evt.EnterHouse(497) -- Zephyr
end, "Zephyr")

RegisterEvent(45, "Queen Catherine", function()
    evt.EnterHouse(498) -- Queen Catherine
end, "Queen Catherine")

RegisterEvent(46, "Ironfist Castle", function()
    evt.EnterHouse(25) -- The Eagle's Eye
end, "Ironfist Castle")

RegisterEvent(47, "Ironfist Castle", nil, "Ironfist Castle")

RegisterEvent(48, "+3 Electricity resistance permanent", function()
    evt.EnterHouse(68) -- Iron Defense
end, "+3 Electricity resistance permanent")

RegisterEvent(49, "+3 Electricity resistance permanent", nil, "+3 Electricity resistance permanent")

RegisterEvent(50, "The Will o' Wisp", function()
    evt.EnterHouse(265) -- The Will o' Wisp
end, "The Will o' Wisp")

RegisterEvent(51, "The Will o' Wisp", nil, "The Will o' Wisp")

RegisterEvent(52, "Initiate Guild of Spirit", function()
    evt.EnterHouse(156) -- Initiate Guild of Spirit
end, "Initiate Guild of Spirit")

RegisterEvent(53, "Initiate Guild of Spirit", nil, "Initiate Guild of Spirit")

RegisterEvent(54, "Initiate Guild of Mind", function()
    evt.EnterHouse(162) -- Initiate Guild of Mind
end, "Initiate Guild of Mind")

RegisterEvent(55, "Initiate Guild of Mind", nil, "Initiate Guild of Mind")

RegisterEvent(56, "Initiate Guild of Body", function()
    evt.EnterHouse(168) -- Initiate Guild of Body
end, "Initiate Guild of Body")

RegisterEvent(57, "Initiate Guild of Body", nil, "Initiate Guild of Body")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1225) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1240) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1255) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1285) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1300) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1313) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1325) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1359) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1371) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1382) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1393) -- House
end, "House")

RegisterEvent(69, "House", function()
    evt.EnterHouse(1412) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1421) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1270) -- House
    evt.EnterHouse(1336) -- House
end, "House")

RegisterEvent(72, "House", function()
    evt.EnterHouse(1348) -- House
end, "House")

RegisterEvent(73, "House", function()
    evt.EnterHouse(1403) -- House
end, "House")

RegisterEvent(74, "House", function()
    evt.EnterHouse(1429) -- House
end, "House")

RegisterEvent(75, "House", function()
    evt.EnterHouse(1438) -- House
end, "House")

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

RegisterEvent(82, "Berserkers' Fury", function()
    evt.EnterHouse(202) -- Berserkers' Fury
end, "Berserkers' Fury")

RegisterEvent(83, "Castle Ironfist", function()
    evt.EnterHouse(1387) -- House
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

RegisterEvent(97, "Temple Baa", function()
    evt.EnterHouse(334) -- Temple Baa
end, "Temple Baa")

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

RegisterEvent(225, "Legacy event 225", function(continueStep)
    local function Step_0()
        if IsQBitSet(QBit(1327)) then return 8 end -- NPC
        return 1
    end
    local function Step_1()
        if IsAtLeast(ActualMight, 40) then return 5 end
        return 2
    end
    local function Step_2()
        evt.FaceExpression(51)
        return 3
    end
    local function Step_3()
        evt.StatusText("The Sword won't budge!")
        return 4
    end
    local function Step_4()
        return 8
    end
    local function Step_5()
        SetQBit(QBit(1327)) -- NPC
        return 6
    end
    local function Step_6()
        evt.GiveItem(4, 23, 1609) -- Barbarian Flamberge
        return 7
    end
    local function Step_7()
        evt.SetSprite(232, 1, "swrdstx")
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_10()
        if IsQBitSet(QBit(1327)) then return 7 end -- NPC
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        elseif step == 10 then
            step = Step_10()
        else
            step = nil
        end
    end
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

RegisterEvent(65535, "", function()
    return evt.map[225](10)
end)

