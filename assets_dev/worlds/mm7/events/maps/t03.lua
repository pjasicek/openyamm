-- Grand Temple of the Sun
-- generated from legacy EVT/STR

SetMapMetadata({
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
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [10] = { kind = "press_button", source = "title" },
    [11] = { kind = "press_button", source = "title" },
    [12] = { kind = "press_button", source = "title" },
    [13] = { kind = "press_button", source = "title" },
    [14] = { kind = "press_button", source = "title" },
    [15] = { kind = "press_button", source = "title" },
    [16] = { kind = "press_button", source = "title" },
    [17] = { kind = "open_door", source = "title" },
    [18] = { kind = "open_door", source = "title" },
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
    [376] = { kind = "shrine", source = "title" },
    [451] = { kind = "secret_event", source = "heuristic", hidden = true },
    [501] = { kind = "leave_dungeon", source = "opcode", targetMap = "out09.odm", targetName = "Evenmorn Island" },
    },
    textureNames = {"cfb1"},
    spriteNames = {},
    castSpellIds = {6},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: Priest of the Sun, spawn Cleric Sun A, spawn Monk A
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

RegisterEvent(10, "Button", function()
    evt.SetDoorState(10, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(11, "Button", function()
    evt.SetDoorState(11, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(12, "Button", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(13, "Button", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(14, "Button", function()
    evt.SetDoorState(14, DoorAction.Trigger)
    SetValue(MapVar(2), 1)
end, "Button")

RegisterEvent(15, "Button", function()
    evt.SetDoorState(15, DoorAction.Trigger)
    SubtractValue(MapVar(2), 1)
    evt.SetDoorState(14, DoorAction.Close)
end, "Button")

RegisterEvent(16, "Button", function()
    if IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(16, DoorAction.Trigger)
        evt.SetDoorState(9, DoorAction.Trigger)
    end
end, "Button")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(2, DoorAction.Trigger)
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

RegisterEvent(376, "Altar", function()
    evt.Debug("Ahoj1")
    if IsQBitSet(QBit(575)) then return end -- Defaced the Altar of Good. Priest of Dark promo quest.
    evt.Debug("Ahoj2")
    if IsQBitSet(QBit(556)) then -- Deface the Altar of Good in the Temple of the Sun on Evenmorn Isle then return to Daedalus Falk in the Deyja Moors.
        evt.Debug("Ahoj3")
        evt.SetTexture(20, "cfb1")
        SetQBit(QBit(575)) -- Defaced the Altar of Good. Priest of Dark promo quest.
        evt.ForPlayer(Players.All)
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        evt.StatusText("You have Desecrated the altar")
        evt.Debug("Ahoj5")
    end
end, "Altar")

RegisterEvent(451, nil, function()
    evt.CastSpell(6, 10, 4, -5, 3919, 288, 0, 1044, 289) -- Fireball
end)

RegisterEvent(501, "Leave the Grand Temple of the Sun", function()
    evt.MoveToMap(-7166, 11033, 185, 1536, 0, 0, 0, 0, "out09.odm") -- Evenmorn Island
end, "Leave the Grand Temple of the Sun")

