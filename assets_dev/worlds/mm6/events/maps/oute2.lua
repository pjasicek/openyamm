-- Misty Islands
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535, 65534, 65533, 65532, 65531, 65530, 65529, 65528, 213},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    },
    textureNames = {},
    spriteNames = {"6tree06"},
    castSpellIds = {6},
    timers = {
    { eventId = 210, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterNoOpEvent(1, "Tree", "Tree")

RegisterEvent(2, "Drink from Fountain.", function()
    evt.EnterHouse(26) -- Arm's Length Spear Shop
end, "Drink from Fountain.")

RegisterEvent(3, "Drink from Fountain.", nil, "Drink from Fountain.")

RegisterEvent(4, "You pray at the shrine.", function()
    evt.EnterHouse(63) -- Armor Emporium
end, "You pray at the shrine.")

RegisterEvent(5, "You pray at the shrine.", nil, "You pray at the shrine.")

RegisterEvent(6, "Witch's Brew", function()
    evt.EnterHouse(98) -- Witch's Brew
end, "Witch's Brew")

RegisterEvent(7, "Legacy event 7", nil)

RegisterEvent(8, "Lock, Stock, and Barrel", function()
    evt.EnterHouse(1229) -- Lock, Stock, and Barrel
end, "Lock, Stock, and Barrel")

RegisterEvent(9, "Lock, Stock, and Barrel", nil, "Lock, Stock, and Barrel")

RegisterEvent(10, "Adventure", function()
    evt.EnterHouse(499) -- Adventure
end, "Adventure")

RegisterEvent(11, "Island Testing Center", function()
    evt.EnterHouse(1590) -- Island Testing Center
end, "Island Testing Center")

RegisterEvent(12, "Island Testing Center", nil, "Island Testing Center")

RegisterEvent(13, "Town Hall", function()
    evt.EnterHouse(210) -- Town Hall
end, "Town Hall")

RegisterEvent(14, "Mist Island Temple", function()
    evt.EnterHouse(330) -- Mist Island Temple
end, "Mist Island Temple")

RegisterEvent(15, "The Imp Slapper", function()
    evt.EnterHouse(261) -- The Imp Slapper
end, "The Imp Slapper")

RegisterEvent(16, "The Imp Slapper", nil, "The Imp Slapper")

RegisterEvent(17, "The Reserves", function()
    evt.EnterHouse(298) -- The Reserves
end, "The Reserves")

RegisterEvent(18, "The Reserves", nil, "The Reserves")

RegisterEvent(19, "Initiate Guild of Fire", function()
    evt.EnterHouse(132) -- Initiate Guild of Fire
end, "Initiate Guild of Fire")

RegisterEvent(20, "Initiate Guild of Fire", nil, "Initiate Guild of Fire")

RegisterEvent(21, "Initiate Guild of Air", function()
    evt.EnterHouse(138) -- Initiate Guild of Air
end, "Initiate Guild of Air")

RegisterEvent(22, "Initiate Guild of Air", nil, "Initiate Guild of Air")

RegisterEvent(23, "Initiate Guild of Water", function()
    evt.EnterHouse(144) -- Initiate Guild of Water
end, "Initiate Guild of Water")

RegisterEvent(24, "Initiate Guild of Water", nil, "Initiate Guild of Water")

RegisterEvent(25, "Duelists' Edge", function()
    evt.EnterHouse(198) -- Duelists' Edge
end, "Duelists' Edge")

RegisterEvent(26, "Duelists' Edge", nil, "Duelists' Edge")

RegisterEvent(27, "Buccaneers' Lair", function()
    evt.EnterHouse(192) -- Buccaneers' Lair
end, "Buccaneers' Lair")

RegisterEvent(28, "Buccaneers' Lair", nil, "Buccaneers' Lair")

RegisterEvent(29, "Town Hall", nil, "Town Hall")

RegisterEvent(30, "Throne Room", function()
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 80, 1, "0.")
    evt.EnterHouse(223) -- Throne Room
end, "Throne Room")

RegisterEvent(31, "Welcome to Misty Islands", nil, "Welcome to Misty Islands")

RegisterEvent(50, "House", function()
    evt.EnterHouse(1227) -- House
end, "House")

RegisterEvent(51, "House", function()
    evt.EnterHouse(1242) -- House
end, "House")

RegisterEvent(52, "House", function()
    evt.EnterHouse(1257) -- House
end, "House")

RegisterEvent(53, "House", function()
    evt.EnterHouse(1272) -- House
end, "House")

RegisterEvent(54, "House", function()
    evt.EnterHouse(1287) -- House
end, "House")

RegisterEvent(55, "House", function()
    evt.EnterHouse(1302) -- House
end, "House")

RegisterEvent(56, "House", function()
    evt.EnterHouse(1315) -- House
end, "House")

RegisterEvent(57, "House", function()
    evt.EnterHouse(1327) -- House
end, "House")

RegisterEvent(58, "House", function()
    evt.EnterHouse(1338) -- House
end, "House")

RegisterEvent(59, "House", function()
    evt.EnterHouse(1350) -- House
end, "House")

RegisterEvent(60, "House", function()
    evt.EnterHouse(1362) -- House
end, "House")

RegisterEvent(61, "House", function()
    evt.EnterHouse(1373) -- House
    if IsQBitSet(QBit(1325)) then return end -- NPC
    SetQBit(QBit(1325)) -- NPC
end, "House")

RegisterEvent(62, "House", function()
    evt.EnterHouse(1384) -- House
end, "House")

RegisterEvent(75, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(76, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(77, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(78, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(79, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(90, "Legacy event 90", function()
    evt.MoveToMap(4427, 3061, 769, 1024, 0, 0, 178, 1, "6d07.blv")
end)

RegisterEvent(91, "Legacy event 91", function()
    if IsQBitSet(QBit(1325)) then -- NPC
        evt.MoveToMap(-18176, -1072, 96, 512, 0, 0, 0, 0)
    end
end)

RegisterEvent(92, "Legacy event 92", function()
    evt.MoveToMap(4688, -2944, 96, 1400, 0, 0, 0, 0)
end)

RegisterEvent(101, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(2), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(2), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(134, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(2), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(102, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(3), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(3), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(135, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(3), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(103, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(4), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(4), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(136, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(4), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(104, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(5), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(5), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(137, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(5), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(105, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(6), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(6), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(138, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(6), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(106, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(7), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(7), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(139, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(7), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(107, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(8), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(8), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(140, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(8), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(108, "Tree", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(9), 1) then return 6 end
        return 1
    end
    local function Step_1()
        SetValue(MapVar(9), 1)
        return 2
    end
    local function Step_2()
        AddValue(Food, 1)
        return 3
    end
    local function Step_3()
        evt.StatusText("Tree")
        return 4
    end
    local function Step_4()
        evt.SetSprite(141, 1, "6tree06")
        return 5
    end
    local function Step_5()
        return nil
    end
    local function Step_6()
        evt.StatusText("There doesn't seem to be anymore apples.")
        return 8
    end
    local function Step_8()
        if IsAtLeast(MapVar(9), 1) then return 4 end
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
        elseif step == 8 then
            step = Step_8()
        else
            step = nil
        end
    end
end, "Tree")

RegisterEvent(109, "Drink from Fountain.", function()
    if not IsAtLeast(MapVar(11), 1) then
        evt.StatusText("Refreshing!")
        return
    end
    SubtractValue(MapVar(11), 1)
    AddValue(CurrentSpellPoints, 10)
    evt.StatusText("+10 Spell points restored.")
    SetAutonote(401) -- 10 Spell points restored by the central fountain in Mist.
end, "Drink from Fountain.")

RegisterEvent(110, "Drink from Fountain.", function()
    if not IsAtLeast(IntellectBonus, 10) then
        SetValue(IntellectBonus, 10)
        SetValue(PersonalityBonus, 10)
        evt.StatusText("+10 Intellect and Personality temporary.")
        SetAutonote(403) -- 10 Points of temporary intellect and personality from the west fountain at Castle Newton.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain.")

RegisterEvent(111, "Drink from Fountain.", function()
    if not IsAtLeast(FireResistanceBonus, 5) then
        SetValue(FireResistanceBonus, 5)
        SetValue(AirResistanceBonus, 5)
        SetValue(WaterResistanceBonus, 5)
        SetValue(EarthResistanceBonus, 5)
        evt.StatusText("+5 Elemental resistance temporary.")
        SetAutonote(404) -- 5 Points of temporary fire, electricity, cold, and poison resistance from the east fountain at Castle Newton.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Fountain.")

RegisterEvent(112, "Drink from Well.", function()
    if not IsAtLeast(LuckBonus, 20) then
        SetValue(LuckBonus, 20)
        evt.StatusText("+20 Luck temporary.")
        SetAutonote(402) -- 20 Points of temporary luck from the fountain west of the Imp Slapper in Mist.
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from Well.")

RegisterEvent(113, "Drink from Trough.", function()
    evt.DamagePlayer(7, 2, 20)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Trough.")

RegisterEvent(114, "Drink from Trough.", function()
    evt.StatusText("Refreshing!")
end, "Drink from Trough.")

RegisterEvent(210, "Legacy event 210", function()
    if IsQBitSet(QBit(1181)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, 3039, -9201, 2818, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(211, "Legacy event 211", function()
    evt.ForPlayer(Players.All)
    if IsQBitSet(QBit(1181)) then -- NPC
        return
    elseif HasItem(2106) then -- Dragon Tower Keys
        SetQBit(QBit(1181)) -- NPC
        return
    else
        return
    end
end)

RegisterEvent(212, "Obelisk", function()
    evt.SimpleMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            f_oteh__fe_h__e_")
    SetQBit(QBit(1397)) -- NPC
    SetAutonote(455) -- Obelisk Message # 14: f_oteh__fe_h__e_
end, "Obelisk")

RegisterEvent(213, "Legacy event 213", function()
    if IsQBitSet(QBit(1181)) then -- NPC
    end
end)

RegisterEvent(261, "Shrine of Intellect", function()
    if not IsAtLeast(MonthIs, 1) then
        evt.StatusText("You pray at the shrine.")
        return
    end
    if not IsQBitSet(QBit(1230)) then -- NPC
        SetQBit(QBit(1230)) -- NPC
        if not IsQBitSet(QBit(1232)) then -- NPC
            SetQBit(QBit(1232)) -- NPC
            evt.ForPlayer(Players.All)
            AddValue(BaseIntellect, 10)
            evt.StatusText("+10 Intellect permanent")
            return
        end
        evt.ForPlayer(Players.All)
        AddValue(BaseIntellect, 3)
        evt.StatusText("+3 Intellect permanent")
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Intellect")

RegisterEvent(65535, "", function()
    return evt.map[101](8)
end)

RegisterEvent(65534, "", function()
    return evt.map[102](8)
end)

RegisterEvent(65533, "", function()
    return evt.map[103](8)
end)

RegisterEvent(65532, "", function()
    return evt.map[104](8)
end)

RegisterEvent(65531, "", function()
    return evt.map[105](8)
end)

RegisterEvent(65530, "", function()
    return evt.map[106](8)
end)

RegisterEvent(65529, "", function()
    return evt.map[107](8)
end)

RegisterEvent(65528, "", function()
    return evt.map[108](8)
end)

