-- Dragoons' Keep
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {42},
    onLeave = {},
    openedChestIds = {
    [26] = {1},
    [27] = {2},
    [28] = {3},
    [29] = {10, 11},
    [34] = {4},
    [35] = {5},
    [36] = {6},
    [37] = {7},
    [38] = {8},
    [39] = {9},
    },
    textureNames = {},
    spriteNames = {"torchnf"},
    castSpellIds = {},
    timers = {
    { eventId = 41, repeating = true, intervalGameMinutes = 7.5, remainingGameMinutes = 7.5 },
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

RegisterEvent(9, "Lever", function()
    evt.SetDoorState(9, DoorAction.Trigger)
    evt.SetDoorState(28, DoorAction.Trigger)
end, "Lever")

RegisterEvent(10, "Lever", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(29, DoorAction.Trigger)
end, "Lever")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Legacy event 13", function()
    evt.SetDoorState(13, DoorAction.Close)
end)

RegisterEvent(14, "Switch", function()
    evt.SetDoorState(14, DoorAction.Trigger)
    evt.SetDoorState(15, DoorAction.Trigger)
end, "Switch")

RegisterEvent(16, "Switch", function()
    evt.SetDoorState(16, DoorAction.Trigger)
    evt.SetDoorState(17, DoorAction.Trigger)
end, "Switch")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(24, DoorAction.Close)
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Door")

RegisterEvent(26, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(27, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(28, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(29, "Chest", function()
    if not IsAtLeast(MapVar(5), 1) then
        if not IsQBitSet(QBit(1028)) then -- 4 D10, given when you retreive artifact from chest
            SetValue(MapVar(5), 1)
            SetQBit(QBit(1028)) -- 4 D10, given when you retreive artifact from chest
            evt.OpenChest(10)
            return
        end
        evt.OpenChest(11)
    end
    SetValue(MapVar(5), 1)
    SetQBit(QBit(1028)) -- 4 D10, given when you retreive artifact from chest
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(30, "Lever", function()
    evt.SetDoorState(26, DoorAction.Trigger)
    if IsAtLeast(MapVar(2), 5) then return end
    evt.SummonMonsters(1, 1, 3, -2976, 2512, 0, 0, 0) -- encounter slot 1 "FighterChain" tier A, count 3, pos=(-2976, 2512, 0), actor group 0, no unique actor name
    AddValue(MapVar(2), 1)
end, "Lever")

RegisterEvent(31, "Lever", function()
    evt.SetDoorState(27, DoorAction.Trigger)
    if IsAtLeast(MapVar(2), 5) then return end
    evt.SummonMonsters(1, 1, 3, -1111, 4424, 0, 0, 0) -- encounter slot 1 "FighterChain" tier A, count 3, pos=(-1111, 4424, 0), actor group 0, no unique actor name
    AddValue(MapVar(2), 1)
end, "Lever")

RegisterEvent(32, "Door", function()
    evt.StatusText("The Door won't budge.")
end, "Door")

RegisterEvent(33, "Exit", function()
    evt.MoveToMap(-4369, -18311, 161, 1536, 0, 0, 0, 0, "outc2.odm")
end, "Exit")

RegisterEvent(34, "Cabinet", function()
    evt.OpenChest(4)
end, "Cabinet")

RegisterEvent(35, "Cabinet", function()
    evt.OpenChest(5)
end, "Cabinet")

RegisterEvent(36, "Cabinet", function()
    evt.OpenChest(6)
end, "Cabinet")

RegisterEvent(37, "Cabinet", function()
    evt.OpenChest(7)
end, "Cabinet")

RegisterEvent(38, "Cabinet", function()
    evt.OpenChest(8)
end, "Cabinet")

RegisterEvent(39, "Cabinet", function()
    evt.OpenChest(9)
end, "Cabinet")

RegisterEvent(40, "Legacy event 40", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.SetDoorState(17, DoorAction.Open)
    evt.FaceExpression(5)
    evt.SetSprite(69, 1, "torchnf")
    evt.StatusText("Caught!")
    SetValue(MapVar(3), 1)
    SetValue(MapVar(4), 1)
end)

RegisterEvent(41, "Legacy event 41", function()
    if IsAtLeast(MapVar(6), 1) then
        return
    elseif IsAtLeast(MapVar(4), 1) then
        if not IsAtLeast(MapVar(4), 3) then
            evt.StatusText("Rats!")
            evt.SummonMonsters(2, 1, 2, -1216, 10992, -256, 0, 0) -- encounter slot 2 "BRat" tier A, count 2, pos=(-1216, 10992, -256), actor group 0, no unique actor name
            AddValue(MapVar(4), 1)
            return
        end
        evt.StatusText("Are those footsteps?")
        evt.SummonMonsters(1, 1, 3, -1152, 9840, -256, 0, 0) -- encounter slot 1 "FighterChain" tier A, count 3, pos=(-1152, 9840, -256), actor group 0, no unique actor name
        evt.SetDoorState(17, DoorAction.Close)
        SetValue(MapVar(6), 1)
    else
        return
    end
end)

RegisterEvent(42, "Legacy event 42", function()
    if IsQBitSet(QBit(1028)) then -- 4 D10, given when you retreive artifact from chest
        SetValue(MapVar(5), 1)
    end
end)

RegisterEvent(43, "Legacy event 43", function()
    if IsAtLeast(MapVar(7), 1) then return end
    evt.GiveItem(5, 23)
    SetValue(MapVar(7), 1)
end)

