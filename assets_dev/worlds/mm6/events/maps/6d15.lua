-- Icewind Keep
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [20] = {0},
    [21] = {1},
    [22] = {2},
    [23] = {3},
    [24] = {4},
    [25] = {5, 7},
    [26] = {6},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "opcode" },
    [2] = { kind = "use_lever", source = "title" },
    [3] = { kind = "use_lever", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [13] = { kind = "use_lever", source = "title" },
    [14] = { kind = "open_door", source = "title" },
    [15] = { kind = "open_door", source = "title" },
    [18] = { kind = "open_door", source = "title" },
    [19] = { kind = "open_door", source = "title" },
    [20] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [21] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [22] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [23] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [24] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [25] = { kind = "open_chest", source = "opcode", chestIds = {5, 7} },
    [26] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [27] = { kind = "generic_event", source = "opcode" },
    [28] = { kind = "generic_event", source = "opcode" },
    [29] = { kind = "generic_event", source = "opcode" },
    [30] = { kind = "generic_event", source = "opcode" },
    [31] = { kind = "generic_event", source = "opcode" },
    [32] = { kind = "generic_event", source = "opcode" },
    [33] = { kind = "generic_event", source = "opcode" },
    [34] = { kind = "generic_event", source = "opcode" },
    [35] = { kind = "open_door", source = "title" },
    [50] = { kind = "leave_dungeon", source = "opcode", targetMap = "outc1.odm", targetName = "Frozen Highlands" },
    [51] = { kind = "secret_event", source = "heuristic", hidden = true },
    [52] = { kind = "secret_event", source = "heuristic", hidden = true },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(2, "Lever", function()
    evt.StatusText("Something rumbles off in the distance.")
    evt.FaceExpression(30)
    evt.SetDoorState(2, DoorAction.Trigger)
    evt.SetDoorState(16, DoorAction.Trigger)
end, "Lever")

RegisterEvent(3, "Lever", function()
    evt.StatusText("Something rumbles off in the distance.")
    evt.SetDoorState(3, DoorAction.Trigger)
    evt.SetDoorState(17, DoorAction.Trigger)
end, "Lever")

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

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Lever", function()
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end, "Lever")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(21, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(22, "Cabinet", function()
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(23, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(24, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(25, "Chest", function()
    if not IsAtLeast(MapVar(11), 1) then
        if not IsQBitSet(QBit(1049)) then -- 25 D15, Given to find merchants White pearl
            evt.OpenChest(5)
            AddValue(MapVar(11), 1)
            SetQBit(QBit(1049)) -- 25 D15, Given to find merchants White pearl
            SetQBit(QBit(1213)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(7)
        return
    end
    evt.OpenChest(5)
    AddValue(MapVar(11), 1)
    SetQBit(QBit(1049)) -- 25 D15, Given to find merchants White pearl
    SetQBit(QBit(1213)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(26, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(27, "Bed", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(2), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(28, "Bed", function()
    if not IsAtLeast(MapVar(3), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(3), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(29, "Bed", function()
    if not IsAtLeast(MapVar(4), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(4), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(30, "Bed", function()
    if not IsAtLeast(MapVar(5), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(5), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(31, "Bed", function()
    if not IsAtLeast(MapVar(6), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(6), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(32, "Bed", function()
    if not IsAtLeast(MapVar(7), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(Gold, 2000)
        AddValue(MapVar(7), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(33, "Bed", function()
    if not IsAtLeast(MapVar(8), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(InventoryItem(1631), 1631) -- Heavy Poleaxe
        AddValue(MapVar(8), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(34, "Bed", function()
    if not IsAtLeast(MapVar(9), 1) then
        evt.StatusText("You find something around the bed.")
        AddValue(InventoryItem(1613), 1613) -- Mighty Broadsword
        AddValue(MapVar(9), 1)
        return
    end
    evt.StatusText("The bed(s) are empty.")
end, "Bed")

RegisterEvent(35, "Gate", function()
    evt.StatusText("The gate will not budge.")
end, "Gate")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(-18638, -5133, 64, 0, 0, 0, 0, 6, "outc1.odm") -- Frozen Highlands
end, "Exit")

RegisterEvent(51, nil, function()
    if IsAtLeast(MapVar(21), 1) then return end
    SetValue(MapVar(21), 1)
    evt.GiveItem(6, 35)
end)

RegisterEvent(52, nil, function()
    if IsAtLeast(MapVar(21), 1) then return end
    SetValue(MapVar(21), 1)
    evt.GiveItem(6, 35)
end)

