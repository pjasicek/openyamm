-- Barrow XI
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
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if not IsQBitSet(QBit(705)) then -- Turn on map in mdrXX(Dwarven Barrow)
        evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
        return
    end
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Door", function()
    evt.OpenChest(1)
end, "Door")

RegisterEvent(177, "Door", function()
    evt.OpenChest(2)
end, "Door")

RegisterEvent(178, "Door", function()
    evt.OpenChest(3)
end, "Door")

RegisterEvent(179, "Door", function()
    evt.OpenChest(4)
end, "Door")

RegisterEvent(180, "Door", function()
    evt.OpenChest(5)
end, "Door")

RegisterEvent(181, "Door", function()
    evt.OpenChest(6)
end, "Door")

RegisterEvent(182, "Door", function()
    evt.OpenChest(7)
end, "Door")

RegisterEvent(183, "Door", function()
    evt.OpenChest(8)
end, "Door")

RegisterEvent(184, "Door", function()
    evt.OpenChest(9)
end, "Door")

RegisterEvent(185, "Door", function()
    evt.OpenChest(10)
end, "Door")

RegisterEvent(186, "Door", function()
    evt.OpenChest(11)
end, "Door")

RegisterEvent(187, "Door", function()
    evt.OpenChest(12)
end, "Door")

RegisterEvent(188, "Door", function()
    evt.OpenChest(13)
end, "Door")

RegisterEvent(189, "Door", function()
    evt.OpenChest(14)
end, "Door")

RegisterEvent(190, "Door", function()
    evt.OpenChest(15)
end, "Door")

RegisterEvent(191, "Door", function()
    evt.OpenChest(16)
end, "Door")

RegisterEvent(192, "Door", function()
    evt.OpenChest(17)
end, "Door")

RegisterEvent(193, "Door", function()
    evt.OpenChest(18)
end, "Door")

RegisterEvent(194, "Door", function()
    evt.OpenChest(19)
end, "Door")

RegisterEvent(195, "Door", function()
    evt.OpenChest(0)
end, "Door")

RegisterEvent(451, "Lever", function()
    if not IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(20, DoorAction.Open)
        SetValue(MapVar(2), 2)
        return
    end
    evt.SetDoorState(20, DoorAction.Close)
    SetValue(MapVar(2), 1)
end, "Lever")

RegisterEvent(452, "Lever", function()
    if not IsAtLeast(MapVar(3), 2) then
        evt.SetDoorState(21, DoorAction.Open)
        SetValue(MapVar(3), 2)
        return
    end
    evt.SetDoorState(21, DoorAction.Close)
    SetValue(MapVar(3), 1)
end, "Lever")

RegisterEvent(501, "Leave the Dwarven Barrow", function()
    if not IsAtLeast(MapVar(3), 2) then
        evt.MoveToMap(406, 365, 49, 640, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(414, 278, -31, 1408, 0, 0, 0, 0)
end, "Leave the Dwarven Barrow")

RegisterEvent(502, "Leave the Dwarven Barrow", function()
    if not IsAtLeast(MapVar(2), 2) then
        evt.MoveToMap(395, -1076, 1, 768, 0, 0, 0, 0)
        return
    end
    evt.MoveToMap(-346, 265, 33, 1792, 0, 0, 0, 0)
end, "Leave the Dwarven Barrow")

