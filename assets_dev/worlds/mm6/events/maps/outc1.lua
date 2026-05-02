-- Frozen Highlands
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {211, 214},
    onLeave = {},
    openedChestIds = {
    [85] = {1},
    [86] = {2},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    { eventId = 209, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterEvent(2, "Shrine of Endurance", function()
    evt.EnterHouse(33) -- Mystical Mayhem
end, "Shrine of Endurance")

RegisterEvent(3, "Shrine of Endurance", nil, "Shrine of Endurance")

RegisterEvent(4, "Mystic Medicine", function()
    evt.EnterHouse(74) -- Mystic Medicine
end, "Mystic Medicine")

RegisterEvent(5, "Mystic Medicine", nil, "Mystic Medicine")

RegisterEvent(6, "Placeholder", function()
    evt.EnterHouse(103) -- Placeholder
end, "Placeholder")

RegisterEvent(7, "Placeholder", nil, "Placeholder")

RegisterEvent(8, "Legacy event 8", function()
    evt.EnterHouse(1274)
end)

RegisterEvent(9, "Legacy event 9", nil)

RegisterEvent(10, "House Farswell", function()
    evt.EnterHouse(329) -- House Farswell
end, "House Farswell")

RegisterEvent(11, "Legacy event 11", function()
    evt.EnterHouse(1592)
end)

RegisterEvent(12, "Legacy event 12", nil)

RegisterEvent(13, "Hostel", function()
    evt.EnterHouse(276) -- Hostel
end, "Hostel")

RegisterEvent(14, "Hostel", nil, "Hostel")

RegisterEvent(15, "Stonecleaver Hall", function()
    evt.EnterHouse(275) -- Stonecleaver Hall
end, "Stonecleaver Hall")

RegisterEvent(16, "Stonecleaver Hall", nil, "Stonecleaver Hall")

RegisterEvent(17, "Guild of Bounty Hunters", function()
    evt.EnterHouse(301) -- Guild of Bounty Hunters
end, "Guild of Bounty Hunters")

RegisterEvent(18, "Guild of Bounty Hunters", nil, "Guild of Bounty Hunters")

RegisterEvent(19, "Sandro/Thant's Throne Room", function()
    evt.EnterHouse(180) -- Sandro/Thant's Throne Room
end, "Sandro/Thant's Throne Room")

RegisterEvent(20, "Sandro/Thant's Throne Room", nil, "Sandro/Thant's Throne Room")

RegisterEvent(21, "Legacy event 21", function()
    evt.EnterHouse(1230)
end)

RegisterEvent(22, "Legacy event 22", nil)

RegisterEvent(23, "Chain of Fire", function()
    evt.EnterHouse(201) -- Chain of Fire
end, "Chain of Fire")

RegisterEvent(24, "Chain of Fire", nil, "Chain of Fire")

RegisterEvent(25, "Smuggler's Cove", function()
    evt.EnterHouse(193) -- Smuggler's Cove
end, "Smuggler's Cove")

RegisterEvent(26, "Smuggler's Cove", nil, "Smuggler's Cove")

RegisterEvent(27, "+5 Endurance permanent.", function()
    evt.EnterHouse(30) -- Needful Things
end, "+5 Endurance permanent.")

RegisterEvent(28, "+5 Endurance permanent.", nil, "+5 Endurance permanent.")

RegisterEvent(29, "Placeholder", function()
    evt.EnterHouse(70) -- Placeholder
end, "Placeholder")

RegisterEvent(30, "Placeholder", nil, "Placeholder")

RegisterEvent(31, "Empty House", function()
    evt.EnterHouse(476) -- Empty House
end, "Empty House")

RegisterEvent(32, "Empty House", nil, "Empty House")

RegisterEvent(33, "Rohtnax's House", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 82, 1, "0.")
    evt.EnterHouse(225) -- Rohtnax's House
end, "Rohtnax's House")

RegisterEvent(34, "Thadin's House", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 84, 1, "0.")
    evt.EnterHouse(227) -- Thadin's House
end, "Thadin's House")

RegisterEvent(35, "Castle Stromgard", function()
    evt.StatusText("Castle Stromgard")
end, "Castle Stromgard")

RegisterEvent(36, "White Cap", function()
    evt.StatusText("White Cap")
end, "White Cap")

RegisterEvent(37, "Rockham/Free Haven", function()
    evt.StatusText("Rockham/Free Haven")
end, "Rockham/Free Haven")

RegisterEvent(50, "Shrine of Endurance", function()
    evt.EnterHouse(1220)
end, "Shrine of Endurance")

