-- Temple of the Sun
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {19},
    onLeave = {},
    openedChestIds = {
    [4] = {0},
    [5] = {1},
    [6] = {2},
    [7] = {3},
    [8] = {4},
    [9] = {5},
    [10] = {6},
    [11] = {7},
    [12] = {8},
    },
    contextActions = {
    [1] = { kind = "open_door", source = "opcode" },
    [2] = { kind = "open_door", source = "opcode" },
    [3] = { kind = "open_door", source = "title" },
    [4] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [5] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [6] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [7] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [8] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [9] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [10] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [11] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [12] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [14] = { kind = "leave_dungeon", source = "opcode", targetMap = "outd2.odm", targetName = "Bootleg Bay" },
    },
    textureNames = {"orair256", "sky_nit1", "sky_sns1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 15, sourceEventId = 15, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 21, startMinute = 0, startSecond = 0 },
    { eventId = 16, sourceEventId = 16, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 88, startMinute = 0, startSecond = 0 },
    { eventId = 17, sourceEventId = 17, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 208, startMinute = 0, startSecond = 0 },
    { eventId = 18, sourceEventId = 18, triggerStep = 0, origin = "legacy", triggerKind = "timer", scheduleKind = "daily", startHour = 244, startMinute = 0, startSecond = 0 },
    },
})

RegisterEvent(1, nil, function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(2, nil, function()
    evt.SetDoorState(2, DoorAction.Close)
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(5, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(6, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(7, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(8, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(9, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(10, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(11, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(12, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(13, "Cabinet", function()
    if not IsQBitSet(QBit(1075)) then -- 51 T4, Given when characters find Silver Chalice.
        SetQBit(QBit(1075)) -- 51 T4, Given when characters find Silver Chalice.
        AddValue(InventoryItem(2054), 2054) -- Sacred Chalice
        SetQBit(QBit(1212)) -- Quest item bits for seer
        return
    end
    if IsAtLeast(MapVar(6), 1) then return end
    evt.GiveItem(4, 23)
    evt.GiveItem(4, ItemType.Armor_)
    evt.GiveItem(4, 34)
    SetValue(MapVar(6), 1)
end, "Cabinet")

RegisterEvent(14, "Exit", function()
    evt.MoveToMap(-7537, 4032, 97, 0, 0, 0, 0, 0, "outd2.odm") -- Bootleg Bay
end, "Exit")

RegisterEvent(15, nil, function()
    evt.SetLight(0, 0)
    evt.SetLight(1, 0)
    evt.SetTexture(-45, "sky_nit1")
end)

RegisterEvent(16, nil, function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 1)
    evt.SetTexture(-45, "orair256")
end)

RegisterEvent(17, nil, function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 0)
    evt.SetTexture(-45, "sky_sns1")
end)

RegisterEvent(18, nil, function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 0)
    evt.SetTexture(-45, "sky_sns1")
end)

RegisterEvent(19, nil, function()
    if IsAtLeast(Hour, 2100) then
        evt.SetLight(0, 0)
        evt.SetLight(1, 0)
        evt.SetTexture(-45, "sky_nit1")
        return
    elseif IsAtLeast(Hour, 2000) then
        evt.SetLight(0, 1)
        evt.SetLight(1, 0)
        evt.SetTexture(-45, "sky_sns1")
        return
    elseif IsAtLeast(Hour, 600) then
        return
    elseif IsAtLeast(Hour, 500) then
        evt.SetLight(0, 1)
        evt.SetLight(1, 0)
        evt.SetTexture(-45, "sky_sns1")
    else
        evt.SetLight(0, 0)
        evt.SetLight(1, 0)
        evt.SetTexture(-45, "sky_nit1")
    end
end)

RegisterEvent(20, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(21, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(22, nil, function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(23, nil, function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

