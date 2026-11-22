-- The Temple of Baa
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {2},
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
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [151] = { kind = "use_elevator", source = "title" },
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
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out14.odm", targetName = "Avlee" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Acolyte of the Moon, Cleric of the Moon, Priest of the Moon, spawn Devil A, +1 more
end)

RegisterEvent(2, nil, function()
    if evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 34, 1, false) then -- OE actor 34; at least 1 matching actor defeated
        SetQBit(QBit(755)) -- Killed High Preist of Baa
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Trigger)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Trigger)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Trigger)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Trigger)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Trigger)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(10, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(11, DoorAction.Trigger)
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Door")

RegisterEvent(151, "Lift", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Lift")

RegisterEvent(176, "Chest", function()
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

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(501, nil, function()
    evt.MoveToMap(-9306, -19451, 3361, 0, 0, 0, 0, 8, "out14.odm") -- Avlee
end)

