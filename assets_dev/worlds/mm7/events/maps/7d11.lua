-- The Walls of Mist
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {0},
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
    [151] = { kind = "open_door", source = "opcode" },
    [152] = { kind = "open_door", source = "opcode" },
    [176] = { kind = "open_chest", source = "opcode", chestIds = {0} },
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
    [376] = { kind = "open_door", source = "opcode" },
    [377] = { kind = "open_door", source = "opcode" },
    [378] = { kind = "open_door", source = "opcode" },
    [452] = { kind = "teleport", source = "heuristic" },
    [453] = { kind = "teleport", source = "heuristic" },
    [454] = { kind = "teleport", source = "heuristic" },
    [455] = { kind = "teleport", source = "heuristic" },
    [456] = { kind = "teleport", source = "heuristic" },
    [457] = { kind = "teleport", source = "heuristic" },
    [458] = { kind = "teleport", source = "heuristic" },
    [459] = { kind = "teleport", source = "heuristic" },
    [460] = { kind = "teleport", source = "heuristic" },
    [461] = { kind = "teleport", source = "heuristic" },
    [462] = { kind = "teleport", source = "heuristic" },
    [463] = { kind = "teleport", source = "heuristic" },
    [464] = { kind = "teleport", source = "heuristic" },
    [465] = { kind = "teleport", source = "heuristic" },
    [466] = { kind = "open_door", source = "opcode" },
    [467] = { kind = "open_door", source = "opcode" },
    [468] = { kind = "open_door", source = "opcode" },
    [469] = { kind = "open_door", source = "opcode" },
    [501] = { kind = "passage", source = "opcode", targetMap = "7d25.blv", targetName = "Celeste" },
    [502] = { kind = "passage", source = "opcode", targetMap = "7d25.blv", targetName = "Celeste" },
    },
    textureNames = {"7wtrtyl"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    SetValue(MapVar(20), 0)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Lesser Light Elemental, spawn Elemental Air A, spawn Genie A, spawn Mage A
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(28, DoorAction.Trigger)
end)

RegisterEvent(4, nil, function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.SetDoorState(5, DoorAction.Trigger)
        SetValue(MapVar(3), 0)
        SetValue(MapVar(6), 1)
        return
    end
    SetValue(MapVar(6), 0)
    SetValue(MapVar(3), 1)
    evt.SetDoorState(5, DoorAction.Trigger)
end)

