-- Silver Cove
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535, 65534, 65533, 223, 226},
    onLeave = {},
    openedChestIds = {
    [100] = {1},
    [101] = {2},
    [102] = {3},
    },
    textureNames = {},
    spriteNames = {"swrdstx"},
    castSpellIds = {6},
    timers = {
    { eventId = 209, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterEvent(2, "+2 Speed permanent.", function()
    evt.EnterHouse(31) -- Abdul's Discount Weapons
end, "+2 Speed permanent.")

RegisterEvent(3, "+2 Speed permanent.", nil, "+2 Speed permanent.")

RegisterEvent(4, "Abdul's Discount Armor", function()
    evt.EnterHouse(69) -- Abdul's Discount Armor
end, "Abdul's Discount Armor")

RegisterEvent(5, "Abdul's Discount Armor", nil, "Abdul's Discount Armor")

RegisterEvent(6, "Abdul's Discount Magic Supplies", function()
    evt.EnterHouse(100) -- Abdul's Discount Magic Supplies
end, "Abdul's Discount Magic Supplies")

RegisterEvent(7, "Abdul's Discount Magic Supplies", nil, "Abdul's Discount Magic Supplies")

RegisterEvent(8, "Trader Joe's", function()
    evt.EnterHouse(1245) -- Trader Joe's
end, "Trader Joe's")

RegisterEvent(9, "Trader Joe's", nil, "Trader Joe's")

RegisterEvent(10, "Abdul's Discount Travel", function()
    evt.EnterHouse(475) -- Abdul's Discount Travel
end, "Abdul's Discount Travel")

RegisterEvent(11, "Abdul's Discount Travel", nil, "Abdul's Discount Travel")

RegisterEvent(12, "Cerulean Skies", function()
    evt.EnterHouse(500) -- Cerulean Skies
end, "Cerulean Skies")

RegisterEvent(13, "Silver Cove Temple", function()
    evt.EnterHouse(331) -- Silver Cove Temple
end, "Silver Cove Temple")

RegisterEvent(14, "Abdul's Discount Training Center", function()
    evt.EnterHouse(1585) -- Abdul's Discount Training Center
end, "Abdul's Discount Training Center")

RegisterEvent(15, "Abdul's Discount Training Center", nil, "Abdul's Discount Training Center")

RegisterEvent(16, "Town Hall", function()
    evt.EnterHouse(211) -- Town Hall
end, "Town Hall")

RegisterEvent(17, "Anchors Away", function()
    evt.EnterHouse(268) -- Anchors Away
end, "Anchors Away")

RegisterEvent(18, "Anchors Away", nil, "Anchors Away")

RegisterEvent(19, "The Grove", function()
    evt.EnterHouse(269) -- The Grove
end, "The Grove")

RegisterEvent(20, "The Grove", nil, "The Grove")

RegisterEvent(21, "The First Bank of Enroth", function()
    evt.EnterHouse(299) -- The First Bank of Enroth
end, "The First Bank of Enroth")

RegisterEvent(22, "The First Bank of Enroth", nil, "The First Bank of Enroth")

RegisterEvent(23, "Initiate Guild of Earth", function()
    evt.EnterHouse(150) -- Initiate Guild of Earth
end, "Initiate Guild of Earth")

RegisterEvent(24, "Initiate Guild of Earth", nil, "Initiate Guild of Earth")

RegisterEvent(25, "Initiate Guild of Light", function()
    evt.EnterHouse(173) -- Initiate Guild of Light
end, "Initiate Guild of Light")

RegisterEvent(26, "Initiate Guild of Light", nil, "Initiate Guild of Light")

RegisterEvent(27, "Adept Guild of the Self", function()
    evt.EnterHouse(190) -- Adept Guild of the Self
end, "Adept Guild of the Self")

RegisterEvent(28, "Legacy event 28", nil)

RegisterEvent(29, "Berserkers' Fury", function()
    evt.EnterHouse(199) -- Berserkers' Fury
end, "Berserkers' Fury")

RegisterEvent(30, "Berserkers' Fury", nil, "Berserkers' Fury")

RegisterEvent(31, "Protection Services", function()
    evt.EnterHouse(194) -- Protection Services
end, "Protection Services")

RegisterEvent(32, "Barracuda", function()
    evt.EnterHouse(502) -- Barracuda
end, "Barracuda")

RegisterEvent(33, "Circus", function()
    evt.EnterHouse(1595) -- Circus
end, "Circus")

RegisterEvent(34, "Throne Room", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 83, 1, "0.")
    evt.EnterHouse(226) -- Throne Room
end, "Throne Room")

RegisterEvent(35, "Castle Stone", function()
    evt.StatusText("Castle Stone")
end, "Castle Stone")

RegisterEvent(36, "Silver Cove", function()
    evt.StatusText("Silver Cove")
end, "Silver Cove")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1223) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1238) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1253) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1268) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1283) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1298) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1311) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1323) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1334) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1346) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1358) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1370) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1381) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1392) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1402) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1411) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1420) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1428) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1437) -- House
end, "House")

RegisterEvent(69, "House", function()
    evt.EnterHouse(1446) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1455) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1462) -- House
