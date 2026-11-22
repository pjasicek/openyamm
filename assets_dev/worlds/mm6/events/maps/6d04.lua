-- Hall of the Fire Lord
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [41] = {1},
    [42] = {2, 2, 12},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [46] = {6},
    [47] = {7},
    [48] = {8},
    [49] = {9},
    [53] = {10},
    [59] = {11},
    },
    contextActions = {
    [2] = { kind = "open_door", source = "title" },
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_door", source = "title" },
    [5] = { kind = "open_door", source = "title" },
    [6] = { kind = "open_door", source = "title" },
    [7] = { kind = "open_door", source = "title" },
    [8] = { kind = "open_door", source = "title" },
    [9] = { kind = "open_door", source = "title" },
    [10] = { kind = "open_door", source = "title" },
    [11] = { kind = "open_door", source = "title" },
    [12] = { kind = "open_door", source = "title" },
    [13] = { kind = "open_door", source = "title" },
    [14] = { kind = "open_door", source = "title" },
    [15] = { kind = "open_door", source = "title" },
    [16] = { kind = "open_door", source = "title" },
    [17] = { kind = "open_door", source = "title" },
    [18] = { kind = "open_door", source = "title" },
    [19] = { kind = "open_door", source = "title" },
    [20] = { kind = "open_door", source = "title" },
    [21] = { kind = "open_door", source = "title" },
    [22] = { kind = "open_door", source = "title" },
    [23] = { kind = "open_door", source = "title" },
    [25] = { kind = "open_door", source = "opcode" },
    [27] = { kind = "teleport", source = "heuristic" },
    [28] = { kind = "teleport", source = "heuristic" },
    [29] = { kind = "teleport", source = "heuristic" },
    [30] = { kind = "open_door", source = "title" },
    [31] = { kind = "open_door", source = "opcode" },
    [32] = { kind = "open_door", source = "opcode" },
    [33] = { kind = "open_door", source = "opcode" },
    [41] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [42] = { kind = "open_chest", source = "opcode", chestIds = {2, 12} },
    [43] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [44] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [45] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [46] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [47] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [48] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [49] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [50] = { kind = "secret_event", source = "heuristic", hidden = true },
    [51] = { kind = "leave_dungeon", source = "opcode", targetMap = "outd2.odm", targetName = "Bootleg Bay" },
    [52] = { kind = "open_door", source = "opcode" },
    [53] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [54] = { kind = "teleport", source = "heuristic" },
    [55] = { kind = "open_door", source = "title" },
    [58] = { kind = "teleport", source = "heuristic" },
    [59] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [60] = { kind = "open_door", source = "title" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {83},
    timers = {
    { eventId = 56, sourceEventId = 56, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 12, startMinute = 0, startSecond = 0 },
    { eventId = 57, sourceEventId = 57, triggerStep = 0, origin = "legacy", triggerKind = "long", scheduleKind = "daily", startHour = 12, startMinute = 0, startSecond = 0 },
    },
})

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
    if IsQBitSet(QBit(1095)) then -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    elseif IsAtLeast(MapVar(11), 1) then
        if not IsAtLeast(MapVar(21), 1) then
            evt.StatusText("All wards must be destroyed.")
            return
        end
        SetQBit(QBit(1095)) -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    elseif IsQBitSet(QBit(1065)) then -- Bruce
        if not HasItem(2102) then -- Amber
            evt.StatusText("The Door is warded.")
            return
        end
        RemoveItem(2102) -- Amber
        SetValue(MapVar(11), 1)
        if not IsAtLeast(MapVar(21), 1) then
            evt.StatusText("All wards must be destroyed.")
            return
        end
        SetQBit(QBit(1095)) -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    else
        evt.StatusText("The Door is warded.")
        return
    end
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

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Open)
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    if not IsQBitSet(QBit(1095)) then -- Walt
        if IsAtLeast(MapVar(21), 1) then
            if not IsAtLeast(MapVar(11), 1) then
                evt.StatusText("All wards must be destroyed.")
                return
            end
            SetQBit(QBit(1095)) -- Walt
            evt.SetDoorState(20, DoorAction.Close)
        elseif IsQBitSet(QBit(1065)) then -- Bruce
            if not HasItem(2102) then -- Amber
                evt.StatusText("The Door is warded.")
                return
            end
            RemoveItem(2102) -- Amber
            SetValue(MapVar(21), 1)
            if not IsAtLeast(MapVar(11), 1) then
                evt.StatusText("All wards must be destroyed.")
                return
            end
            SetQBit(QBit(1095)) -- Walt
            evt.SetDoorState(20, DoorAction.Close)
        else
            evt.StatusText("The Door is warded.")
            return
        end
        return
    end
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

RegisterEvent(25, nil, function()
    evt.SetDoorState(25, DoorAction.Trigger)
end)

RegisterEvent(27, "Stone Face", function()
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(player, const.Damage.Physical, 50)
            SetValue(MapVar(2), 1)
        end
    end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(28, nil, function()
    evt.MoveToMap(-2853, 1600, -2655, 1024, 0, 0, 0, 0)
end)

RegisterEvent(29, nil, function()
    evt.MoveToMap(2823, 1534, -2655, 45, 0, 0, 0, 0)
end)

RegisterEvent(30, "Door", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Door")

RegisterEvent(31, nil, function()
    evt.SetDoorState(30, DoorAction.Open)
end)

RegisterEvent(32, nil, function()
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
end)

RegisterEvent(33, nil, function()
    evt.SetDoorState(18, DoorAction.Open)
end)

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    if not IsAtLeast(MapVar(12), 1) then
        if IsQBitSet(QBit(1099)) then -- Lisa
            evt.OpenChest(12)
        elseif HasItem(2179) then -- Chest Key
            evt.OpenChest(2)
            RemoveItem(2179) -- Chest Key
            SetValue(MapVar(12), 1)
            SetQBit(QBit(1099)) -- Lisa
        else
            evt.StatusText("The chest is locked.")
        end
        return
    end
    evt.OpenChest(2)
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

RegisterEvent(46, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(47, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(48, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(50, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.CastSpell(83, 4, 1, 0, 0, 0, 0, 0, 0) -- Day of the Gods
    SetValue(MapVar(3), 1)
    evt.StatusText("Magically Refreshing!")
end)

RegisterEvent(51, "Exit", function()
    evt.MoveToMap(16387, -20005, 225, 512, 0, 0, 0, 6, "outd2.odm") -- Bootleg Bay
end, "Exit")

RegisterEvent(52, "Lord of Fire", function()
    evt.SetDoorState(51, DoorAction.Close)
    evt.SetDoorState(52, DoorAction.Close)
    SetQBit(QBit(1065)) -- Bruce
    evt.SpeakNPC(1083) -- Lord of Fire
end, "Lord of Fire")

RegisterEvent(53, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(54, "Stone Face", function()
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(player, const.Damage.Physical, 50)
            SetValue(MapVar(2), 1)
        end
    end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(55, DoorAction.Close)
end, "Door")

RegisterEvent(56, nil, function()
    SetValue(MapVar(3), 0)
end)

RegisterEvent(57, nil, function()
    SetValue(MapVar(3), 0)
end)

RegisterEvent(58, "Stone Face", function()
    for _, player in ipairs(PartyMembers()) do
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(player, const.Damage.Physical, 50)
            SetValue(MapVar(2), 1)
        end
    end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(59, "Bag", function()
    evt.OpenChest(11)
end, "Bag")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(58, DoorAction.Close)
end, "Door")

