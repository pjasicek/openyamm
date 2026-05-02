-- The Temple of the Moon
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [21] = {1},
    [22] = {2},
    [23] = {3},
    [24] = {4},
    [25] = {5},
    [26] = {6},
    [27] = {7},
    [28] = {8},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {2},
    timers = {
    { eventId = 51, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(21, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(22, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(23, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(24, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(25, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(26, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(27, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(29, "Bookcase", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    AddValue(InventoryItem(1202), 1202) -- Torch Light
end, "Bookcase")

RegisterEvent(30, "Bookcase", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    AddValue(InventoryItem(1224), 1224) -- Awaken
end, "Bookcase")

RegisterEvent(31, "Bookcase", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    AddValue(InventoryItem(1104), 1104) -- Fire Resistance
end, "Bookcase")

RegisterEvent(32, "Bookcase", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    AddValue(InventoryItem(1113), 1113) -- Wizard Eye
end, "Bookcase")

RegisterEvent(33, "Bookcase", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    AddValue(InventoryItem(1103), 1103) -- Fire Bolt
end, "Bookcase")

RegisterEvent(34, "Bookcase", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    AddValue(InventoryItem(1125), 1125) -- Poison Spray
end, "Bookcase")

RegisterEvent(35, "Bookcase", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(8), 1)
    AddValue(InventoryItem(1102), 1102) -- Torch Light
end, "Bookcase")

RegisterEvent(36, "Bookcase", function()
    if IsAtLeast(MapVar(9), 1) then return end
    SetValue(MapVar(9), 1)
    AddValue(InventoryItem(1102), 1102) -- Torch Light
end, "Bookcase")

RegisterEvent(37, "Bookcase", function()
    if IsAtLeast(MapVar(10), 1) then return end
    SetValue(MapVar(10), 1)
    AddValue(InventoryItem(1102), 1102) -- Torch Light
end, "Bookcase")

RegisterEvent(38, "Bookcase", function()
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    AddValue(InventoryItem(1102), 1102) -- Torch Light
end, "Bookcase")

RegisterEvent(39, "Bookcase", function()
    if IsAtLeast(MapVar(12), 1) then return end
    SetValue(MapVar(12), 1)
    AddValue(InventoryItem(1102), 1102) -- Torch Light
end, "Bookcase")

RegisterEvent(40, "Bookcase", function()
    if IsAtLeast(MapVar(13), 1) then return end
    SetValue(MapVar(13), 1)
    AddValue(InventoryItem(1113), 1113) -- Wizard Eye
end, "Bookcase")

RegisterEvent(41, "Bookcase", function()
    if IsAtLeast(MapVar(14), 1) then return end
    SetValue(MapVar(14), 1)
    AddValue(InventoryItem(1113), 1113) -- Wizard Eye
end, "Bookcase")

RegisterEvent(42, "Bookcase", function()
    if IsAtLeast(MapVar(15), 1) then return end
    SetValue(MapVar(15), 1)
    AddValue(InventoryItem(1113), 1113) -- Wizard Eye
end, "Bookcase")

RegisterEvent(43, "Bookcase", function()
    if IsAtLeast(MapVar(16), 1) then return end
    SetValue(MapVar(16), 1)
    AddValue(InventoryItem(1113), 1113) -- Wizard Eye
end, "Bookcase")

RegisterEvent(51, "Legacy event 51", function()
    evt.CastSpell(2, 2, 1, -2619, 7850, -95, -2619, 4008, -95) -- Fire Bolt
    evt.CastSpell(2, 2, 1, -2619, 4050, -95, -2619, 7896, -95) -- Fire Bolt
end)

RegisterEvent(100, "Leave the Temple of the Moon", function()
    evt.MoveToMap(15816, 12161, 1133, 1024, 0, 0, 0, 0, "7out01.odm")
end, "Leave the Temple of the Moon")

