-- Temple of Tsantsa
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [12] = {1},
    [13] = {2},
    [14] = {4},
    [15] = {5},
    [16] = {6},
    [31] = {3},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 28, repeating = true, intervalGameMinutes = 1, remainingGameMinutes = 1 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(13, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(14, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(15, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(16, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(17, "Lever", function()
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
end, "Lever")

RegisterEvent(18, "Legacy event 18", function()
    SetValue(MapVar(4), 1)
end)

RegisterEvent(19, "Cell", function()
    if not HasItem(2186) then -- Cell Key
        evt.StatusText("The door is locked")
        return
    end
    RemoveItem(2186) -- Cell Key
    evt.SetDoorState(25, DoorAction.Close)
end, "Cell")

RegisterEvent(20, "Lever", function()
    evt.SetDoorState(14, DoorAction.Close)
    AddValue(MapVar(2), 1)
    if IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(16, DoorAction.Close)
    end
end, "Lever")

RegisterEvent(21, "Lever", function()
    evt.SetDoorState(15, DoorAction.Close)
    AddValue(MapVar(2), 1)
    if IsAtLeast(MapVar(2), 2) then
        evt.SetDoorState(16, DoorAction.Close)
    end
end, "Lever")

RegisterEvent(23, "Lever", function()
    evt.SetDoorState(18, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end, "Lever")

RegisterEvent(24, "Lever", function()
    evt.SetDoorState(20, DoorAction.Trigger)
    evt.SetDoorState(21, DoorAction.Trigger)
end, "Lever")

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(17, DoorAction.Close)
end)

RegisterEvent(26, "Lever", function()
    evt.SetDoorState(22, DoorAction.Trigger)
    evt.SetDoorState(23, DoorAction.Trigger)
end, "Lever")

RegisterEvent(27, "Legacy event 27", function()
    SetValue(MapVar(4), 0)
end)

RegisterEvent(28, "Legacy event 28", function()
    if IsAtLeast(MapVar(4), 1) then
        evt.DamagePlayer(5, 5, 5)
    end
end)

RegisterEvent(29, "Door", function()
    evt.SetDoorState(24, DoorAction.Close)
end, "Door")

RegisterEvent(30, "Legacy event 30", function()
    if IsQBitSet(QBit(1030)) then return end -- 6 T3, given when you rescue prisoner
    evt.SpeakNPC(940) -- Sherell Ivanaveh
    SetQBit(QBit(1705)) -- Replacement for NPCs ¹155 ver. 6
    SetQBit(QBit(1030)) -- 6 T3, given when you rescue prisoner
end)

RegisterEvent(31, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(50, "Legacy event 50", function()
    evt.MoveToMap(7474, 17670, 97, 1024, 0, 0, 0, 0, "outd2.odm")
end)

RegisterEvent(55, "Legacy event 55", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    evt.GiveItem(5, 26)
end)

