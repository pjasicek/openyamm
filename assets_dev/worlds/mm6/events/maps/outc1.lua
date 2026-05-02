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
    evt.EnterHouse(33) -- Mark and Missile
end, "Shrine of Endurance")

RegisterEvent(3, "Shrine of Endurance", nil, "Shrine of Endurance")

RegisterEvent(4, "Silver Lining Armor & Shield", function()
    evt.EnterHouse(74) -- Silver Lining Armor & Shield
end, "Silver Lining Armor & Shield")

RegisterEvent(5, "Silver Lining Armor & Shield", nil, "Silver Lining Armor & Shield")

RegisterEvent(6, "Apples, Thorns, and Potions", function()
    evt.EnterHouse(103) -- Apples, Thorns, and Potions
end, "Apples, Thorns, and Potions")

RegisterEvent(7, "Apples, Thorns, and Potions", nil, "Apples, Thorns, and Potions")

RegisterEvent(8, "General Store", function()
    evt.EnterHouse(1274) -- General Store
end, "General Store")

RegisterEvent(9, "General Store", nil, "General Store")

RegisterEvent(10, "White Cap Temple", function()
    evt.EnterHouse(329) -- White Cap Temple
end, "White Cap Temple")

RegisterEvent(11, "Riverside Academy", function()
    evt.EnterHouse(1592) -- Riverside Academy
end, "Riverside Academy")

RegisterEvent(12, "Riverside Academy", nil, "Riverside Academy")

RegisterEvent(13, "The Frosty Tankard", function()
    evt.EnterHouse(276) -- The Frosty Tankard
end, "The Frosty Tankard")

RegisterEvent(14, "The Frosty Tankard", nil, "The Frosty Tankard")

RegisterEvent(15, "Rime and Reason", function()
    evt.EnterHouse(275) -- Rime and Reason
end, "Rime and Reason")

RegisterEvent(16, "Rime and Reason", nil, "Rime and Reason")

RegisterEvent(17, "Secure Trust", function()
    evt.EnterHouse(301) -- Secure Trust
end, "Secure Trust")

RegisterEvent(18, "Secure Trust", nil, "Secure Trust")

RegisterEvent(19, "Initiate Guild of Dark", function()
    evt.EnterHouse(180) -- Initiate Guild of Dark
end, "Initiate Guild of Dark")

RegisterEvent(20, "Initiate Guild of Dark", nil, "Initiate Guild of Dark")

RegisterEvent(21, "Adept Guild of the Elements", function()
    evt.EnterHouse(1230) -- Adept Guild of the Elements
end, "Adept Guild of the Elements")

RegisterEvent(22, "Adept Guild of the Elements", nil, "Adept Guild of the Elements")

RegisterEvent(23, "Blades' End", function()
    evt.EnterHouse(201) -- Blades' End
end, "Blades' End")

RegisterEvent(24, "Blades' End", nil, "Blades' End")

RegisterEvent(25, "Protection Services", function()
    evt.EnterHouse(193) -- Protection Services
end, "Protection Services")

RegisterEvent(26, "Protection Services", nil, "Protection Services")

RegisterEvent(27, "+5 Endurance permanent.", function()
    evt.EnterHouse(30) -- Haft and Handle Pole arms
end, "+5 Endurance permanent.")

RegisterEvent(28, "+5 Endurance permanent.", nil, "+5 Endurance permanent.")

RegisterEvent(29, "Quality Armor", function()
    evt.EnterHouse(70) -- Quality Armor
end, "Quality Armor")

RegisterEvent(30, "Quality Armor", nil, "Quality Armor")

RegisterEvent(31, "White Cap Transport Co.", function()
    evt.EnterHouse(476) -- White Cap Transport Co.
end, "White Cap Transport Co.")

RegisterEvent(32, "White Cap Transport Co.", nil, "White Cap Transport Co.")

RegisterEvent(33, "Throne Room", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 82, 1, "0.")
    evt.EnterHouse(225) -- Throne Room
