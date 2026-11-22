-- The Dragon's Lair
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    contextActions = {
    [1] = { kind = "open_door", source = "opcode" },
    [101] = { kind = "leave_dungeon", source = "opcode", targetMap = "7out01.odm", targetName = "Emerald Island" },
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, nil, function()
    evt.SetDoorState(1, DoorAction.Open)
end)

RegisterEvent(101, nil, function()
    evt.MoveToMap(13839, 16367, 169, 1, 0, 0, 0, 4, "7out01.odm") -- Emerald Island
end)

RegisterEvent(201, nil, function()
    if IsAtLeast(MapVar(2), 1) then return end
    AddValue(InventoryItem(845), 845) -- Longbow
    SetValue(MapVar(2), 1)
end)

RegisterEvent(202, nil, function()
    if IsAtLeast(MapVar(3), 1) then return end
    AddValue(InventoryItem(1460), 1460) -- Contestant's Shield
    SetValue(MapVar(3), 1)
end)

