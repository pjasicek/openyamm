-- The Arena
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
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
    { eventId = 451, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 452, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 453, repeating = true, intervalGameMinutes = 1.5, remainingGameMinutes = 1.5 },
    { eventId = 454, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 455, repeating = true, intervalGameMinutes = 2, remainingGameMinutes = 2 },
    { eventId = 456, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

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

RegisterEvent(376, "Door", function()
    evt.SpeakNPC(639) -- Arena Master
end, "Door")

RegisterEvent(451, "Legacy event 451", function()
    evt.SetDoorState(1, DoorAction.Trigger)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end)

RegisterEvent(453, "Legacy event 453", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end)

RegisterEvent(454, "Legacy event 454", function()
    evt.SetDoorState(4, DoorAction.Trigger)
end)

RegisterEvent(455, "Legacy event 455", function()
    evt.SetDoorState(5, DoorAction.Trigger)
end)

RegisterEvent(456, "Legacy event 456", function()
    evt.SetDoorState(6, DoorAction.Trigger)
end)

RegisterEvent(457, "Legacy event 457", function()
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
    evt.SetDoorState(5, DoorAction.Trigger)
    evt.SetDoorState(6, DoorAction.Trigger)
end)

RegisterEvent(501, "Leave the Arena", function()
    evt.MoveToMap(-5692, 11137, 1, 1024, 0, 0, 0, 0, "7out02.odm")
end, "Leave the Arena")