end, "House")

RegisterEvent(72, "House", function()
    evt.EnterHouse(1468) -- House
end, "House")

RegisterEvent(73, "House", function()
    evt.EnterHouse(1473) -- House
end, "House")

RegisterEvent(74, "House", function()
    evt.EnterHouse(1478) -- House
end, "House")

RegisterEvent(75, "House", function()
    evt.EnterHouse(1483) -- House
end, "House")

RegisterEvent(76, "House", function()
    evt.EnterHouse(1488) -- House
end, "House")

RegisterEvent(77, "House", function()
    evt.EnterHouse(1493) -- House
end, "House")

RegisterEvent(78, "House", function()
    evt.EnterHouse(1498) -- House
end, "House")

RegisterEvent(79, "House", function()
    evt.EnterHouse(1503) -- House
end, "House")

RegisterEvent(80, "House", function()
    evt.EnterHouse(1507) -- House
end, "House")

RegisterEvent(81, "House", function()
    evt.EnterHouse(1511) -- House
end, "House")

RegisterEvent(82, "House", function()
    evt.EnterHouse(1514) -- House
end, "House")

RegisterEvent(83, "House", function()
    evt.EnterHouse(1517) -- House
end, "House")

RegisterEvent(84, "House", function()
    evt.EnterHouse(1520) -- House
end, "House")

RegisterEvent(85, "House", function()
    evt.EnterHouse(1523) -- House
end, "House")

RegisterEvent(86, "House", function()
    evt.EnterHouse(1525) -- House
end, "House")

RegisterEvent(87, "House", function()
    evt.EnterHouse(1527) -- House
end, "House")

RegisterEvent(88, "House", function()
    evt.EnterHouse(1529) -- House
end, "House")

RegisterEvent(89, "House", function()
    evt.EnterHouse(1531) -- House
end, "House")

RegisterEvent(90, "House", function()
    evt.EnterHouse(1533) -- House
end, "House")

RegisterEvent(91, "House", function()
    evt.EnterHouse(1535) -- House
end, "House")

RegisterEvent(92, "House", function()
    evt.EnterHouse(1537) -- House
end, "House")

RegisterEvent(93, "House", function()
    evt.EnterHouse(1539) -- House
end, "House")

RegisterEvent(94, "House", function()
    evt.EnterHouse(1541) -- House
end, "House")

