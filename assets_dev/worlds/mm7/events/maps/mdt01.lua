-- Barrow IX
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
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "open_door", source = "opcode" },
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
    [502] = { kind = "passage", source = "opcode", targetMap = "mdr03.blv", targetName = "Barrow V" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if not IsQBitSet(QBit(703)) then -- Turn on map in mdtXX(Dwarven Barrow)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn AGog A, spawn Bat A
        return
    end
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn AGog A, spawn Bat A
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(4, nil, function()
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(703)) then -- Turn on map in mdtXX(Dwarven Barrow)
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
    if IsQBitSet(QBit(703)) then return end -- Turn on map in mdtXX(Dwarven Barrow)
    evt.ForPlayer(Players.All)
    if HasItem(1457) then -- Barrow Key
        evt.SetDoorState(25, DoorAction.Open)
        evt.SetDoorState(26, DoorAction.Open)
        SetQBit(QBit(703)) -- Turn on map in mdtXX(Dwarven Barrow)
        RemoveItem(1457) -- Barrow Key
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
    evt.MoveToMap(16667, 12511, 1779, 512, 0, 0, 0, 8, "out11.odm") -- The Barrow Downs
end, "Leave the Dwarven Barrow")

RegisterEvent(502, "Leave the Dwarven Barrow", function()
    if not IsAtLeast(MapVar(2), 2) then
        evt.MoveToMap(2899, 1448, 695, 260, 0, 0, 0, 0, "mdr03.blv") -- Barrow V
        return
    end
    evt.MoveToMap(407, -1064, 1, 768, 0, 0, 0, 0, "mdk01.blv") -- Barrow VII
end, "Leave the Dwarven Barrow")