end, "Throne Room")

RegisterEvent(34, "Throne Room", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 84, 1, "0.")
    evt.EnterHouse(227) -- Throne Room
end, "Throne Room")

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
    evt.EnterHouse(1220) -- House
end, "Shrine of Endurance")

RegisterEvent(51, "You pray at the shrine.", function()
    evt.EnterHouse(1235) -- House
end, "You pray at the shrine.")

RegisterEvent(52, "+10 Endurance permanent", function()
    evt.EnterHouse(1250) -- House
end, "+10 Endurance permanent")

RegisterEvent(53, "+3 Endurance permanent", function()
    evt.EnterHouse(1265) -- House
end, "+3 Endurance permanent")

RegisterEvent(54, "\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _ay,enis_nn_ans.\"", function()
    evt.EnterHouse(1280) -- House
end, "\"The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            _ay,enis_nn_ans.\"")

RegisterEvent(55, "Obelisk", function()
    evt.EnterHouse(1295) -- House
end, "Obelisk")

RegisterEvent(56, "Castle Stromgard", function()
    evt.EnterHouse(1308) -- House
end, "Castle Stromgard")

RegisterEvent(57, "White Cap", function()
    evt.EnterHouse(1320) -- House
end, "White Cap")

RegisterEvent(58, "Rockham/Free Haven", function()
    evt.EnterHouse(1331) -- House
end, "Rockham/Free Haven")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1343) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1355) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1367) -- House
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1378) -- House
end, "House")

RegisterEvent(63, "House", function()
    evt.EnterHouse(1389) -- House
end, "House")

RegisterEvent(64, "House", function()
    evt.EnterHouse(1399) -- House
end, "House")

RegisterEvent(65, "House", function()
    evt.EnterHouse(1414) -- House
end, "House")

RegisterEvent(66, "House", function()
    evt.EnterHouse(1423) -- House
end, "House")

RegisterEvent(67, "House", function()
    evt.EnterHouse(1432) -- House
end, "House")

RegisterEvent(68, "House", function()
    evt.EnterHouse(1441) -- House
end, "House")

RegisterEvent(69, "House", function()
    evt.EnterHouse(1450) -- House
end, "House")

RegisterEvent(70, "House", function()
    evt.EnterHouse(1458) -- House
end, "House")

RegisterEvent(71, "House", function()
    evt.EnterHouse(1465) -- House
end, "House")

RegisterEvent(72, "House", function()
    evt.EnterHouse(1470) -- House
end, "House")

RegisterEvent(73, "House", function()
    evt.EnterHouse(1475) -- House
end, "House")

RegisterEvent(74, "House", function()
    evt.EnterHouse(1480) -- House
end, "House")

RegisterEvent(75, "House", function()
    evt.EnterHouse(1485) -- House
end, "House")

RegisterEvent(76, "House", function()
    evt.EnterHouse(1490) -- House
end, "House")

RegisterEvent(77, "House", function()
    evt.EnterHouse(1495) -- House
end, "House")

RegisterEvent(78, "Legacy event 78", function()
    evt.EnterHouse(1500) -- House
end)

RegisterEvent(79, "Drink from Well.", function()
    evt.EnterHouse(1504) -- House
end, "Drink from Well.")

RegisterEvent(80, "Look Out!", function()
    evt.EnterHouse(1508) -- House
end, "Look Out!")

RegisterEvent(81, "Drink from Fountain", function()
    evt.EnterHouse(1512) -- House
end, "Drink from Fountain")

RegisterEvent(82, "+20 Accuracy and Speed temporary.", function()
    evt.EnterHouse(1515) -- House
end, "+20 Accuracy and Speed temporary.")

RegisterEvent(83, "+20 Armor class temporary.", function()
    evt.EnterHouse(1518) -- House
end, "+20 Armor class temporary.")

RegisterEvent(84, "+10 Level temporary.", function()
    evt.EnterHouse(1521) -- House
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

