-- The Dragon's Lair
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetDoorState(1, DoorAction.Open)
end)

RegisterEvent(101, "Legacy event 101", function()
    evt.MoveToMap(13839, 16367, 169, 1, 0, 0, 0, 0, "7out01.odm")
end)

RegisterEvent(201, "Legacy event 201", function()
    if IsAtLeast(MapVar(2), 1) then return end
    AddValue(InventoryItem(845), 845) -- Longbow
    SetValue(MapVar(2), 1)
end)

RegisterEvent(202, "Legacy event 202", function()
    if IsAtLeast(MapVar(3), 1) then return end
    AddValue(InventoryItem(1460), 1460) -- Contestant's Shield
    SetValue(MapVar(3), 1)
end)