RegisterEvent(5, nil, function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.SetDoorState(6, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        AddValue(MapVar(7), 1)
        return
    end
    SubtractValue(MapVar(7), 1)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(6, DoorAction.Trigger)
end)

RegisterEvent(6, nil, function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.SetDoorState(7, DoorAction.Trigger)
        SetValue(MapVar(3), 0)
        SetValue(MapVar(8), 1)
        return
    end
    SetValue(MapVar(8), 0)
    SetValue(MapVar(3), 1)
    evt.SetDoorState(7, DoorAction.Trigger)
end)

RegisterEvent(7, nil, function()
    if not IsAtLeast(MapVar(9), 1) then
        evt.SetDoorState(8, DoorAction.Trigger)
        SetValue(MapVar(3), 0)
        SetValue(MapVar(9), 1)
        return
    end
    SetValue(MapVar(9), 0)
    SetValue(MapVar(3), 1)
    evt.SetDoorState(8, DoorAction.Trigger)
end)

RegisterEvent(8, nil, function()
    if not IsAtLeast(MapVar(10), 1) then
        evt.SetDoorState(9, DoorAction.Trigger)
        AddValue(MapVar(2), 1)
        AddValue(MapVar(10), 1)
        return
    end
    SubtractValue(MapVar(10), 1)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(9, DoorAction.Trigger)
end)

RegisterEvent(9, nil, function()
    if not IsAtLeast(MapVar(11), 1) then
        evt.SetDoorState(10, DoorAction.Trigger)
        SetValue(MapVar(3), 0)
        SetValue(MapVar(11), 1)
        return
    end
    SetValue(MapVar(11), 0)
    SetValue(MapVar(3), 1)
    evt.SetDoorState(10, DoorAction.Trigger)
end)

RegisterEvent(10, nil, function()
    if IsAtLeast(MapVar(3), 1) then
        if IsAtLeast(MapVar(2), 2) then
            evt.SetDoorState(3, DoorAction.Trigger)
            evt.SetDoorState(4, DoorAction.Trigger)
            evt.SetDoorState(11, DoorAction.Trigger)
            SetValue(MapVar(2), 0)
            SetValue(MapVar(7), 0)
            SetValue(MapVar(10), 0)
        end
        return
    elseif IsAtLeast(MapVar(6), 1) then
        return
    elseif IsAtLeast(MapVar(8), 1) then
        return
    elseif IsAtLeast(MapVar(11), 1) then
        return
    elseif IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(3, DoorAction.Trigger)
        evt.SetDoorState(4, DoorAction.Trigger)
        evt.SetDoorState(11, DoorAction.Trigger)
        SetValue(MapVar(2), 0)
        SetValue(MapVar(7), 0)
        SetValue(MapVar(10), 0)
    else
        return
    end
end)

RegisterEvent(11, nil, function()
    evt.SetDoorState(29, DoorAction.Trigger)
end)

RegisterEvent(12, nil, function()
    evt.SetDoorState(30, DoorAction.Trigger)
end)

RegisterEvent(151, nil, function()
    evt.SetDoorState(12, DoorAction.Trigger)
end)

RegisterEvent(152, nil, function()
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(14, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(0)
    SetQBit(QBit(660)) -- Got Lich Jar from Walls of Mist
    SetAutonote(1) -- Destroyer's Riddles. Riddle One: "Prison." Riddle Two: ? Riddle Three: ? Prison + ? + ?
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
    ClearQBit(QBit(741)) -- Lich Jar (Empty) - I lost it
end, "Chest")

RegisterEvent(376, nil, function()
    if IsAtLeast(MapVar(17), 1) then
        return
    elseif HasItem(1454) then -- West Pillar Key
        RemoveItem(1454) -- West Pillar Key
        evt.SetDoorState(31, DoorAction.Trigger)
        SetValue(MapVar(17), 1)
        AddValue(MapVar(20), 1)
        if IsAtLeast(MapVar(20), 3) then
            evt.SetDoorState(1, DoorAction.Open)
            evt.SetDoorState(2, DoorAction.Open)
        end
        return
    elseif IsAtLeast(MapVar(20), 3) then
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetDoorState(2, DoorAction.Open)
    else
        return
    end
end)

RegisterEvent(377, nil, function()
    if IsAtLeast(MapVar(18), 1) then
        return
    elseif HasItem(1455) then -- Central Pillar Key
        RemoveItem(1455) -- Central Pillar Key
        evt.SetDoorState(32, DoorAction.Trigger)
        SetValue(MapVar(18), 1)
        AddValue(MapVar(20), 1)
        if IsAtLeast(MapVar(20), 3) then
            evt.SetDoorState(1, DoorAction.Open)
            evt.SetDoorState(2, DoorAction.Open)
        end
        return
    elseif IsAtLeast(MapVar(20), 3) then
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetDoorState(2, DoorAction.Open)
    else
        return
    end
end)

RegisterEvent(378, nil, function()
    if IsAtLeast(MapVar(19), 1) then
        return
    elseif HasItem(1456) then -- East Pillar Key
        RemoveItem(1456) -- East Pillar Key
        evt.SetDoorState(33, DoorAction.Trigger)
        SetValue(MapVar(19), 1)
        AddValue(MapVar(20), 1)
        if IsAtLeast(MapVar(20), 3) then
            evt.SetDoorState(1, DoorAction.Open)
            evt.SetDoorState(2, DoorAction.Open)
        end
        return
    elseif IsAtLeast(MapVar(20), 3) then
        evt.SetDoorState(1, DoorAction.Open)
        evt.SetDoorState(2, DoorAction.Open)
    else
        return
    end
end)

RegisterEvent(452, nil, function()
    evt.MoveToMap(-10880, 7424, 96, 0, 0, 0, 0, 0)
end)

RegisterEvent(453, nil, function()
    evt.MoveToMap(-1792, -128, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(454, nil, function()
    evt.MoveToMap(-896, -128, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(455, nil, function()
    evt.MoveToMap(8448, -21120, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(456, nil, function()
    evt.MoveToMap(13568, -6528, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(457, nil, function()
    evt.MoveToMap(1, -128, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(458, nil, function()
    evt.MoveToMap(13280, 1152, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(459, nil, function()
    evt.MoveToMap(13312, 704, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(460, nil, function()
    evt.MoveToMap(13248, 2976, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(461, nil, function()
    evt.MoveToMap(13248, 3456, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(462, nil, function()
    evt.MoveToMap(12384, 2144, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(463, nil, function()
    evt.MoveToMap(11936, 2144, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(464, nil, function()
    evt.MoveToMap(14240, 2048, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(465, nil, function()
    evt.MoveToMap(14944, 2080, 160, 0, 0, 0, 0, 0)
end)

RegisterEvent(466, nil, function()
    if IsAtLeast(MapVar(13), 1) then return end
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetFacetBit(1, FacetBits.Fluid, 1)
    evt.SetTexture(1, "7wtrtyl")
    evt.SetDoorState(17, DoorAction.Trigger)
    AddValue(MapVar(13), 1)
    if not IsAtLeast(MapVar(12), 1) then
        evt.SetDoorState(24, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 2) then
        evt.SetDoorState(25, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 3) then
        evt.SetDoorState(26, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(467, nil, function()
    if IsAtLeast(MapVar(14), 1) then return end
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetFacetBit(2, FacetBits.Fluid, 1)
    evt.SetTexture(2, "7wtrtyl")
    evt.SetDoorState(19, DoorAction.Trigger)
    AddValue(MapVar(14), 1)
    if not IsAtLeast(MapVar(12), 1) then
        evt.SetDoorState(24, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 2) then
        evt.SetDoorState(25, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 3) then
        evt.SetDoorState(26, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(468, nil, function()
    if IsAtLeast(MapVar(15), 1) then return end
    evt.SetDoorState(20, DoorAction.Trigger)
    evt.SetFacetBit(3, FacetBits.Fluid, 1)
    evt.SetTexture(3, "7wtrtyl")
    evt.SetDoorState(21, DoorAction.Trigger)
    AddValue(MapVar(15), 1)
    if not IsAtLeast(MapVar(12), 1) then
        evt.SetDoorState(24, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 2) then
        evt.SetDoorState(25, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 3) then
        evt.SetDoorState(26, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(469, nil, function()
    if IsAtLeast(MapVar(16), 1) then return end
    evt.SetDoorState(22, DoorAction.Trigger)
    evt.SetFacetBit(4, FacetBits.Fluid, 1)
    evt.SetTexture(4, "7wtrtyl")
    evt.SetDoorState(23, DoorAction.Trigger)
    AddValue(MapVar(16), 1)
    if not IsAtLeast(MapVar(12), 1) then
        evt.SetDoorState(24, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 2) then
        evt.SetDoorState(25, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    if not IsAtLeast(MapVar(12), 3) then
        evt.SetDoorState(26, DoorAction.Trigger)
        AddValue(MapVar(12), 1)
        return
    end
    evt.SetFacetBit(5, FacetBits.Untouchable, 1)
    evt.SetFacetBit(5, FacetBits.Invisible, 1)
    evt.SetDoorState(27, DoorAction.Trigger)
end)

RegisterEvent(501, "Leave the Walls of Mist", function()
    evt.MoveToMap(1728, 3648, 97, 1024, 0, 0, 0, 8, "7d25.blv") -- Celeste
end, "Leave the Walls of Mist")

RegisterEvent(502, "Leave the Walls of Mist", function()
    if not evt.CheckMonstersKilled(ActorKillCheck.Group, 52, 1, false) then -- actor group 52; at least 1 matching actor defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(614)) -- Completed Proving Grounds without killing a single creature
        evt.MoveToMap(1728, 3648, 97, 1024, 0, 0, 0, 8, "7d25.blv") -- Celeste
        return
    end
    evt.MoveToMap(1728, 3648, 97, 1024, 0, 0, 0, 8, "7d25.blv") -- Celeste
end, "Leave the Walls of Mist")

