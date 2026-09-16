-- The Mercenary Guild
-- generated from legacy EVT/STR

SetMapMetadata({
    levitateTrapEvents = {451},
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
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "open_door", source = "opcode" },
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
    [22] = { kind = "open_door", source = "opcode" },
    [23] = { kind = "open_door", source = "opcode" },
    [24] = { kind = "open_door", source = "opcode" },
    [25] = { kind = "open_door", source = "opcode" },
    [26] = { kind = "open_door", source = "opcode" },
    [27] = { kind = "open_door", source = "opcode" },
    [28] = { kind = "open_door", source = "opcode" },
    [29] = { kind = "open_door", source = "opcode" },
    [30] = { kind = "open_door", source = "opcode" },
    [31] = { kind = "open_door", source = "opcode" },
    [32] = { kind = "open_door", source = "opcode" },
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
    [197] = { kind = "open_door", source = "opcode" },
    [198] = { kind = "open_door", source = "opcode" },
    [199] = { kind = "open_door", source = "opcode" },
    [200] = { kind = "open_door", source = "opcode" },
    [451] = { kind = "secret_event", source = "heuristic", hidden = true },
    [452] = { kind = "generic_event", source = "opcode" },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out13.odm", targetName = "Tatalia" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {24, 39},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Bowman, Master of the Sword, spawn Archer A, spawn Fighter Leather A, +1 more
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(3, DoorAction.Close)
end)

RegisterEvent(4, nil, function()
    evt.SetDoorState(4, DoorAction.Open)
end)

RegisterEvent(5, nil, function()
    evt.SetDoorState(4, DoorAction.Close)
end)

RegisterEvent(6, nil, function()
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(7, nil, function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(8, nil, function()
    evt.SetDoorState(6, DoorAction.Open)
end)

RegisterEvent(9, nil, function()
    evt.SetDoorState(6, DoorAction.Close)
end)

RegisterEvent(10, nil, function()
    evt.SetDoorState(7, DoorAction.Trigger)
end)

RegisterEvent(11, nil, function()
    evt.SetDoorState(7, DoorAction.Close)
end)

RegisterEvent(12, nil, function()
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end)

RegisterEvent(13, nil, function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Close)
end)

RegisterEvent(14, nil, function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end)

RegisterEvent(15, nil, function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
end)

RegisterEvent(16, "Bookcase", function()
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(37, DoorAction.Open)
end, "Bookcase")

RegisterEvent(17, nil, function()
    evt.SetDoorState(12, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
end)

RegisterEvent(18, nil, function()
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(1, DoorAction.Open)
end)

RegisterEvent(19, nil, function()
    evt.SetDoorState(3, DoorAction.Open)
end)

RegisterEvent(20, nil, function()
    evt.SetDoorState(17, DoorAction.Open)
    evt.SetDoorState(18, DoorAction.Open)
end)

RegisterEvent(21, nil, function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Close)
end)

RegisterEvent(22, "Bookcase", function()
    evt.SetDoorState(23, DoorAction.Open)
    evt.SetDoorState(24, DoorAction.Open)
end, "Bookcase")

RegisterEvent(23, nil, function()
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
end)

RegisterEvent(24, nil, function()
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
end)

RegisterEvent(25, nil, function()
    evt.SetDoorState(27, DoorAction.Open)
    evt.SetDoorState(28, DoorAction.Open)
    evt.CastSpell(39, 7, 4, -1136, 4480, 29, 112, 4480, 160) -- Blades
end)

RegisterEvent(26, nil, function()
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(28, DoorAction.Close)
end)

RegisterEvent(27, nil, function()
    evt.SetDoorState(29, DoorAction.Open)
    evt.SetDoorState(30, DoorAction.Open)
end)

RegisterEvent(28, nil, function()
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(30, DoorAction.Close)
end)

RegisterEvent(29, nil, function()
    evt.SetDoorState(31, DoorAction.Open)
end)

RegisterEvent(30, nil, function()
    evt.SetDoorState(31, DoorAction.Close)
end)

RegisterEvent(31, nil, function()
    evt.SetDoorState(32, DoorAction.Open)
end)

RegisterEvent(32, nil, function()
    evt.SetDoorState(32, DoorAction.Close)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if IsQBitSet(QBit(729)) then return end -- Heart of Wood - I lost it
    evt.OpenChest(3)
    SetQBit(QBit(729)) -- Heart of Wood - I lost it
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

RegisterEvent(196, "Wine Rack", function()
    if IsAtLeast(MapVar(6), 2) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 12, 12, 13, 14})
    if randomStep == 2 then
        local randomStep = PickRandomOption(196, 3, {3, 5, 7, 9, 11, 12})
        if randomStep == 3 then
            AddValue(InventoryItem(1025), 1025) -- _potion/reagent
        elseif randomStep == 5 then
            AddValue(InventoryItem(1029), 1029) -- _potion/reagent
        elseif randomStep == 7 then
            AddValue(InventoryItem(1030), 1030) -- _potion/reagent
        elseif randomStep == 9 then
            AddValue(InventoryItem(1024), 1024) -- _potion/reagent
        elseif randomStep == 11 then
            AddValue(InventoryItem(1040), 1040) -- _potion/reagent
        end
        local randomStep = PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14})
        if randomStep == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 12 then
        local randomStep = PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14})
        if randomStep == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 13 then
        AddValue(MapVar(6), 1)
    end
end, "Wine Rack")

RegisterEvent(197, nil, function()
    evt.SetDoorState(19, DoorAction.Trigger)
end)

RegisterEvent(198, nil, function()
    evt.SetDoorState(20, DoorAction.Trigger)
end)

RegisterEvent(199, nil, function()
    evt.SetDoorState(21, DoorAction.Trigger)
end)

RegisterEvent(200, nil, function()
    evt.SetDoorState(22, DoorAction.Trigger)
end)

RegisterEvent(451, nil, function()
    evt.CastSpell(24, 2, 4, 2240, 4336, 215, 2240, 4336, -64) -- Poison Spray
    evt.CastSpell(24, 2, 4, 2464, 4032, 215, 2464, 4336, -64) -- Poison Spray
end)

RegisterEvent(452, "Bookcase", function()
    evt.StatusText("You see nothing of interest")
end, "Bookcase")

RegisterEvent(501, "Leave the Mercenary Guild", function()
    evt.MoveToMap(17920, 16803, 3072, 1536, 0, 0, 0, 0, "7out13.odm") -- Tatalia
end, "Leave the Mercenary Guild")