RegisterEvent(51, "You pray at the shrine.", function()
    evt.EnterHouse(1235)
end, "You pray at the shrine.")

RegisterEvent(52, "+10 Endurance permanent", function()
    evt.EnterHouse(1250)
end, "+10 Endurance permanent")

RegisterEvent(53, "+3 Endurance permanent", function()
    evt.EnterHouse(1265)
end, "+3 Endurance permanent")

RegisterEvent(54, "\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _ay,enis_nn_ans.\"", function()
    evt.EnterHouse(1280)
end, "\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _ay,enis_nn_ans.\"")

RegisterEvent(55, "Obelisk", function()
    evt.EnterHouse(1295)
end, "Obelisk")

RegisterEvent(56, "Castle Stromgard", function()
    evt.EnterHouse(1308)
end, "Castle Stromgard")

RegisterEvent(57, "White Cap", function()
    evt.EnterHouse(1320)
end, "White Cap")

RegisterEvent(58, "Rockham/Free Haven", function()
    evt.EnterHouse(1331)
end, "Rockham/Free Haven")

RegisterEvent(59, "Legacy event 59", function()
    evt.EnterHouse(1343)
end)

RegisterEvent(60, "Legacy event 60", function()
    evt.EnterHouse(1355)
end)

RegisterEvent(61, "Legacy event 61", function()
    evt.EnterHouse(1367)
end)

RegisterEvent(62, "Legacy event 62", function()
    evt.EnterHouse(1378)
end)

RegisterEvent(63, "Legacy event 63", function()
    evt.EnterHouse(1389)
end)

RegisterEvent(64, "Legacy event 64", function()
    evt.EnterHouse(1399)
end)

RegisterEvent(65, "Legacy event 65", function()
    evt.EnterHouse(1414)
end)

RegisterEvent(66, "Legacy event 66", function()
    evt.EnterHouse(1423)
end)

RegisterEvent(67, "Legacy event 67", function()
    evt.EnterHouse(1432)
end)

RegisterEvent(68, "Legacy event 68", function()
    evt.EnterHouse(1441)
end)

RegisterEvent(69, "Legacy event 69", function()
    evt.EnterHouse(1450)
end)

RegisterEvent(70, "Legacy event 70", function()
    evt.EnterHouse(1458)
end)

RegisterEvent(71, "Legacy event 71", function()
    evt.EnterHouse(1465)
end)

RegisterEvent(72, "Legacy event 72", function()
    evt.EnterHouse(1470)
end)

RegisterEvent(73, "Legacy event 73", function()
    evt.EnterHouse(1475)
end)

RegisterEvent(74, "Legacy event 74", function()
    evt.EnterHouse(1480)
end)

RegisterEvent(75, "Legacy event 75", function()
    evt.EnterHouse(1485)
end)

RegisterEvent(76, "Legacy event 76", function()
    evt.EnterHouse(1490)
end)

RegisterEvent(77, "Legacy event 77", function()
    evt.EnterHouse(1495)
end)

RegisterEvent(78, "Legacy event 78", function()
    evt.EnterHouse(1500)
end)

RegisterEvent(79, "Drink from Well.", function()
    evt.EnterHouse(1504)
end, "Drink from Well.")

RegisterEvent(80, "Look Out!", function()
    evt.EnterHouse(1508)
end, "Look Out!")

RegisterEvent(81, "Drink from Fountain", function()
    evt.EnterHouse(1512)
end, "Drink from Fountain")

RegisterEvent(82, "+20 Accuracy and Speed temporary.", function()
    evt.EnterHouse(1515)
end, "+20 Accuracy and Speed temporary.")

RegisterEvent(83, "+20 Armor class temporary.", function()
    evt.EnterHouse(1518)
end, "+20 Armor class temporary.")

RegisterEvent(84, "+10 Level temporary.", function()
    evt.EnterHouse(1521)
end, "+10 Level temporary.")

RegisterEvent(85, "Legacy event 85", function()
    evt.OpenChest(1)
end)

RegisterEvent(86, "Legacy event 86", function()
    evt.OpenChest(2)
end)

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(1408, -1664, 1, 1024, 0, 0, 180, 1, "6d08.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    evt.MoveToMap(-495, -219, 1, 512, 0, 0, 188, 1, "6d15.blv")
end)

