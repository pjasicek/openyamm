-- White Cliff Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535, 65534, 65533},
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
    [196] = { kind = "secret_event", source = "heuristic", hidden = true },
    [197] = { kind = "secret_event", source = "heuristic", hidden = true },
    [198] = { kind = "secret_event", source = "heuristic", hidden = true },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out02.odm", targetName = "Harmondale" },
    },
    textureNames = {"cwb1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

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

RegisterEvent(196, nil, function()
    if IsAtLeast(MapVar(16), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 4, 6, 7, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(Players.All, const.Damage.Fire, 50)
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 7 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    end
    SetValue(MapVar(16), 1)
    evt.SetTexture(2, "cwb1")
end)

RegisterEvent(197, nil, function()
    if IsAtLeast(MapVar(17), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 4, 6, 7, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(Players.All, const.Damage.Fire, 50)
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 7 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    end
    SetValue(MapVar(17), 1)
    evt.SetTexture(3, "cwb1")
end)

RegisterEvent(198, nil, function()
    if IsAtLeast(MapVar(18), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 4, 6, 7, 2, 2})
    if randomStep == 2 then
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
    elseif randomStep == 4 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 6 then
        evt.DamagePlayer(Players.All, const.Damage.Fire, 50)
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    elseif randomStep == 7 then
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
    end
    SetValue(MapVar(18), 1)
    evt.SetTexture(4, "cwb1")
end)

RegisterEvent(501, "Leave the White Cliff Caves", function()
    evt.MoveToMap(9686, -17990, 702, 1024, 0, 0, 0, 4, "7out02.odm") -- Harmondale
end, "Leave the White Cliff Caves")

RegisterEvent(65535, "", function()
    if IsAtLeast(MapVar(16), 1) then
        evt.SetTexture(2, "cwb1")
    end
end)

RegisterEvent(65534, "", function()
    if IsAtLeast(MapVar(17), 1) then
        evt.SetTexture(3, "cwb1")
    end
end)

RegisterEvent(65533, "", function()
    if IsAtLeast(MapVar(18), 1) then
        evt.SetTexture(4, "cwb1")
    end
end)

