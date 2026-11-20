-- Colony Zod
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
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
    [3] = { kind = "open_door", source = "opcode" },
    [5] = { kind = "open_door", source = "opcode" },
    [6] = { kind = "open_door", source = "opcode" },
    [7] = { kind = "open_door", source = "opcode" },
    [8] = { kind = "open_door", source = "opcode" },
    [9] = { kind = "open_door", source = "opcode" },
    [10] = { kind = "open_door", source = "opcode" },
    [11] = { kind = "open_door", source = "opcode" },
    [12] = { kind = "open_door", source = "opcode" },
    [13] = { kind = "open_door", source = "opcode" },
    [14] = { kind = "open_door", source = "opcode" },
    [15] = { kind = "open_door", source = "opcode" },
    [16] = { kind = "open_door", source = "opcode" },
    [17] = { kind = "open_door", source = "opcode" },
    [18] = { kind = "open_door", source = "opcode" },
    [19] = { kind = "open_door", source = "opcode" },
    [20] = { kind = "open_door", source = "opcode" },
    [21] = { kind = "open_door", source = "opcode" },
    [23] = { kind = "open_door", source = "opcode" },
    [24] = { kind = "open_door", source = "opcode" },
    [25] = { kind = "open_door", source = "opcode" },
    [26] = { kind = "open_door", source = "opcode" },
    [27] = { kind = "open_door", source = "opcode" },
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
    [377] = { kind = "open_door", source = "title" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out12.odm", targetName = "The Land of the Giants" },
    },
    textureNames = {},
    spriteNames = {"0"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(2, nil, function()
    if not evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 0, 0, false) then return end -- OE actor 0; all matching actors defeated
    if IsQBitSet(QBit(617)) then return end -- Slayed Xenofex
    SetQBit(QBit(617)) -- Slayed Xenofex
    evt.ShowMovie("\"family reunion\"", true)
    AddValue(History(25), 0)
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(5, DoorAction.Trigger)
    evt.SetDoorState(6, DoorAction.Trigger)
end)

RegisterEvent(4, nil, function()
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(1, FacetBits.Invisible, 1)
    evt.SetFacetBit(2, FacetBits.Untouchable, 0)
    evt.SetFacetBit(2, FacetBits.Invisible, 0)
end)

RegisterEvent(5, nil, function()
    evt.SetDoorState(7, DoorAction.Trigger)
    evt.SetDoorState(8, DoorAction.Trigger)
end)

RegisterEvent(6, nil, function()
    evt.SetDoorState(9, DoorAction.Trigger)
    evt.SetDoorState(10, DoorAction.Trigger)
    evt.SetDoorState(11, DoorAction.Trigger)
end)

RegisterEvent(7, nil, function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end)

RegisterEvent(8, nil, function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(14, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(14, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(9, nil, function()
    if IsAtLeast(MapVar(2), 3) then return end
    evt.SetDoorState(15, DoorAction.Trigger)
    AddValue(MapVar(2), 1)
end)

RegisterEvent(10, nil, function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(16, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(11, nil, function()
    if not IsAtLeast(MapVar(2), 3) then
        evt.SetDoorState(17, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(17, DoorAction.Trigger)
    evt.SetLight(1, 0)
    evt.SetFacetBit(3, FacetBits.Untouchable, 1)
end)

RegisterEvent(12, nil, function()
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end)

RegisterEvent(13, nil, function()
    evt.SetDoorState(20, DoorAction.Trigger)
    evt.SetDoorState(21, DoorAction.Trigger)
end)

RegisterEvent(14, nil, function()
    evt.SetDoorState(22, DoorAction.Trigger)
    evt.SetDoorState(23, DoorAction.Trigger)
end)

RegisterEvent(15, nil, function()
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
end)

RegisterEvent(16, nil, function()
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(17, nil, function()
    evt.SetDoorState(28, DoorAction.Trigger)
    evt.SetDoorState(29, DoorAction.Trigger)
end)

RegisterEvent(18, nil, function()
    if IsAtLeast(MapVar(3), 2) then
        evt.SetDoorState(30, DoorAction.Trigger)
        evt.SetDoorState(31, DoorAction.Trigger)
    end
end)

RegisterEvent(19, nil, function()
    evt.SetDoorState(34, DoorAction.Trigger)
    evt.SetDoorState(35, DoorAction.Trigger)
    evt.SetDoorState(36, DoorAction.Trigger)
    evt.SetDoorState(26, DoorAction.Close)
    evt.SetDoorState(27, DoorAction.Close)
end)

RegisterEvent(20, nil, function()
    evt.SetDoorState(37, DoorAction.Trigger)
    evt.SetDoorState(38, DoorAction.Trigger)
    evt.SetDoorState(39, DoorAction.Trigger)
    evt.SetDoorState(30, DoorAction.Close)
    evt.SetDoorState(31, DoorAction.Close)
end)

RegisterEvent(21, nil, function()
    if HasItem(1089) then -- _potion/reagent
        evt.SetDoorState(32, DoorAction.Trigger)
        evt.SetDoorState(33, DoorAction.Trigger)
    end
end)

RegisterEvent(23, nil, function()
    if IsAtLeast(MapVar(4), 1) then return end
    evt.SetDoorState(40, DoorAction.Trigger)
    AddValue(MapVar(3), 1)
    AddValue(MapVar(4), 1)
end)

RegisterEvent(24, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    evt.SetDoorState(41, DoorAction.Trigger)
    AddValue(MapVar(3), 1)
    AddValue(MapVar(5), 1)
end)

RegisterEvent(25, nil, function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(26, nil, function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(27, nil, function()
    evt.SetDoorState(42, DoorAction.Trigger)
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

RegisterEvent(376, nil, function()
    evt.SpeakNPC(626) -- Roland Ironfist
    evt.SetSprite(20, 1, "0")
    AddValue(InventoryItem(1463), 1463) -- Colony Zod Key
    SetQBit(QBit(752)) -- Talked to Roland
    AddValue(History(24), 0)
    evt.SetFacetBit(1, FacetBits.Untouchable, 1)
    evt.SetFacetBit(1, FacetBits.Invisible, 1)
end)

RegisterEvent(377, "Door", function()
    if not HasItem(1463) then -- Colony Zod Key
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        evt.StatusText("The Door is Locked")
        return
    end
    RemoveItem(1463) -- Colony Zod Key
    evt.SetDoorState(32, DoorAction.Open)
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(501, "Leave the Hive", function()
    evt.MoveToMap(-18246, -11910, 3201, 128, 0, 0, 0, 0, "out12.odm") -- The Land of the Giants
end, "Leave the Hive")

