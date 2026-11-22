-- Barrow VII
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {0, 1},
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
    },
    contextActions = {
    [1] = { kind = "open_door", source = "opcode" },
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_door", source = "opcode" },
    [151] = { kind = "open_door", source = "opcode" },
    [152] = { kind = "open_door", source = "opcode" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {0, 1} },
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
    [376] = { kind = "open_door", source = "opcode" },
    [451] = { kind = "use_lever", source = "title" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out11.odm", targetName = "The Barrow Downs" },
    [502] = { kind = "passage", source = "opcode", targetMap = "mdt01.blv", targetName = "Barrow IX" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if not IsQBitSet(QBit(704)) then -- Turn on map in mdkXX(Dwarven Barrow)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn AGog A, spawn Rat A
        return
    end
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn AGog A, spawn Rat A
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SetDoorState(2, DoorAction.Close)
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(5, nil, function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(6, nil, function()
    evt.SetDoorState(6, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(151, nil, function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(152, nil, function()
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(704)) then -- Turn on map in mdkXX(Dwarven Barrow)
        evt.OpenChest(0)
        return
    end
    evt.OpenChest(1)
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

RegisterEvent(376, "Key Hole", function()
    if IsQBitSet(QBit(704)) then return end -- Turn on map in mdkXX(Dwarven Barrow)
    evt.ForPlayer(Players.All)
    if HasItem(1458) then -- Barrow Key
        evt.SetDoorState(25, DoorAction.Open)
        evt.SetDoorState(26, DoorAction.Open)
        SetQBit(QBit(704)) -- Turn on map in mdkXX(Dwarven Barrow)
        RemoveItem(1458) -- Barrow Key
    end
end, "Key Hole")

RegisterEvent(451, "Lever", function()
    if not IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(20, DoorAction.Open)
        SetValue(MapVar(2), 2)
        return
    end
    evt.SetDoorState(20, DoorAction.Close)
    SetValue(MapVar(2), 1)
end, "Lever")

RegisterEvent(501, "Leave the Dwarven Barrow", function()
    evt.MoveToMap(10155, -18616, 1601, 1024, 0, 0, 0, 8, "out11.odm") -- The Barrow Downs
end, "Leave the Dwarven Barrow")

RegisterEvent(502, "Leave the Dwarven Barrow", function()
    if not IsAtLeast(MapVar(2), 2) then
        evt.MoveToMap(-412, 298, -15, 1792, 0, 0, 0, 0, "mdt01.blv") -- Barrow IX
        return
    end
    evt.MoveToMap(925, -684, 65, 776, 0, 0, 0, 0, "mdr01.blv") -- Barrow X
end, "Leave the Dwarven Barrow")

