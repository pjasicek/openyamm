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
    textureNames = {"orair256", "sky_nit1", "sky_sns1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 15, repeating = false, targetHour = 21, intervalGameMinutes = 1260, remainingGameMinutes = 720 },
    { eventId = 16, repeating = false, targetHour = 88, intervalGameMinutes = 5280, remainingGameMinutes = 4740 },
    { eventId = 17, repeating = false, targetHour = 208, intervalGameMinutes = 12480, remainingGameMinutes = 11940 },
    { eventId = 18, repeating = false, targetHour = 244, intervalGameMinutes = 14640, remainingGameMinutes = 14100 },
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetDoorState(1, DoorAction.Close)
end)

RegisterEvent(2, "Legacy event 2", function()
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
    evt.MoveToMap(-7537, 4032, 97, 0, 0, 0, 0, 0, "outd2.odm")
end, "Exit")

RegisterEvent(15, "Legacy event 15", function()
    evt.SetLight(0, 0)
    evt.SetLight(1, 0)
    evt.SetTexture(79, "sky_nit1")
end)

RegisterEvent(16, "Legacy event 16", function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 1)
    evt.SetTexture(79, "orair256")
end)

RegisterEvent(17, "Legacy event 17", function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 0)
    evt.SetTexture(79, "sky_sns1")
end)

RegisterEvent(18, "Legacy event 18", function()
    evt.SetLight(0, 1)
    evt.SetLight(1, 0)
    evt.SetTexture(79, "sky_sns1")
end)

RegisterEvent(19, "Legacy event 19", function()
    if IsAtLeast(Hour, 2100) then
        evt.SetLight(0, 0)
        evt.SetLight(1, 0)
        evt.SetTexture(79, "sky_nit1")
        return
    elseif IsAtLeast(Hour, 2000) then
        evt.SetLight(0, 1)
        evt.SetLight(1, 0)
        evt.SetTexture(79, "sky_sns1")
        return
    elseif IsAtLeast(Hour, 600) then
        return
    elseif IsAtLeast(Hour, 500) then
        evt.SetLight(0, 1)
        evt.SetLight(1, 0)
        evt.SetTexture(79, "sky_sns1")
    else
        evt.SetLight(0, 0)
        evt.SetLight(1, 0)
        evt.SetTexture(79, "sky_nit1")
    end
end)

RegisterEvent(20, "Legacy event 20", function()
    if IsAtLeast(MapVar(2), 1) then return end
    SetValue(MapVar(2), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(21, "Legacy event 21", function()
    if IsAtLeast(MapVar(3), 1) then return end
    SetValue(MapVar(3), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(22, "Legacy event 22", function()
    if IsAtLeast(MapVar(4), 1) then return end
    SetValue(MapVar(4), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

RegisterEvent(23, "Legacy event 23", function()
    if IsAtLeast(MapVar(5), 1) then return end
    SetValue(MapVar(5), 1)
    AddValue(InventoryItem(1888), 1888) -- Sunray
end)

