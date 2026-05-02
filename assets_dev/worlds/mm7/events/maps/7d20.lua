-- The Mercenary Guild
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {},
    openedChestIds = {
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
    [181] = {6},
    [182] = {7},
    [183] = {8},
    [184] = {9},
    [185] = {10},
    [186] = {11},
    [187] = {12},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {24, 39},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(3, DoorAction.Close)
end)

RegisterEvent(4, "Legacy event 4", function()
    evt.SetDoorState(4, DoorAction.Open)
end)

RegisterEvent(5, "Legacy event 5", function()
    evt.SetDoorState(4, DoorAction.Close)
end)

RegisterEvent(6, "Legacy event 6", function()
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(7, "Legacy event 7", function()
    evt.SetDoorState(5, DoorAction.Close)
end)

RegisterEvent(8, "Legacy event 8", function()
    evt.SetDoorState(6, DoorAction.Open)
end)

RegisterEvent(9, "Legacy event 9", function()
    evt.SetDoorState(6, DoorAction.Close)
end)

RegisterEvent(10, "Legacy event 10", function()
    evt.SetDoorState(7, DoorAction.Trigger)
end)

RegisterEvent(11, "Legacy event 11", function()
    evt.SetDoorState(7, DoorAction.Close)
end)

RegisterEvent(12, "Legacy event 12", function()
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end)

RegisterEvent(13, "Legacy event 13", function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Close)
end)

RegisterEvent(14, "Legacy event 14", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end)

RegisterEvent(15, "Legacy event 15", function()
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Close)
end)

RegisterEvent(16, "Bookcase", function()
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(37, DoorAction.Open)
end, "Bookcase")

RegisterEvent(17, "Legacy event 17", function()
    evt.SetDoorState(12, DoorAction.Close)
    evt.SetDoorState(37, DoorAction.Close)
end)

RegisterEvent(18, "Legacy event 18", function()
    evt.SetDoorState(2, DoorAction.Open)
    evt.SetDoorState(1, DoorAction.Open)
end)

RegisterEvent(19, "Legacy event 19", function()
    evt.SetDoorState(3, DoorAction.Open)
end)

RegisterEvent(20, "Legacy event 20", function()
    evt.SetDoorState(17, DoorAction.Open)
    evt.SetDoorState(18, DoorAction.Open)
end)

RegisterEvent(21, "Legacy event 21", function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Close)
end)

RegisterEvent(22, "Bookcase", function()
    evt.SetDoorState(23, DoorAction.Open)
    evt.SetDoorState(24, DoorAction.Open)
end, "Bookcase")

RegisterEvent(23, "Legacy event 23", function()
    evt.SetDoorState(25, DoorAction.Open)
    evt.SetDoorState(26, DoorAction.Open)
end)

RegisterEvent(24, "Legacy event 24", function()
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
end)

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(27, DoorAction.Open)
    evt.SetDoorState(28, DoorAction.Open)
    evt.CastSpell(39, 7, 4, -1136, 4480, 29, 112, 4480, 160) -- Blades
end)

RegisterEvent(26, "Legacy event 26", function()
    evt.SetDoorState(27, DoorAction.Close)
    evt.SetDoorState(28, DoorAction.Close)
end)

RegisterEvent(27, "Legacy event 27", function()
    evt.SetDoorState(29, DoorAction.Open)
    evt.SetDoorState(30, DoorAction.Open)
end)

RegisterEvent(28, "Legacy event 28", function()
    evt.SetDoorState(29, DoorAction.Close)
    evt.SetDoorState(30, DoorAction.Close)
end)

RegisterEvent(29, "Legacy event 29", function()
    evt.SetDoorState(31, DoorAction.Open)
end)

RegisterEvent(30, "Legacy event 30", function()
    evt.SetDoorState(31, DoorAction.Close)
end)

RegisterEvent(31, "Legacy event 31", function()
    evt.SetDoorState(32, DoorAction.Open)
end)

RegisterEvent(32, "Legacy event 32", function()
    evt.SetDoorState(32, DoorAction.Close)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    if IsQBitSet(QBit(729)) then return end -- Heart of Wood - I lost it
    evt.OpenChest(3)
    SetQBit(QBit(729)) -- Heart of Wood - I lost it
end, "Chest")

RegisterEvent(179, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(181, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(182, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(183, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(188, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(189, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(190, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(191, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(192, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(193, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(194, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(195, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(196, "Wine Rack", function()
    if IsAtLeast(MapVar(6), 2) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 12, 12, 13, 14})
    if randomStep == 2 then
        local randomStep = PickRandomOption(196, 3, {3, 5, 7, 9, 11, 12})
        if randomStep == 3 then
            AddValue(InventoryItem(1025), 1025) -- _potion/reagent
        elseif randomStep == 5 then
            AddValue(InventoryItem(1029), 1029) -- _potion/reagent
        elseif randomStep == 7 then
            AddValue(InventoryItem(1030), 1030) -- _potion/reagent
        elseif randomStep == 9 then
            AddValue(InventoryItem(1024), 1024) -- _potion/reagent
        elseif randomStep == 11 then
            AddValue(InventoryItem(1040), 1040) -- _potion/reagent
        end
        local randomStep = PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14})
        if randomStep == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 12 then
        local randomStep = PickRandomOption(196, 13, {13, 13, 13, 13, 14, 14})
        if randomStep == 13 then
            AddValue(MapVar(6), 1)
        end
    elseif randomStep == 13 then
        AddValue(MapVar(6), 1)
    end
end, "Wine Rack")

RegisterEvent(197, "Legacy event 197", function()
    evt.SetDoorState(19, DoorAction.Trigger)
end)

RegisterEvent(198, "Legacy event 198", function()
    evt.SetDoorState(20, DoorAction.Trigger)
end)

RegisterEvent(199, "Legacy event 199", function()
    evt.SetDoorState(21, DoorAction.Trigger)
end)

RegisterEvent(200, "Legacy event 200", function()
    evt.SetDoorState(22, DoorAction.Trigger)
end)

RegisterEvent(451, "Legacy event 451", function()
    evt.CastSpell(24, 2, 4, 2240, 4336, 215, 2240, 4336, -64) -- Poison Spray
    evt.CastSpell(24, 2, 4, 2464, 4032, 215, 2464, 4336, -64) -- Poison Spray
end)

RegisterEvent(452, "Bookcase", function()
    evt.StatusText("You see nothing of interest")
end, "Bookcase")

RegisterEvent(501, "Leave the Mercenary Guild", function()
    evt.MoveToMap(17920, 16803, 3072, 1536, 0, 0, 0, 0, "7out13.odm")
end, "Leave the Mercenary Guild")

