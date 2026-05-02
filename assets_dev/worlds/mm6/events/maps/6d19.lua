-- Agar's Laboratory
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [18] = {0},
    [19] = {1},
    [20] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {32},
    timers = {
    { eventId = 21, repeating = true, intervalGameMinutes = 2.5, remainingGameMinutes = 2.5 },
    },
})

RegisterEvent(2, "Switch", function()
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Switch")

RegisterEvent(3, "Switch", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Switch")

RegisterEvent(4, "Switch", function()
    SetValue(MapVar(3), 1)
    evt.SetDoorState(4, DoorAction.Close)
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetDoorState(6, DoorAction.Close)
    evt.FaceExpression(39)
    if IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(18, DoorAction.Close)
    end
end, "Switch")

RegisterEvent(7, "Switch", function()
    SetValue(MapVar(2), 1)
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Close)
    evt.FaceExpression(39)
    if IsAtLeast(MapVar(3), 1) then
        evt.SetDoorState(18, DoorAction.Close)
    end
end, "Switch")

RegisterEvent(10, "Switch", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Close)
    evt.FaceExpression(48)
end, "Switch")

RegisterEvent(13, "Legacy event 13", function()
    if IsAtLeast(MapVar(21), 1) then return end
    evt.StatusText("Uh oh....")
    evt.SetDoorState(13, DoorAction.Close)
    AddValue(MapVar(21), 1)
end)

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Trigger)
end, "Door")

RegisterEvent(15, "Switch", function()
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(3, DoorAction.Close)
end, "Switch")

RegisterEvent(16, "Legacy event 16", function()
    evt.SetDoorState(16, DoorAction.Close)
end)

RegisterNoOpEvent(17, "Legacy event 17")

RegisterEvent(18, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(19, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(20, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(21, "Legacy event 21", function()
    evt.CastSpell(32, 7, 3, -2048, 9712, -2282, -2048, 9050, -2282) -- Ice Blast
end)

RegisterEvent(25, "Chandelier", function()
    if IsAtLeast(MapVar(6), 1) then return end
    SetValue(MapVar(6), 1)
    AddValue(InventoryItem(2056), 2056) -- Diamond
end, "Chandelier")

RegisterEvent(26, "Chandelier", function()
    if IsAtLeast(MapVar(7), 1) then return end
    SetValue(MapVar(7), 1)
    AddValue(InventoryItem(2056), 2056) -- Diamond
end, "Chandelier")

RegisterEvent(27, "Chandelier", function()
    if IsAtLeast(MapVar(8), 1) then return end
    SetValue(MapVar(8), 1)
    AddValue(InventoryItem(2056), 2056) -- Diamond
end, "Chandelier")

RegisterEvent(30, "Legacy event 30", function()
    evt.SetDoorState(16, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(31, "Switch", function()
    evt.SetDoorState(15, DoorAction.Open)
    evt.SetDoorState(3, DoorAction.Open)
end, "Switch")

RegisterEvent(35, "Cauldron", function()
    evt.ForPlayer(Players.Current)
    SetValue(Asleep, 0)
    if not IsAtLeast(Asleep, 0) then
        SetValue(Eradicated, 0)
        return
    end
    AddValue(BaseIntellect, 50)
    SetPlayerBit(PlayerBit(60))
    evt.StatusText("+50 Intellect permanent.")
end, "Cauldron")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(7762, 16306, 449, 1664, 0, 0, 0, 0, "outb1.odm")
end, "Exit")

