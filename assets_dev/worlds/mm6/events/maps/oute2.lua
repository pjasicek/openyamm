-- Misty Islands
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {210},
    onLoad = {65535, 65534, 65533, 65532, 65531, 65530, 65529, 65528, 213},
    onLeave = {},
    openedChestIds = {
    [75] = {1},
    [76] = {2},
    [77] = {3},
    [78] = {4},
    [79] = {5},
    },
    contextActions = {
    [2] = { kind = "enter_house", source = "opcode", houseId = 26, targetName = "Arm's Length Spear Shop" },
    [4] = { kind = "enter_house", source = "opcode", houseId = 63, targetName = "Armor Emporium" },
    [6] = { kind = "enter_house", source = "opcode", houseId = 98, targetName = "Witch's Brew" },
    [8] = { kind = "enter_house", source = "opcode", houseId = 1229, targetName = "Lock, Stock, and Barrel" },
    [10] = { kind = "enter_house", source = "opcode", houseId = 499, targetName = "Adventure" },
    [11] = { kind = "enter_house", source = "opcode", houseId = 1590, targetName = "Island Testing Center" },
    [13] = { kind = "enter_house", source = "opcode", houseId = 210, targetName = "Town Hall" },
    [14] = { kind = "enter_house", source = "opcode", houseId = 330, targetName = "Mist Island Temple" },
    [15] = { kind = "enter_house", source = "opcode", houseId = 261, targetName = "The Imp Slapper" },
    [17] = { kind = "enter_house", source = "opcode", houseId = 298, targetName = "The Reserves" },
    [19] = { kind = "enter_house", source = "opcode", houseId = 132, targetName = "Initiate Guild of Fire" },
    [21] = { kind = "enter_house", source = "opcode", houseId = 138, targetName = "Initiate Guild of Air" },
    [23] = { kind = "enter_house", source = "opcode", houseId = 144, targetName = "Initiate Guild of Water" },
    [25] = { kind = "enter_house", source = "opcode", houseId = 198, targetName = "Duelists' Edge" },
    [27] = { kind = "enter_house", source = "opcode", houseId = 192, targetName = "Buccaneers' Lair" },
    [30] = { kind = "enter_house", source = "opcode", houseId = 223, targetName = "Throne Room" },
    [50] = { kind = "enter_house", source = "opcode", houseId = 1227, targetName = "House" },
    [51] = { kind = "enter_house", source = "opcode", houseId = 1242, targetName = "House" },
    [52] = { kind = "enter_house", source = "opcode", houseId = 1257, targetName = "House" },
    [53] = { kind = "enter_house", source = "opcode", houseId = 1272, targetName = "House" },
    [54] = { kind = "enter_house", source = "opcode", houseId = 1287, targetName = "House" },
    [55] = { kind = "enter_house", source = "opcode", houseId = 1302, targetName = "House" },
    [56] = { kind = "enter_house", source = "opcode", houseId = 1315, targetName = "House" },
    [57] = { kind = "enter_house", source = "opcode", houseId = 1327, targetName = "House" },
    [58] = { kind = "enter_house", source = "opcode", houseId = 1338, targetName = "House" },
    [59] = { kind = "enter_house", source = "opcode", houseId = 1350, targetName = "House" },
    [60] = { kind = "enter_house", source = "opcode", houseId = 1362, targetName = "House" },
    [61] = { kind = "enter_house", source = "opcode", houseId = 1373, targetName = "House" },
    [62] = { kind = "enter_house", source = "opcode", houseId = 1384, targetName = "House" },
    [75] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [76] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [77] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [78] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [79] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [90] = { kind = "enter_house", source = "opcode", houseId = 434, targetName = "Silver Helm Outpost" },
    [91] = { kind = "teleport", source = "heuristic" },
    [92] = { kind = "teleport", source = "heuristic" },
    [101] = { kind = "generic_event", source = "opcode" },
    [102] = { kind = "generic_event", source = "opcode" },
    [103] = { kind = "generic_event", source = "opcode" },
    [104] = { kind = "generic_event", source = "opcode" },
    [105] = { kind = "generic_event", source = "opcode" },
    [106] = { kind = "generic_event", source = "opcode" },
    [107] = { kind = "generic_event", source = "opcode" },
    [108] = { kind = "generic_event", source = "opcode" },
    [109] = { kind = "fountain", source = "title" },
    [110] = { kind = "fountain", source = "title" },
    [111] = { kind = "fountain", source = "title" },
    [112] = { kind = "well", source = "title" },
    [113] = { kind = "boost", source = "title" },
    [114] = { kind = "boost", source = "title" },
    [212] = { kind = "obelisk", source = "title" },
    [261] = { kind = "shrine", source = "title" },
    },
    textureNames = {},
    spriteNames = {"6tree06"},
    castSpellIds = {6},
    timers = {
    { eventId = 65527, sourceEventId = 109, triggerStep = 8, origin = "legacy", triggerKind = "long", scheduleKind = "daily", startHour = 0, startMinute = 0, startSecond = 1 },
    { eventId = 210, sourceEventId = 210, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "interval", intervalHalfMinutes = 10 },
    },
})

RegisterNoOpEvent(1, "Tree", "Tree")

RegisterEvent(2, "Arm's Length Spear Shop", function()
    evt.EnterHouse(26) -- Arm's Length Spear Shop
end, "Arm's Length Spear Shop")

