-- Silver Cove
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {220, 221, 222, 223, 226},
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
    evt.EnterHouse(31) -- Arcane Items
end, "+2 Speed permanent.")

RegisterEvent(3, "+2 Speed permanent.", nil, "+2 Speed permanent.")

RegisterEvent(4, "Placeholder", function()
    evt.EnterHouse(69) -- Placeholder
end, "Placeholder")

RegisterEvent(5, "Placeholder", nil, "Placeholder")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(100) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1245)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "Empty House", function()
    evt.EnterHouse(475) -- Empty House
end, "Empty House")

RegisterEvent(11, "Empty House", nil, "Empty House")

RegisterEvent(12, "Backdoor of Abandoned Temple", function()
    evt.EnterHouse(500) -- Backdoor of Abandoned Temple
end, "Backdoor of Abandoned Temple")

RegisterEvent(13, "Stone's Hovel", function()
    evt.EnterHouse(331) -- Stone's Hovel
end, "Stone's Hovel")

RegisterEvent(14, "Legacy event 14", function()
    evt.EnterHouse(1585)
end)

RegisterEvent(15, "Legacy event 15", nil)

RegisterEvent(16, "Small Sub Pen", function()
    evt.EnterHouse(211) -- Small Sub Pen
end, "Small Sub Pen")

RegisterEvent(17, "Temper Hall", function()
    evt.EnterHouse(268) -- Temper Hall
end, "Temper Hall")

RegisterEvent(18, "Temper Hall", nil, "Temper Hall")

RegisterEvent(19, "Putnam's Home", function()
    evt.EnterHouse(269) -- Putnam's Home
end, "Putnam's Home")

RegisterEvent(20, "Putnam's Home", nil, "Putnam's Home")

RegisterEvent(21, "Sablewood Hall", function()
    evt.EnterHouse(299) -- Sablewood Hall
end, "Sablewood Hall")

RegisterEvent(22, "Sablewood Hall", nil, "Sablewood Hall")

RegisterEvent(23, "Placeholder", function()
    evt.EnterHouse(150) -- Placeholder
end, "Placeholder")

RegisterEvent(24, "Placeholder", nil, "Placeholder")

RegisterEvent(25, "Clan Leader's Hall", function()
    evt.EnterHouse(173) -- Clan Leader's Hall
end, "Clan Leader's Hall")

RegisterEvent(26, "Clan Leader's Hall", nil, "Clan Leader's Hall")

RegisterEvent(27, "The Adventurer's Inn", function()
    evt.EnterHouse(190) -- The Adventurer's Inn
end, "The Adventurer's Inn")

RegisterEvent(28, "Legacy event 28", nil)

RegisterEvent(29, "Troll Tomb", function()
    evt.EnterHouse(199) -- Troll Tomb
end, "Troll Tomb")

RegisterEvent(30, "Troll Tomb", nil, "Troll Tomb")

RegisterEvent(31, "Dire Wolf Den", function()
    evt.EnterHouse(194) -- Dire Wolf Den
end, "Dire Wolf Den")

RegisterEvent(32, "House 502", function()
    evt.EnterHouse(502) -- House 502
end, "House 502")

RegisterEvent(33, "Legacy event 33", function()
    evt.EnterHouse(1595)
end)

RegisterEvent(34, "Tisk's Hut", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 83, 1, "0.")
    evt.EnterHouse(226) -- Tisk's Hut
end, "Tisk's Hut")

RegisterEvent(35, "Castle Stone", function()
    evt.StatusText("Castle Stone")
end, "Castle Stone")

RegisterEvent(36, "Silver Cove", function()
    evt.StatusText("Silver Cove")
end, "Silver Cove")

RegisterEvent(50, "Legacy event 50", function()
    evt.EnterHouse(1223)
end)

RegisterEvent(51, "Legacy event 51", function()
    evt.EnterHouse(1238)
end)

RegisterEvent(52, "Legacy event 52", function()
    evt.EnterHouse(1253)
end)

RegisterEvent(53, "Legacy event 53", function()
    evt.EnterHouse(1268)
end)