RegisterEvent(100, "Drink from Well.", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.SummonMonsters(3, 3, 2, 15024, -4720, 96, 0, 0) -- encounter slot 3 "BArcher" tier C, count 2, pos=(15024, -4720, 96), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, 16960, -3936, 96, 0, 0) -- encounter slot 3 "BArcher" tier C, count 2, pos=(16960, -3936, 96), actor group 0, no unique actor name
        evt.SummonMonsters(3, 3, 2, 16320, -1648, 224, 0, 0) -- encounter slot 3 "BArcher" tier C, count 2, pos=(16320, -1648, 224), actor group 0, no unique actor name
        SetValue(MapVar(2), 1)
        evt.StatusText("Look Out!")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(101, "Drink from Well.", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.SummonMonsters(2, 3, 2, -5136, 15968, 96, 0, 0) -- encounter slot 2 "Barbarian" tier C, count 2, pos=(-5136, 15968, 96), actor group 0, no unique actor name
        evt.SummonMonsters(2, 3, 2, -6912, 13952, 96, 0, 0) -- encounter slot 2 "Barbarian" tier C, count 2, pos=(-6912, 13952, 96), actor group 0, no unique actor name
        evt.SummonMonsters(2, 3, 2, -5152, 13648, 96, 0, 0) -- encounter slot 2 "Barbarian" tier C, count 2, pos=(-5152, 13648, 96), actor group 0, no unique actor name
        SetValue(MapVar(3), 1)
        evt.StatusText("Look Out!")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(102, "Drink from Fountain", function()
    if not IsAtLeast(AccuracyBonus, 20) then
        SetValue(AccuracyBonus, 20)
        SetValue(SpeedBonus, 20)
        evt.StatusText("+20 Accuracy and Speed temporary.")
        SetAutonote(420) -- 20 Points of temporary speed and accuracy from the west fountain in Icewind Lake.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(103, "Drink from Fountain", function()
    if not IsAtLeast(ArmorClassBonus, 20) then
        SetValue(ArmorClassBonus, 20)
        evt.StatusText("+20 Armor class temporary.")
        SetAutonote(421) -- 20 Points of temporary armor class from the east fountain in Icewind Lake.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(104, "Drink from Fountain", function()
    if not IsAtLeast(LevelBonus, 10) then
        SetValue(LevelBonus, 10)
        evt.StatusText("+10 Level temporary.")
        SetAutonote(422) -- 10 Temporary levels from the fountain northeast of Castle Stone.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(105, "Drink from Fountain", function()
    if not IsAtLeast(MightBonus, 30) then
        SetValue(MightBonus, 30)
        evt.StatusText("+30 Might temporary.")
        SetAutonote(423) -- 30 Points of temporary might from the fountain west of Castle Stromgard.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain")

RegisterEvent(106, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(61)) then
        SetPlayerBit(PlayerBit(61))
        AddValue(BaseMight, 5)
        SetValue(Eradicated, 0)
        evt.StatusText("+5 Might permanent.")
        SetAutonote(424) -- 5 Points of permanent might from the north fountain east of White Cap Temple.
        return
    end
    SetValue(Eradicated, 0)
end, "Drink from Fountain")

RegisterEvent(107, "Drink from Fountain", function()
    if not IsPlayerBitSet(PlayerBit(62)) then
        SetPlayerBit(PlayerBit(62))
        AddValue(BaseEndurance, 5)
        SetValue(Eradicated, 0)
        evt.StatusText("+5 Endurance permanent.")
        SetAutonote(425) -- 5 Points of permanent endurance from the south fountain east of White Cap Temple.
        return
    end
    SetValue(Eradicated, 0)
end, "Drink from Fountain")

RegisterEvent(209, "Legacy event 209", function()
    if IsQBitSet(QBit(1185)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, -6606, 15546, 2550, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(210, "Legacy event 210", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1185)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1185)) -- NPC
        evt.ShowMovie("t1swbu", true)
    else
        return
    end
end)

RegisterEvent(211, "Legacy event 211", function()
    if IsQBitSet(QBit(1252)) then return end -- NPC
    evt.SetSnow(0, 1)
end)

RegisterEvent(213, "Obelisk", function()
    evt.SimpleMessage("\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _ay,enis_nn_ans.\"")
    SetQBit(QBit(1390)) -- NPC
    SetAutonote(448) -- Obelisk Message # 7: _ay,enis_nn_ans.
end, "Obelisk")

RegisterEvent(214, "Legacy event 214", function()
    if IsQBitSet(QBit(1185)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Endurance", function()
    if not IsAtLeast(MonthIs, 3) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1234)) then -- NPC
            SetQBit(QBit(1234)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseEndurance, 10)
            evt.StatusText("+10 Endurance permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseEndurance, 3)
        evt.StatusText("+3 Endurance permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Endurance")

