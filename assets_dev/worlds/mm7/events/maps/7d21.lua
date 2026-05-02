-- White Cliff Cave
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {65535, 65534, 65533},
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
    textureNames = {"cwb1"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(3, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(176, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(177, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(178, "Chest", function()
    evt.OpenChest(3)
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

RegisterEvent(196, "Legacy event 196", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(16), 1) then return 10 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(196, 1, {2, 4, 6, 7, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 3
    end
    local function Step_3()
        return 8
    end
    local function Step_4()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 5
    end
    local function Step_5()
        return 8
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 8
    end
    local function Step_8()
        SetValue(MapVar(16), 1)
        return 9
    end
    local function Step_9()
        evt.SetTexture(2, "cwb1")
        return 10
    end
    local function Step_10()
        return nil
    end
    local function Step_12()
        if IsAtLeast(MapVar(16), 1) then return 14 end
        return 13
    end
    local function Step_13()
        return 10
    end
    local function Step_14()
        evt.SetTexture(2, "cwb1")
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        elseif step == 9 then
            step = Step_9()
        elseif step == 10 then
            step = Step_10()
        elseif step == 12 then
            step = Step_12()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        else
            step = nil
        end
    end
end)

RegisterEvent(197, "Legacy event 197", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(17), 1) then return 10 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(197, 1, {2, 4, 6, 7, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 3
    end
    local function Step_3()
        return 8
    end
    local function Step_4()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 5
    end
    local function Step_5()
        return 8
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 8
    end
    local function Step_8()
        SetValue(MapVar(17), 1)
        return 9
    end
    local function Step_9()
        evt.SetTexture(3, "cwb1")
        return 10
    end
    local function Step_10()
        return nil
    end
    local function Step_12()
        if IsAtLeast(MapVar(17), 1) then return 14 end
        return 13
    end
    local function Step_13()
        return 10
    end
    local function Step_14()
        evt.SetTexture(3, "cwb1")
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        elseif step == 9 then
            step = Step_9()
        elseif step == 10 then
            step = Step_10()
        elseif step == 12 then
            step = Step_12()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        else
            step = nil
        end
    end
end)

RegisterEvent(198, "Legacy event 198", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(18), 1) then return 10 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(198, 1, {2, 4, 6, 7, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1488), 1488) -- Iron-laced ore
        return 3
    end
    local function Step_3()
        return 8
    end
    local function Step_4()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 5
    end
    local function Step_5()
        return 8
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        AddValue(InventoryItem(1489), 1489) -- Siertal-laced ore
        return 8
    end
    local function Step_8()
        SetValue(MapVar(18), 1)
        return 9
    end
    local function Step_9()
        evt.SetTexture(4, "cwb1")
        return 10
    end
    local function Step_10()
        return nil
    end
    local function Step_12()
        if IsAtLeast(MapVar(18), 1) then return 14 end
        return 13
    end
    local function Step_13()
        return 10
    end
    local function Step_14()
        evt.SetTexture(4, "cwb1")
        return nil
    end
    local step = continueStep or 0
    while step ~= nil do
        if step == 0 then
            step = Step_0()
        elseif step == 1 then
            step = Step_1()
        elseif step == 2 then
            step = Step_2()
        elseif step == 3 then
            step = Step_3()
        elseif step == 4 then
            step = Step_4()
        elseif step == 5 then
            step = Step_5()
        elseif step == 6 then
            step = Step_6()
        elseif step == 7 then
            step = Step_7()
        elseif step == 8 then
            step = Step_8()
        elseif step == 9 then
            step = Step_9()
        elseif step == 10 then
            step = Step_10()
        elseif step == 12 then
            step = Step_12()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        else
            step = nil
        end
    end
end)

RegisterEvent(501, "Leave the White Cliff Caves", function()
    evt.MoveToMap(9686, -17990, 702, 1024, 0, 0, 0, 0, "7out02.odm")
end, "Leave the White Cliff Caves")

RegisterEvent(65535, "", function()
    return evt.map[196](12)
end)

RegisterEvent(65534, "", function()
    return evt.map[197](12)
end)

RegisterEvent(65533, "", function()
    return evt.map[198](12)
end)

