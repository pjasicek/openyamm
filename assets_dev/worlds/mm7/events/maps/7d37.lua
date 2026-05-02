-- The Haunted Mansion
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {2},
    openedChestIds = {
    [177] = {1},
    [178] = {2},
    [179] = {3},
    [180] = {4},
    [181] = {5},
    [182] = {6},
    [183] = {7},
    [184] = {8},
    [185] = {9},
    [186] = {10},
    [187] = {11},
    [188] = {13},
    [189] = {14},
    [190] = {15},
    [191] = {16},
    [192] = {17},
    [193] = {18},
    [194] = {19},
    [195] = {0},
    },
    textureNames = {"t2bs"},
    spriteNames = {},
    castSpellIds = {2},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(2, "Legacy event 2", function()
    if evt.CheckMonstersKilled(ActorKillCheck.Any, 51, 0, false) then -- any actor; all matching actors defeated
        evt.ForPlayer(Players.All)
        SetQBit(QBit(652)) -- Cleaned out the haunted mansion (Cavalier promo)
    end
end)

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
    evt.SetDoorState(4, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
    evt.SetDoorState(8, DoorAction.Open)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(10, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(12, DoorAction.Open)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(13, DoorAction.Open)
    evt.SetDoorState(14, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(15, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(21, DoorAction.Open)
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(23, DoorAction.Trigger)
    evt.CastSpell(2, 20, 3, 0, 3488, 576, 0, 2588, 576) -- Fire Bolt
end, "Door")

RegisterEvent(177, "Cabinet", function()
    evt.OpenChest(1)
end, "Cabinet")

RegisterEvent(178, "Cabinet", function()
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(179, "Cabinet", function()
    evt.OpenChest(3)
end, "Cabinet")

RegisterEvent(180, "Cabinet", function()
    evt.OpenChest(4)
end, "Cabinet")

RegisterEvent(181, "Cabinet", function()
    evt.OpenChest(5)
end, "Cabinet")

RegisterEvent(182, "Cabinet", function()
    evt.OpenChest(6)
end, "Cabinet")

RegisterEvent(183, "Cabinet", function()
    evt.OpenChest(7)
end, "Cabinet")

RegisterEvent(184, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(185, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(186, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(187, "Chest", function()
    evt.OpenChest(11)
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

RegisterEvent(196, "Bookcase", function()
    if IsAtLeast(MapVar(51), 1) then return end
    local randomStep = PickRandomOption(196, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(196, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(196, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(51), 1)
    end
end, "Bookcase")

RegisterEvent(197, "Bookcase", function()
    if IsAtLeast(MapVar(52), 1) then return end
    local randomStep = PickRandomOption(197, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(197, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(197, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(52), 1)
    end
end, "Bookcase")

RegisterEvent(198, "Bookcase", function()
    if IsAtLeast(MapVar(53), 1) then return end
    local randomStep = PickRandomOption(198, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(198, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(53), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(198, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(198, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(53), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(53), 1)
    end
end, "Bookcase")

RegisterEvent(199, "Bookcase", function()
    if IsAtLeast(MapVar(54), 1) then return end
    local randomStep = PickRandomOption(199, 2, {2, 2, 2, 4, 15, 18})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        local randomStep = PickRandomOption(199, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(54), 1)
        end
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(199, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(1203), 1203) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(1214), 1214) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(1216), 1216) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(1281), 1281) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(1269), 1269) -- Heal
        end
        local randomStep = PickRandomOption(199, 15, {15, 15, 15, 15, 18, 18})
        if randomStep == 15 then
            AddValue(MapVar(54), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(54), 1)
    end
end, "Bookcase")

RegisterEvent(200, "Bookcase", function()
    evt.StatusText("There are no items that interest you")
end, "Bookcase")

RegisterEvent(376, "Portrait", function()
    if IsQBitSet(QBit(778)) then return end -- Took Angel Painting
    evt.SetTexture(15, "t2bs")
    AddValue(InventoryItem(1423), 1423) -- Angel Statue Painting
    SetQBit(QBit(778)) -- Took Angel Painting
end, "Portrait")

RegisterEvent(501, "Leave the Haunted Mansion", function()
    evt.MoveToMap(-19207, 12339, 33, 1536, 0, 0, 0, 0, "out11.odm")
end, "Leave the Haunted Mansion")

