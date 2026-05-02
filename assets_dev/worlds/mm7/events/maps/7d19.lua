-- Grand Temple of the Moon
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1},
    onLeave = {2},
    openedChestIds = {
    [17] = {6},
    [176] = {1},
    [177] = {2},
    [178] = {3},
    [179] = {4},
    [180] = {5},
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
    textureNames = {"t2bedsht"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    SetValue(MapVar(2), 1)
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(2, "Legacy event 2", function()
    local function Step_1()
        evt.ForPlayer(Players.All)
        return 2
    end
    local function Step_2()
        if HasItem(1143) then return 4 end -- Telekinesis
        return 3
    end
    local function Step_3()
        return nil
    end
    local function Step_4()
        RemoveItem(1143) -- Telekinesis
        return 5
    end
    local function Step_5()
        return 2
    end
    local step = 1
    while step ~= nil do
        if step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        else
            step = nil
        end
    end
end)

RegisterEvent(3, "Legacy event 3", function()
    evt.SetDoorState(6, DoorAction.Open)
end)

RegisterEvent(4, "Door", function()
    evt.SetDoorState(3, DoorAction.Open)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(7, DoorAction.Open)
end, "Door")

RegisterEvent(6, "Legacy event 6", function()
    if IsAtLeast(MapVar(2), 2) then return end
    evt.SetDoorState(8, DoorAction.Open)
    evt.SetDoorState(9, DoorAction.Open)
end)

RegisterEvent(7, "Door", function()
    evt.SetDoorState(10, DoorAction.Open)
    evt.SetDoorState(11, DoorAction.Open)
end, "Door")

RegisterEvent(8, "Legacy event 8", function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Close)
end)

RegisterEvent(9, "Door", function()
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Open)
end, "Door")

RegisterEvent(10, "Legacy event 10", function()
    evt.SetDoorState(14, DoorAction.Open)
end)

RegisterEvent(11, "Switch", function()
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(28, DoorAction.Open)
end, "Switch")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(17, DoorAction.Open)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Legacy event 16", function()
    evt.SetDoorState(24, DoorAction.Open)
    evt.SetDoorState(25, DoorAction.Open)
end)

RegisterEvent(17, "Drawer", function()
    evt.SetDoorState(26, DoorAction.Open)
    evt.OpenChest(6)
end, "Drawer")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Button", function()
    evt.SetDoorState(28, DoorAction.Close)
    evt.SetDoorState(15, DoorAction.Open)
end, "Button")

RegisterEvent(20, "Legacy event 20", function()
    AddValue(InventoryItem(1143), 1143) -- Telekinesis
    evt.SetDoorState(29, DoorAction.Open)
end)

RegisterEvent(21, "Door", function()
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(22, "Legacy event 22", function()
    evt.SetDoorState(4, DoorAction.Open)
    evt.SetDoorState(5, DoorAction.Open)
end)

RegisterEvent(23, "Legacy event 23", function()
    evt.SetDoorState(1, DoorAction.Open)
    evt.SetDoorState(2, DoorAction.Open)
end)

RegisterEvent(24, "Door", function()
    evt.SetDoorState(51, DoorAction.Open)
    evt.SetDoorState(50, DoorAction.Open)
end, "Door")

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(52, DoorAction.Open)
end)

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Cabinet", function()
    evt.OpenChest(2)
end, "Cabinet")

RegisterEvent(178, "Cabinet", function()
    evt.OpenChest(3)
end, "Cabinet")

RegisterEvent(179, "Cabinet", function()
    evt.OpenChest(4)
end, "Cabinet")

RegisterEvent(180, "Chest", function()
    evt.OpenChest(5)
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
end, "Bookcase")

RegisterEvent(376, "Altar", function()
    if IsQBitSet(QBit(574)) then return end -- Purified the Altar of Evil. Priest of Light promo quest.
    if IsQBitSet(QBit(554)) then -- Purify the Altar of Evil in the Temple of the Moon on Evenmorn Isle then return to Rebecca Devine in Celeste.
        evt.SetTexture(20, "t2bedsht")
        evt.ForPlayer(Players.All)
        SetQBit(QBit(574)) -- Purified the Altar of Evil. Priest of Light promo quest.
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        evt.StatusText("You have Purified the Altar")
    end
end, "Altar")

RegisterEvent(451, "Legacy event 451", function()
    if not IsAtLeast(MapVar(2), 2) then
        SetValue(MapVar(2), 2)
        evt.SetFacetBit(1, FacetBits.Untouchable, 1)
        evt.SetDoorState(30, DoorAction.Open)
        return
    end
    SetValue(MapVar(2), 1)
    evt.SetFacetBit(1, FacetBits.Untouchable, 0)
    evt.SetDoorState(30, DoorAction.Close)
end)

RegisterEvent(501, "Leave the Grand Temple of the Moon", function()
    evt.ForPlayer(Players.All)
    RemoveItem(1143) -- Telekinesis
    evt.MoveToMap(8472, -3176, 32, 1408, 0, 0, 0, 0, "out09.odm")
end, "Leave the Grand Temple of the Moon")

