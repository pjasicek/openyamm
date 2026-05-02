-- The Hive
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {100},
    onLeave = {},
    openedChestIds = {
    [41] = {1},
    [42] = {2},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 51, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    { eventId = 54, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    { eventId = 57, repeating = true, intervalGameMinutes = 60, remainingGameMinutes = 60 },
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
    if not HasItem(2190) then -- Hive Sanctum Key
        evt.StatusText("The door is locked")
        return
    end
    evt.SetDoorState(6, DoorAction.Close)
    RemoveItem(2190) -- Hive Sanctum Key
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

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Switch", function()
    evt.MoveToMap(468, 3690, 1, 45, 0, 0, 0, 0)
    evt.SetDoorState(16, DoorAction.Trigger)
    SetValue(MapVar(2), 0)
    evt.StatusText("Flush system deactivated")
end, "Switch")

RegisterEvent(17, "Legacy event 17", function()
    if IsAtLeast(MapVar(23), 1) then
        return
    elseif IsAtLeast(MapVar(2), 1) then
        return
    else
        evt.StatusText("Flush system activated.")
        SetValue(MapVar(2), 0)
        return
    end
end)

RegisterEvent(19, "Legacy event 19", function()
    if IsAtLeast(MapVar(23), 1) then
        return
    elseif IsAtLeast(MapVar(2), 1) then
        return
    else
        SetValue(MapVar(2), 1)
        return
    end
end)

RegisterEvent(21, "Door", function()
    evt.StatusText("The Door Won't Budge")
end, "Door")

RegisterEvent(22, "Legacy event 22", function()
    SetValue(MapVar(5), 0)
end)

RegisterEvent(23, "Keg", function()
    evt.StatusText(" +20 Hit Points")
    AddValue(CurrentHealth, 20)
end, "Keg")

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(43, DoorAction.Close)
end)

RegisterEvent(28, "Door", function()
    evt.SetDoorState(28, DoorAction.Close)
end, "Door")

RegisterEvent(29, "Legacy event 29", function()
    SetValue(MapVar(2), 0)
end)

RegisterEvent(31, "Switch", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
end, "Switch")

RegisterEvent(33, "Legacy event 33", function()
    evt.SetDoorState(35, DoorAction.Trigger)
    evt.SetDoorState(36, DoorAction.Trigger)
end)

RegisterEvent(34, "Switch", function()
    evt.SetDoorState(37, DoorAction.Trigger)
    evt.SetDoorState(38, DoorAction.Trigger)
end, "Switch")

RegisterEvent(36, "Switch", function()
    evt.SetDoorState(41, DoorAction.Trigger)
    evt.SetDoorState(43, DoorAction.Trigger)
end, "Switch")

RegisterEvent(38, "Legacy event 38", function()
    evt.SetDoorState(42, DoorAction.Close)
end)

RegisterEvent(39, "Legacy event 39", function()
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
end)

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(2)
    SetValue(MapVar(12), 1)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(48, "Exit", function()
    evt.MoveToMap(-14355, 15010, 3841, 1408, 0, 0, 0, 0, "outa1.odm")
end, "Exit")

RegisterEvent(50, "Switch", function()
    evt.SetDoorState(50, DoorAction.Close)
    SetValue(MapVar(23), 1)
end, "Switch")

RegisterEvent(51, "Legacy event 51", function()
    if IsAtLeast(MapVar(22), 1) then
        evt.StatusText("Flush sequence complete.")
        SetValue(MapVar(22), 0)
    end
end)

RegisterEvent(54, "Legacy event 54", function()
    if not IsAtLeast(MapVar(21), 1) then return end
    evt.StatusText("Flush sequence in progress.")
    if not IsAtLeast(MapVar(3), 1) then
        evt.DamagePlayer(5, 4, 20)
    end
    SetValue(MapVar(22), 1)
    SetValue(MapVar(21), 0)
end)

RegisterEvent(56, "Protected", function()
    SetValue(MapVar(3), 1)
end, "Protected")

RegisterEvent(57, "Legacy event 57", function()
    if IsAtLeast(MapVar(2), 1) then
        evt.StatusText("Warning!  Flush system activated!")
        SetValue(MapVar(21), 1)
    end
end)

RegisterEvent(58, "Legacy event 58", function()
    SetValue(MapVar(3), 0)
end)

RegisterEvent(60, "Exit", function()
    if not IsQBitSet(QBit(1226)) then -- NPC
        evt.StatusText("The door is locked")
        return
    end
    evt.ForPlayer(Players.All)
    if not HasItem(2164) then -- Ritual of the Void
        evt.EnterHouse(0)
        return
    end
    SetQBit(QBit(1261)) -- NPC
    ClearQBit(QBit(1222)) -- Quest item bits for seer
    RemoveItem(2164) -- Ritual of the Void
    SetAward(Award(78)) -- Destroyed the Hive and Saved Enroth
    evt.EnterHouse(0)
end, "Exit")

RegisterEvent(100, "Legacy event 100", function()
    if IsQBitSet(QBit(1204)) then -- NPC
        evt.SetDoorState(28, DoorAction.Open)
        evt.SetDoorState(30, DoorAction.Close)
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(52, DoorAction.Open)
        evt.SetDoorState(53, DoorAction.Close)
    end
end)

