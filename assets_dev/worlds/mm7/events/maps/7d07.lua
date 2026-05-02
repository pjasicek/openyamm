-- Thunderfist Mountain
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1, 0},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {6, 41, 43},
    timers = {
    { eventId = 453, repeating = true, intervalGameMinutes = 1, remainingGameMinutes = 1 },
    { eventId = 454, repeating = true, intervalGameMinutes = 3, remainingGameMinutes = 3 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(9, DoorAction.Open)
end)

RegisterEvent(151, "Legacy event 151", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
end)

RegisterEvent(152, "Legacy event 152", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end)

RegisterEvent(176, "Chest", function()
    if not HasAward(Award(24)) then -- Retrieved Soul Jars
        evt.OpenChest(1)
        SetQBit(QBit(743)) -- Lich Jar Case - I lost it
        SetQBit(QBit(661)) -- Got Lich Jar from Thunderfist Mountain
        return
    end
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Bookcase", function()
    if IsAtLeast(MapVar(51), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(196, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(51), 1)
    end
end, "Bookcase")

RegisterEvent(197, "Bookcase", function()
    if IsAtLeast(MapVar(52), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(197, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(52), 1)
    end
end, "Bookcase")

RegisterEvent(198, "Bookcase", function()
end, "Bookcase")

RegisterEvent(451, "Legacy event 451", function()
    evt.ForPlayer(Players.All)
    SetValue(Eradicated, 0)
end)

RegisterEvent(452, "Legacy event 452", function()
    if not IsAtLeast(FireResistanceBonus, 50) then
        if not IsAtLeast(FireResistance, 50) then
            evt.ForPlayer(Players.All)
            SetValue(Eradicated, 0)
            return
        end
    end
    local randomStep = PickRandomOption(452, 6, {6, 8})
    if randomStep == 6 then
        evt.ForPlayer(Players.All)
        SetValue(Eradicated, 0)
    end
end)

RegisterEvent(453, "Legacy event 453", function()
    local randomStep = PickRandomOption(453, 2, {2, 3, 6, 7, 2, 7})
    if randomStep == 2 then
        evt.CastSpell(41, 15, 4, -1536, -896, 0, -1536, -896, 5376) -- Rock Blast
        evt.CastSpell(41, 15, 4, -128, -704, 0, -128, -704, 5376) -- Rock Blast
        local randomStep = PickRandomOption(453, 5, {5, 7, 7, 6, 7, 7})
        if randomStep == 5 then
            evt.CastSpell(43, 20, 4, -128, -1216, 0, -128, -1216, 5376) -- Death Blossom
            evt.CastSpell(43, 20, 4, -128, -704, 0, -128, -704, 1576) -- Death Blossom
        elseif randomStep == 6 then
            evt.CastSpell(43, 20, 4, -128, -704, 0, -128, -704, 1576) -- Death Blossom
        end
    elseif randomStep == 3 then
        evt.CastSpell(41, 15, 4, -128, -704, 0, -128, -704, 5376) -- Rock Blast
        local randomStep = PickRandomOption(453, 5, {5, 7, 7, 6, 7, 7})
        if randomStep == 5 then
            evt.CastSpell(43, 20, 4, -128, -1216, 0, -128, -1216, 5376) -- Death Blossom
            evt.CastSpell(43, 20, 4, -128, -704, 0, -128, -704, 1576) -- Death Blossom
        elseif randomStep == 6 then
            evt.CastSpell(43, 20, 4, -128, -704, 0, -128, -704, 1576) -- Death Blossom
        end
    elseif randomStep == 6 then
        evt.CastSpell(43, 20, 4, -128, -704, 0, -128, -704, 1576) -- Death Blossom
    end
end)

RegisterEvent(454, "Legacy event 454", function()
    SetValue(MapVar(3), 1)
    local randomStep = PickRandomOption(454, 3, {4, 6, 8, 10, 10, 10})
    if randomStep == 4 then
        evt.CastSpell(6, 10, 4, 1293, -2315, 4200, 777, -2315, 4200) -- Fireball
        if IsAtLeast(MapVar(3), 1) then return end
        evt.CastSpell(6, 10, 4, 743, -1675, 4200, 1306, -1675, 4200) -- Fireball
        if IsAtLeast(MapVar(3), 1) then return end
        evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
    elseif randomStep == 6 then
        evt.CastSpell(6, 10, 4, 743, -1675, 4200, 1306, -1675, 4200) -- Fireball
        if IsAtLeast(MapVar(3), 1) then return end
        evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
    elseif randomStep == 8 then
        evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
    elseif randomStep == 10 then
        SetValue(MapVar(3), 0)
        local randomStep = PickRandomOption(454, 12, {4, 6, 8})
        if randomStep == 4 then
            evt.CastSpell(6, 10, 4, 1293, -2315, 4200, 777, -2315, 4200) -- Fireball
            if IsAtLeast(MapVar(3), 1) then return end
            evt.CastSpell(6, 10, 4, 743, -1675, 4200, 1306, -1675, 4200) -- Fireball
            if IsAtLeast(MapVar(3), 1) then return end
            evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
        elseif randomStep == 6 then
            evt.CastSpell(6, 10, 4, 743, -1675, 4200, 1306, -1675, 4200) -- Fireball
            if IsAtLeast(MapVar(3), 1) then return end
            evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
        elseif randomStep == 8 then
            evt.CastSpell(6, 10, 4, 1275, -1022, 4200, 762, -1022, 4200) -- Fireball
        end
    end
end)

RegisterEvent(501, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(-7673, -7957, 3201, 512, 0, 0, 0, 0, "out10.odm")
end, "Leave Thunderfist Mountain")

RegisterEvent(502, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(-14395, 3771, 3201, 1024, 0, 0, 0, 0, "out10.odm")
end, "Leave Thunderfist Mountain")

RegisterEvent(503, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(6138, 3063, 2406, 0, 0, 0, 0, 0, "out10.odm")
end, "Leave Thunderfist Mountain")

RegisterEvent(504, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(11623, -11083, 3840, 0, 0, 0, 0, 0, "out10.odm")
end, "Leave Thunderfist Mountain")

RegisterEvent(505, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(9350, -1010, 1, 744, 0, 0, 45, 0, "7d35.blv")
end, "Leave Thunderfist Mountain")

RegisterEvent(506, "Leave Thunderfist Mountain", function()
    evt.MoveToMap(-437, -1078, 1, 256, 0, 0, 48, 0, "7d36.blv")
end, "Leave Thunderfist Mountain")

