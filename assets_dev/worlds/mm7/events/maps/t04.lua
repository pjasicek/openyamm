-- The Hall of the Pit
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
    },
    contextActions = {
    [3] = { kind = "open_door", source = "title" },
    [151] = { kind = "open_door", source = "opcode" },
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
    [451] = { kind = "teleport", source = "heuristic" },
    [452] = { kind = "teleport", source = "heuristic" },
    [453] = { kind = "teleport", source = "heuristic" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out05.odm", targetName = "Deyja" },
    [502] = { kind = "passage", source = "opcode", targetMap = "7d26.blv", targetName = "The Pit" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    if IsQBitSet(QBit(612)) then return end -- Chose the path of Dark
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn Gargoyle A, spawn Harpy A, spawn Zombie A
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(151, nil, function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    if not IsQBitSet(QBit(707)) then -- Retrieve the Seasons' Stole from the Hall of the Pit and return it to Gary Zimm in the Bracada Desert.
        evt.OpenChest(1)
        return
    end
    if not HasAward(Award(52)) then -- Retrieved the Seasons' Stole
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

RegisterEvent(451, nil, function()
    evt.MoveToMap(2304, 1152, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(452, nil, function()
    evt.MoveToMap(576, 11200, 64, 0, 0, 0, 0, 0)
end)

RegisterEvent(453, nil, function()
    evt.MoveToMap(512, 7680, -1488, 0, 0, 0, 0, 0)
end)

RegisterEvent(501, "Leave the Hall of the Pit", function()
    evt.MoveToMap(18294, 6145, 1825, 1152, 0, 0, 0, 8, "7out05.odm") -- Deyja
end, "Leave the Hall of the Pit")

RegisterEvent(502, "Enter the Pit", function()
    if IsQBitSet(QBit(611)) or IsQBitSet(QBit(612)) then -- Chose the path of Light
        evt.MoveToMap(-256, 1024, 65, 1536, 0, 0, 0, 8, "7d26.blv") -- The Pit
    end
end, "Enter the Pit")