RegisterEvent(95, "House", function()
    evt.EnterHouse(1543) -- House
end, "House")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(101, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(102, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(150, "Legacy event 150", function()
    evt.MoveToMap(-127, 4190, 1, 1536, 0, 0, 185, 1, "6d12.blv")
end)

RegisterEvent(151, "Legacy event 151", function()
    evt.MoveToMap(-128, -3968, 1, 512, 0, 0, 186, 1, "6d13.blv")
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.MoveToMap(-4724, 1494, 127, 1920, 0, 0, 189, 1, "6d16.blv")
end)

RegisterEvent(161, "Drink from Well.", function()
    if not IsAtLeast(IntellectBonus, 20) then
        SetValue(IntellectBonus, 20)
        SetValue(PersonalityBonus, 20)
        evt.StatusText("+20 Intellect and Personality temporary.")
        SetAutonote(413) -- 20 Points of temporary intellect and personality from the fountain in the north side of Silver Cove.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(162, "Drink from Fountain", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Refreshing!")
        SetAutonote(414) -- 25 Spell points restored by the fountain outside of Town Hall in Silver Cove.
        return
    end
    SubtractValue(MapVar(2), 1)
    AddValue(CurrentSpellPoints, 25)
    evt.StatusText("+25 Spell points restored.")
    SetAutonote(414) -- 25 Spell points restored by the fountain outside of Town Hall in Silver Cove.
end, "Drink from Fountain")

RegisterEvent(163, "Drink from Fountain", function()
    SetValue(DiseasedGreen, 0)
    evt.StatusText("WOW!")
end, "Drink from Fountain")

RegisterEvent(164, "Drink from Fountain", function()
    if not IsAtLeast(BaseAccuracy, 15) then
        if not IsAtLeast(MapVar(3), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(3), 1)
        AddValue(BaseAccuracy, 2)
        evt.StatusText("+2 Accuracy permanent.")
        SetAutonote(415) -- 2 Points of permanent accuracy from the north fountain west of Silver Cove.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(165, "Drink from Fountain", function()
    if not IsAtLeast(BaseSpeed, 15) then
        if not IsAtLeast(MapVar(4), 1) then
            evt.StatusText("Refreshing!")
            return
        end
        SubtractValue(MapVar(4), 1)
        AddValue(BaseSpeed, 2)
        evt.StatusText("+2 Speed permanent.")
        SetAutonote(416) -- 2 Points of permanent speed from the south fountain west of Silver Cove.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(209, "Legacy event 209", function()
    if IsQBitSet(QBit(1182)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, 11032, -8940, 2830, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(210, "Legacy event 210", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1182)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1182)) -- NPC
        evt.ShowMovie("Name", true)
    else
        return
    end
end)

RegisterEvent(211, "Circle of Stones", function()
    if IsQBitSet(QBit(1197)) then return end -- NPC
    if IsAtLeast(DayOfYear, 76) then
        if not IsQBitSet(QBit(1142)) then return end -- Visit the Altar of the Sun in the circle of stones north of Silver Cove on an equinox or solstice (HINT: March 20th is an equinox). - NPC
        evt.SpeakNPC(1090) -- Loretta Fleise
        return
    elseif IsAtLeast(DayOfYear, 161) then
        if not IsQBitSet(QBit(1142)) then return end -- Visit the Altar of the Sun in the circle of stones north of Silver Cove on an equinox or solstice (HINT: March 20th is an equinox). - NPC
        evt.SpeakNPC(1090) -- Loretta Fleise
        return
    elseif IsAtLeast(DayOfYear, 247) then
        if not IsQBitSet(QBit(1142)) then return end -- Visit the Altar of the Sun in the circle of stones north of Silver Cove on an equinox or solstice (HINT: March 20th is an equinox). - NPC
        evt.SpeakNPC(1090) -- Loretta Fleise
        return
    elseif IsAtLeast(DayOfYear, 329) then
        if not IsQBitSet(QBit(1142)) then return end -- Visit the Altar of the Sun in the circle of stones north of Silver Cove on an equinox or solstice (HINT: March 20th is an equinox). - NPC
        evt.SpeakNPC(1090) -- Loretta Fleise
        return
    else
        return
    end
end, "Circle of Stones")

RegisterEvent(212, "Legacy event 212", function()
    evt.MoveToMap(-12344, 17112, 1, 1536, 0, 0, 0, 0)
end)

RegisterEvent(213, "Legacy event 213", function()
    evt.MoveToMap(-9400, 17184, 1, 1536, 0, 0, 0, 0)
end)

RegisterEvent(214, "Legacy event 214", function()
    evt.MoveToMap(-11512, 19368, 1, 1536, 0, 0, 0, 0)
end)

RegisterEvent(215, "Legacy event 215", function()
    evt.MoveToMap(-9192, 21936, 160, 1536, 0, 0, 0, 0)
end)

RegisterEvent(220, "Legacy event 220", function(continueStep)
    local function Step_0()
        if IsQBitSet(QBit(1334)) then return 8 end -- NPC
        return 1
    end
    local function Step_1()
        if IsAtLeast(ActualMight, 60) then return 5 end
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
        SetQBit(QBit(1334)) -- NPC
        return 6
    end
    local function Step_6()
        evt.GiveItem(5, 23, 1606) -- Conqueror Sword
        return 7
    end
    local function Step_7()
        evt.SetSprite(359, 1, "swrdstx")
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_10()
        if IsQBitSet(QBit(1334)) then return 7 end -- NPC
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

RegisterEvent(221, "Legacy event 221", function(continueStep)
    local function Step_0()
        if IsQBitSet(QBit(1335)) then return 8 end -- NPC
        return 1
    end
    local function Step_1()
        if IsAtLeast(ActualMight, 60) then return 5 end
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
        SetQBit(QBit(1335)) -- NPC
        return 6
    end
    local function Step_6()
        evt.GiveItem(5, 23, 1607) -- Lionheart Sword
        return 7
    end
    local function Step_7()
        evt.SetSprite(360, 1, "swrdstx")
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_10()
        if IsQBitSet(QBit(1335)) then return 7 end -- NPC
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

RegisterEvent(222, "Legacy event 222", function(continueStep)
    local function Step_0()
        if IsQBitSet(QBit(1336)) then return 8 end -- NPC
        return 1
    end
    local function Step_1()
        if IsAtLeast(ActualMight, 100) then return 5 end
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
        SetQBit(QBit(1336)) -- NPC
        return 6
    end
    local function Step_6()
        evt.GiveItem(6, 23, 1610) -- Vanquisher Sword
        return 7
    end
    local function Step_7()
        evt.SetSprite(361, 1, "swrdstx")
        return 8
    end
    local function Step_8()
        return nil
    end
    local function Step_10()
        if IsQBitSet(QBit(1336)) then return 7 end -- NPC
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

RegisterEvent(223, "Legacy event 223", function()
    if IsQBitSet(QBit(1203)) then return end -- NPC
    SetQBit(QBit(1203)) -- NPC
end)

RegisterEvent(224, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            nnaifnt_ieif_tu_")
    SetQBit(QBit(1393)) -- NPC
    SetAutonote(451) -- Obelisk Message # 10: nnaifnt_ieif_tu_
end, "Obelisk")

RegisterEvent(226, "Legacy event 226", function()
    if IsQBitSet(QBit(1182)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Personality", function()
    if not IsAtLeast(MonthIs, 2) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1233)) then -- NPC
            SetQBit(QBit(1233)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BasePersonality, 10)
            evt.StatusText("+10 Personality permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BasePersonality, 3)
        evt.StatusText("+3 Personality permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Personality")

RegisterEvent(65535, "", function()
    return evt.map[220](10)
end)

RegisterEvent(65534, "", function()
    return evt.map[221](10)
end)

RegisterEvent(65533, "", function()
    return evt.map[222](10)
end)

