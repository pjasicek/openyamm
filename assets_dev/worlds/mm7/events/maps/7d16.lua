-- The Wine Cellar
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
    [3] = { kind = "open_door", source = "opcode" },
    [4] = { kind = "press_button", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "opcode" },
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
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out13.odm", targetName = "Tatalia" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Elder Vampire, Shade, spawn Bat A, spawn Necromancer A, +1 more
end)

RegisterEvent(2, nil, function()
    if evt.CheckMonstersKilled(ActorKillCheck.ActorIdOe, 0, 0, true) then -- OE actor 0; all matching actors defeated
        SetQBit(QBit(619)) -- Slayed the vampire
    end
end)

RegisterEvent(3, nil, function()
    evt.SetDoorState(3, DoorAction.Open)
end)

RegisterEvent(4, "Button", function()
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Close)
end, "Button")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Wine Rack", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Wine Rack")

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

RegisterEvent(196, "Wine Rack", function()
    if IsAtLeast(MapVar(6), 2) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 12, 12, 13, 14})
    if randomStep == 2 then
        local randomStep = PickRandomOption(196, 3, {3, 5, 7, 9, 11, 12})
        if randomStep == 3 then
            AddValue(InventoryItem(225), 225) -- Cure Disease
        elseif randomStep == 5 then
            AddValue(InventoryItem(229), 229) -- Heroism
        elseif randomStep == 7 then
            AddValue(InventoryItem(230), 230) -- Bless
        elseif randomStep == 9 then
            AddValue(InventoryItem(224), 224) -- Cure Weakness
        elseif randomStep == 11 then
            AddValue(InventoryItem(240), 240) -- Might Boost
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

RegisterEvent(501, "Leave the Vampire Family House", function()
    SetQBit(QBit(619)) -- Slayed the vampire
    evt.MoveToMap(8216, -10619, 289, 0, 0, 0, 0, 1, "7out13.odm") -- Tatalia
end, "Leave the Vampire Family House")