RegisterEvent(54, "Legacy event 54", function()
    evt.EnterHouse(1283)
end)

RegisterEvent(55, "Legacy event 55", function()
    evt.EnterHouse(1298)
end)

RegisterEvent(56, "Legacy event 56", function()
    evt.EnterHouse(1311)
end)

RegisterEvent(57, "Legacy event 57", function()
    evt.EnterHouse(1323)
end)

RegisterEvent(58, "Legacy event 58", function()
    evt.EnterHouse(1334)
end)

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1346)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1358)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1370)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1381)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1392)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1402)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1411)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.EnterHouse(1420)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.EnterHouse(1428)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.EnterHouse(1437)
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.EnterHouse(1446)
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.EnterHouse(1455)
end)

RegisterEvent(71, "Legacy event 71", function()
    evt.EnterHouse(1462)
end)

RegisterEvent(72, "Legacy event 72", function()
    evt.EnterHouse(1468)
end)

RegisterEvent(73, "Legacy event 73", function()
    evt.EnterHouse(1473)
end)

RegisterEvent(74, "Legacy event 74", function()
    evt.EnterHouse(1478)
end)

RegisterEvent(75, "Legacy event 75", function()
    evt.EnterHouse(1483)
end)

RegisterEvent(76, "Legacy event 76", function()
    evt.EnterHouse(1488)
end)

RegisterEvent(77, "Legacy event 77", function()
    evt.EnterHouse(1493)
end)

RegisterEvent(78, "Legacy event 78", function()
    evt.EnterHouse(1498)
end)

RegisterEvent(79, "Legacy event 79", function()
    evt.EnterHouse(1503)
end)

RegisterEvent(80, "Legacy event 80", function()
    evt.EnterHouse(1507)
end)

RegisterEvent(81, "Legacy event 81", function()
    evt.EnterHouse(1511)
end)

RegisterEvent(82, "Legacy event 82", function()
    evt.EnterHouse(1514)
end)

RegisterEvent(83, "Legacy event 83", function()
    evt.EnterHouse(1517)
end)

RegisterEvent(84, "Legacy event 84", function()
    evt.EnterHouse(1520)
end)

RegisterEvent(85, "Legacy event 85", function()
    evt.EnterHouse(1523)
end)

RegisterEvent(86, "Legacy event 86", function()
    evt.EnterHouse(1525)
end)

RegisterEvent(87, "Legacy event 87", function()
    evt.EnterHouse(1527)
end)

RegisterEvent(88, "Legacy event 88", function()
    evt.EnterHouse(1529)
end)

RegisterEvent(89, "Legacy event 89", function()
    evt.EnterHouse(1531)
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.EnterHouse(1533)
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.EnterHouse(1535)
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.EnterHouse(1537)
end)

RegisterEvent(93, "Legacy event 93", function()
    evt.EnterHouse(1539)
end)

RegisterEvent(94, "Legacy event 94", function()
    evt.EnterHouse(1541)
end)

RegisterEvent(95, "Legacy event 95", function()
    evt.EnterHouse(1543)
end)

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

RegisterEvent(220, "Legacy event 220", function()
    if IsQBitSet(QBit(1334)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 60) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1334)) -- NPC
    evt.GiveItem(5, 23, 1606) -- Conqueror Sword
    evt.SetSprite(359, 1, "swrdstx")
end)

RegisterEvent(221, "Legacy event 221", function()
    if IsQBitSet(QBit(1335)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 60) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1335)) -- NPC
    evt.GiveItem(5, 23, 1607) -- Lionheart Sword
    evt.SetSprite(360, 1, "swrdstx")
end)

RegisterEvent(222, "Legacy event 222", function()
    if IsQBitSet(QBit(1336)) then -- NPC
        return
    end
    if not IsAtLeast(ActualMight, 100) then
        evt.FaceExpression(51)
        evt.StatusText("The Sword won't budge!")
        return
    end
    SetQBit(QBit(1336)) -- NPC
    evt.GiveItem(6, 23, 1610) -- Vanquisher Sword
    evt.SetSprite(361, 1, "swrdstx")
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