RegisterEvent(3, "Arm's Length Spear Shop", nil, "Arm's Length Spear Shop")

RegisterEvent(4, "Armor Emporium", function()
    evt.EnterHouse(63) -- Armor Emporium
end, "Armor Emporium")

RegisterEvent(5, "Armor Emporium", nil, "Armor Emporium")

RegisterEvent(6, "Witch's Brew", function()
    evt.EnterHouse(98) -- Witch's Brew
end, "Witch's Brew")

RegisterEvent(7, nil, nil)

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
    evt.MoveToMap(0, 0, 0, 0, 0, 0, 80, 1)
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

RegisterEvent(90, nil, function()
    evt.MoveToMap(4427, 3061, 769, 1024, 0, 0, 434, 1, "6d07.blv") -- Silver Helm Outpost
end)

RegisterEvent(91, nil, function()
    if IsQBitSet(QBit(1325)) then -- NPC
        evt.MoveToMap(-18176, -1072, 96, 512, 0, 0, 0, 0)
    end
end)

RegisterEvent(92, nil, function()
    evt.MoveToMap(4688, -2944, 96, 1400, 0, 0, 0, 0)
end)

RegisterEvent(101, "Tree", function()
    if not IsAtLeast(MapVar(2), 1) then
        SetValue(MapVar(2), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(134, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(102, "Tree", function()
    if not IsAtLeast(MapVar(3), 1) then
        SetValue(MapVar(3), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(135, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(103, "Tree", function()
    if not IsAtLeast(MapVar(4), 1) then
        SetValue(MapVar(4), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(136, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(104, "Tree", function()
    if not IsAtLeast(MapVar(5), 1) then
        SetValue(MapVar(5), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(137, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(105, "Tree", function()
    if not IsAtLeast(MapVar(6), 1) then
        SetValue(MapVar(6), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(138, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(106, "Tree", function()
    if not IsAtLeast(MapVar(7), 1) then
        SetValue(MapVar(7), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(139, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(107, "Tree", function()
    if not IsAtLeast(MapVar(8), 1) then
        SetValue(MapVar(8), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(140, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
end, "Tree")

RegisterEvent(108, "Tree", function()
    if not IsAtLeast(MapVar(9), 1) then
        SetValue(MapVar(9), 1)
        AddValue(Food, 1)
        evt.StatusText("Tree")
        evt.SetSprite(141, 1, "6tree06")
        return
    end
    evt.StatusText("There doesn't seem to be anymore apples.")
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
    evt.DamagePlayer(Players.Current, const.Damage.Water, 20)
    SetValue(PoisonedYellow, 1)
    evt.StatusText("Poison!")
end, "Drink from Trough.")

RegisterEvent(114, "Drink from Trough.", function()
    evt.StatusText("Refreshing!")
end, "Drink from Trough.")

RegisterEvent(210, nil, function()
    if IsQBitSet(QBit(1181)) then -- NPC
        return
    elseif IsAtLeast(IsFlying, 0) then
        evt.CastSpell(6, 5, 3, 3039, -9201, 2818, 0, 0, 0) -- Fireball
    else
        return
    end
end)

RegisterEvent(211, nil, function()
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

RegisterEvent(212, "Obelisk", function(continueStep)
    if continueStep == 2 then
        SetQBit(QBit(1397)) -- NPC
        SetAutonote(455) -- Obelisk Message # 14: f_oteh__fe_h__e_
    end
    if continueStep ~= nil then return end
    evt.SetMessage("The surface of the obelisk is blood warm to the touch.  A message swims into view as you remove your hand:                                                                                                                                                            f_oteh__fe_h__e_")
    evt._PressAnyKey(212, 2)
end, "Obelisk")

RegisterEvent(213, nil, function()
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
        return
    end
    evt.StatusText("You pray at the shrine.")
end, "Shrine of Intellect")

RegisterEvent(65535, "", function()
    if not IsAtLeast(MapVar(2), 1) then return end
    evt.SetSprite(134, 1, "6tree06")
end)

RegisterEvent(65534, "", function()
    if not IsAtLeast(MapVar(3), 1) then return end
    evt.SetSprite(135, 1, "6tree06")
end)

RegisterEvent(65533, "", function()
    if not IsAtLeast(MapVar(4), 1) then return end
    evt.SetSprite(136, 1, "6tree06")
end)

RegisterEvent(65532, "", function()
    if not IsAtLeast(MapVar(5), 1) then return end
    evt.SetSprite(137, 1, "6tree06")
end)

RegisterEvent(65531, "", function()
    if not IsAtLeast(MapVar(6), 1) then return end
    evt.SetSprite(138, 1, "6tree06")
end)

RegisterEvent(65530, "", function()
    if not IsAtLeast(MapVar(7), 1) then return end
    evt.SetSprite(139, 1, "6tree06")
end)

RegisterEvent(65529, "", function()
    if not IsAtLeast(MapVar(8), 1) then return end
    evt.SetSprite(140, 1, "6tree06")
end)

RegisterEvent(65528, "", function()
    if not IsAtLeast(MapVar(9), 1) then return end
    evt.SetSprite(141, 1, "6tree06")
end)

RegisterEvent(65527, "", function()
    SetValue(MapVar(11), 20)
end)

