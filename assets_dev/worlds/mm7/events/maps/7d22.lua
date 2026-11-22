-- The Hall under the Hill
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {460},
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
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [151] = { kind = "open_door", source = "opcode" },
    [152] = { kind = "teleport", source = "heuristic" },
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
    [197] = { kind = "well", source = "title" },
    [451] = { kind = "teleport", source = "heuristic" },
    [452] = { kind = "teleport", source = "heuristic" },
    [453] = { kind = "open_door", source = "opcode" },
    [454] = { kind = "generic_event", source = "opcode" },
    [455] = { kind = "generic_event", source = "opcode" },
    [456] = { kind = "generic_event", source = "opcode" },
    [457] = { kind = "generic_event", source = "opcode" },
    [458] = { kind = "generic_event", source = "opcode" },
    [459] = { kind = "generic_event", source = "opcode" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out14.odm", targetName = "Avlee" },
    },
    textureNames = {},
    spriteNames = {"0", "tree37"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(3, "Door", function()
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(30, DoorAction.Trigger)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(31, DoorAction.Trigger)
end, "Door")

RegisterEvent(151, nil, function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(152, nil, function()
    evt.MoveToMap(-1383, 2328, 1, 0, 0, 0, 0, 0)
    evt.SetDoorState(1, DoorAction.Open)
end)

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

RegisterEvent(196, "Well", nil, "Well")

RegisterEvent(197, "Drink from the Well", function()
    evt.StatusText("Refreshing !")
end, "Drink from the Well")

RegisterEvent(316, nil, function()
    if IsQBitSet(QBit(549)) or IsQBitSet(QBit(691)) then -- Solve the secret to the entrance of the Faerie Mound in Avlee and speak to the Faerie King.
        evt.SpeakNPC(391) -- Faerie King
    end
end)

RegisterEvent(451, nil, function()
    evt.MoveToMap(1233, -34, -1023, -1, 0, 0, 0, 0)
end)

RegisterEvent(452, nil, function()
    evt.MoveToMap(-1210, 194, -2047, -1, 0, 0, 0, 0)
end)

RegisterEvent(453, nil, function()
    evt.ForPlayer(Players.All)
    if not HasItem(1464) then -- Faerie Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        evt.StatusText("The Door is Locked")
        return
    end
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Close)
    evt.SetDoorState(13, DoorAction.Close)
    evt.SetDoorState(14, DoorAction.Close)
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(16, DoorAction.Close)
    evt.SetDoorState(20, DoorAction.Close)
end)

RegisterEvent(454, "Fruit Tree", function()
    if IsAtLeast(MapVar(52), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(52), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(51, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(455, "Fruit Tree", function()
    if IsAtLeast(MapVar(53), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(53), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(52, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(456, "Fruit Tree", function()
    if IsAtLeast(MapVar(54), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(54), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(53, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(457, "Fruit Tree", function()
    if IsAtLeast(MapVar(55), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(55), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(54, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(458, "Fruit Tree", function()
    if IsAtLeast(MapVar(56), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(56), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(55, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(459, "Fruit Tree", function()
    if IsAtLeast(MapVar(57), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(57), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(56, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(460, nil, function()
    if IsAtLeast(MapVar(52), 1) then
        goto step_4
    end
    evt.SetSprite(51, 1, "0")
    goto step_5
    ::step_4::
    evt.SetSprite(51, 1, "0")
    ::step_5::
    if IsAtLeast(MapVar(53), 1) then
        goto step_8
    end
    evt.SetSprite(52, 1, "0")
    goto step_9
    ::step_8::
    evt.SetSprite(52, 1, "0")
    ::step_9::
    if IsAtLeast(MapVar(54), 1) then
        goto step_12
    end
    evt.SetSprite(53, 1, "0")
    goto step_13
    ::step_12::
    evt.SetSprite(53, 1, "0")
    ::step_13::
    if IsAtLeast(MapVar(55), 1) then
        goto step_16
    end
    evt.SetSprite(54, 1, "0")
    goto step_17
    ::step_16::
    evt.SetSprite(54, 1, "0")
    ::step_17::
    if IsAtLeast(MapVar(56), 1) then
        goto step_20
    end
    evt.SetSprite(55, 1, "0")
    goto step_21
    ::step_20::
    evt.SetSprite(55, 1, "0")
    ::step_21::
    if IsAtLeast(MapVar(57), 1) then
        goto step_24
    end
    evt.SetSprite(56, 1, "0")
    goto step_25
    ::step_24::
    evt.SetSprite(56, 1, "0")
    ::step_25::
    do return end
end)

RegisterEvent(501, "Leave the Hall Under the Hill", function()
    evt.MoveToMap(1550, 21117, 800, 1536, 0, 0, 0, 4, "out14.odm") -- Avlee
end, "Leave the Hall Under the Hill")

