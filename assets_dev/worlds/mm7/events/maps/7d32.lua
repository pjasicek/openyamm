-- Castle Navan
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
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
    contextActions = {
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "opcode" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "opcode" },
    [12] = { kind = "open_door", source = "title" },
    [151] = { kind = "open_door", source = "opcode" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [177] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [178] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [179] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [180] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [181] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [182] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [183] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [184] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [185] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [186] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [187] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [188] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [189] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [190] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [191] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [192] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [193] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [194] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [195] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [196] = { kind = "generic_event", source = "opcode" },
    [197] = { kind = "generic_event", source = "opcode" },
    [198] = { kind = "generic_event", source = "opcode" },
    [199] = { kind = "generic_event", source = "opcode" },
    [416] = { kind = "enter_house", source = "opcode", houseId = 218, targetName = "Throne Room" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out04.odm", targetName = "The Tularean Forest" },
    [502] = { kind = "passage", source = "opcode", targetMap = "7d08.blv", targetName = "The Tularean Caves" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 454, sourceEventId = 454, triggerStep = 0, origin = "legacy", triggerKind = "long", scheduleKind = "monthly" },
    },
})

RegisterEvent(1, nil, function()
    if IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
    elseif IsQBitSet(QBit(612)) then -- Chose the path of Dark
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
    else
        return
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(4, nil, function()
    if IsQBitSet(QBit(547)) then -- Raid the Elven Treasury at Castle Navan in the Tularean Forest and return to Frederick Org in Erathia.
        evt.SetDoorState(7, DoorAction.Open)
    end
end)

RegisterEvent(5, "Door", function()
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Door", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        SetValue(MapVar(6), 2)
        evt.SetDoorState(12, DoorAction.Open)
        evt.SetDoorState(13, DoorAction.Open)
        return
    end
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    if not IsAtLeast(MapVar(6), 2) then
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        SetValue(MapVar(6), 2)
        evt.SetDoorState(14, DoorAction.Open)
        evt.SetDoorState(15, DoorAction.Open)
        return
    end
    evt.SetDoorState(14, DoorAction.Open)
    evt.SetDoorState(15, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(16, DoorAction.Open)
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(11, nil, function()
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end)

RegisterEvent(12, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(151, nil, function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(1)
        return
    end
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(2)
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(3)
        return
    end
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(179, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(4)
        return
    end
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(5)
        return
    end
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(6)
        return
    end
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(8)
        return
    end
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(9)
        return
    end
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(10)
        return
    end
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(11)
        return
    end
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(12)
        return
    end
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(13)
        return
    end
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(14)
        return
    end
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(15)
        return
    end
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(16)
        return
    end
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(17)
        return
    end
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(18)
        return
    end
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(19)
        return
    end
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    if not IsAtLeast(MapVar(6), 2) then
        SetValue(MapVar(6), 2)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
        evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
        evt.OpenChest(0)
        return
    end
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
    if IsAtLeast(MapVar(53), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(198, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(53), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(198, 5, {5, 7, 9, 11, 13, 14})
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
        local randomStep = PickRandomOption(198, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(53), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(53), 1)
    end
end, "Bookcase")

RegisterEvent(199, "Bookcase", function()
end, "Bookcase")

RegisterEvent(376, nil, function()
    if IsQBitSet(QBit(572)) then return end -- Robbed Elven treasury. Black Knight promo quest.
    evt.ForPlayer(Players.All)
    SetQBit(QBit(572)) -- Robbed Elven treasury. Black Knight promo quest.
end)

RegisterEvent(416, "Throne Room", function()
    if IsQBitSet(QBit(610)) then -- Built Castle to Level 2 (rescued dwarf guy)
        if not IsAtLeast(MapVar(6), 2) then
            evt.EnterHouse(218) -- Throne Room
            return
        end
    end
    evt.StatusText("The Door is Locked")
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Throne Room")

RegisterEvent(451, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.SpeakNPC(617) -- Castle Guard
    SetValue(MapVar(6), 1)
end)

RegisterEvent(452, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Peasant, spawn Dragonfly A, spawn Elf Archer A, spawn Elf Spearman A
    evt.SetMonGroupBit(55, MonsterBits.Hostile, 1) -- actor group 55: Elven Scout
    SetValue(MapVar(6), 2)
end)

RegisterEvent(453, nil, function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(6), 2) then return end
    SetValue(MapVar(6), 0)
end)

RegisterEvent(454, nil, function()
    SetValue(MapVar(6), 0)
end)

RegisterEvent(501, "Leave Castle Navan", function()
    evt.MoveToMap(-18532, -10251, 1537, 0, 0, 0, 0, 8, "7out04.odm") -- The Tularean Forest
end, "Leave Castle Navan")

RegisterEvent(502, "Leave Castle Navan", function()
    evt.MoveToMap(-3257, -12544, 833, 0, 0, 0, 0, 3, "7d08.blv") -- The Tularean Caves
end, "Leave Castle Navan")

