-- Tunnels to Eeofol
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

RegisterEvent(196, "Ore Vein", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(16), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(196, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
        return 5
    end
    local function Step_5()
        return 9
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        evt.StatusText("Cave In !")
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1492), 1492) -- Erudine-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(16), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(2, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(16), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
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
        elseif step == 11 then
            step = Step_11()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        else
            step = nil
        end
    end
end, "Ore Vein")

RegisterEvent(197, "Ore Vein", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(17), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(197, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
        return 5
    end
    local function Step_5()
        return 9
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        evt.StatusText("Cave In !")
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1492), 1492) -- Erudine-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(17), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(3, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(17), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
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
        elseif step == 11 then
            step = Step_11()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        else
            step = nil
        end
    end
end, "Ore Vein")

RegisterEvent(198, "Ore Vein", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(18), 1) then return 11 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(198, 1, {2, 4, 6, 8, 2, 2})
    end
    local function Step_2()
        AddValue(InventoryItem(1490), 1490) -- Phylt-laced ore
        return 3
    end
    local function Step_3()
        return 9
    end
    local function Step_4()
        AddValue(InventoryItem(1491), 1491) -- Kergar-laced ore
        return 5
    end
    local function Step_5()
        return 9
    end
    local function Step_6()
        evt.DamagePlayer(5, 0, 50)
        return 7
    end
    local function Step_7()
        evt.StatusText("Cave In !")
        return 8
    end
    local function Step_8()
        AddValue(InventoryItem(1492), 1492) -- Erudine-laced ore
        return 9
    end
    local function Step_9()
        SetValue(MapVar(18), 1)
        return 10
    end
    local function Step_10()
        evt.SetTexture(4, "cwb1")
        return 11
    end
    local function Step_11()
        return nil
    end
    local function Step_13()
        if IsAtLeast(MapVar(18), 1) then return 15 end
        return 14
    end
    local function Step_14()
        return 11
    end
    local function Step_15()
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
        elseif step == 11 then
            step = Step_11()
        elseif step == 13 then
            step = Step_13()
        elseif step == 14 then
            step = Step_14()
        elseif step == 15 then
            step = Step_15()
        else
            step = nil
        end
    end
end, "Ore Vein")

RegisterEvent(451, "Legacy event 451", function()
    evt.MoveToMap(1664, 6336, 1, 0, 0, 0, 0, 0)
end)

RegisterEvent(452, "Legacy event 452", function()
    evt.MoveToMap(992, 8544, -320, 0, 0, 0, 0, 0)
end)

RegisterEvent(501, "Leave the Cave", function()
    evt.MoveToMap(20890, -3119, 1, 896, 0, 0, 0, 0, "out12.odm")
end, "Leave the Cave")

RegisterEvent(502, "Leave the Cave", function()
    evt.MoveToMap(2324, 7371, 1644, 1428, 0, 0, 0, 0, "7d07.blv")
end, "Leave the Cave")

RegisterEvent(65535, "", function()
    return evt.map[196](13)
end)

RegisterEvent(65534, "", function()
    return evt.map[197](13)
end)

RegisterEvent(65533, "", function()
    return evt.map[198](13)
end)

