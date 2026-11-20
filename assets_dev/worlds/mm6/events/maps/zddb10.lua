-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [12] = {0},
    [13] = {1},
    },
    contextActions = {
    [1] = { kind = "use_switch", source = "title" },
    [2] = { kind = "use_switch", source = "title" },
    [3] = { kind = "generic_event", source = "opcode" },
    [4] = { kind = "open_door", source = "title" },
    [6] = { kind = "use_switch", source = "title" },
    [9] = { kind = "generic_event", source = "opcode" },
    [10] = { kind = "generic_event", source = "opcode" },
    [11] = { kind = "generic_event", source = "opcode" },
    [12] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [13] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [14] = { kind = "open_door", source = "opcode" },
    [19] = { kind = "generic_event", source = "opcode" },
    [20] = { kind = "generic_event", source = "opcode" },
    [21] = { kind = "press_button", source = "title" },
    [22] = { kind = "press_button", source = "title" },
    [23] = { kind = "press_button", source = "title" },
    [25] = { kind = "generic_event", source = "opcode" },
    [26] = { kind = "generic_event", source = "opcode" },
    [27] = { kind = "generic_event", source = "opcode" },
    [28] = { kind = "generic_event", source = "opcode" },
    [29] = { kind = "generic_event", source = "opcode" },
    [30] = { kind = "generic_event", source = "opcode" },
    [31] = { kind = "generic_event", source = "opcode" },
    [32] = { kind = "generic_event", source = "opcode" },
    [33] = { kind = "generic_event", source = "opcode" },
    [34] = { kind = "generic_event", source = "opcode" },
    [35] = { kind = "generic_event", source = "opcode" },
    [37] = { kind = "teleport", source = "heuristic" },
    [38] = { kind = "open_door", source = "title" },
    [39] = { kind = "generic_event", source = "opcode" },
    [40] = { kind = "generic_event", source = "opcode" },
    [41] = { kind = "generic_event", source = "opcode" },
    [42] = { kind = "open_door", source = "title" },
    [43] = { kind = "open_door", source = "title" },
    },
    textureNames = {"d8s2on"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Switch.", function()
    evt.StatusText("With some muscle you move the switch down.")
    evt.SetDoorState(1, DoorAction.Trigger)
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Switch.")

RegisterEvent(2, "Switch.", function()
    evt.StatusText("With some muscle you move the switch down.")
    evt.SetDoorState(2, DoorAction.Trigger)
    evt.SetDoorState(4, DoorAction.Trigger)
end, "Switch.")

RegisterEvent(3, "Crates.", function()
    evt.StatusText("The crates are all empty.")
end, "Crates.")

RegisterEvent(4, "Door.", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door.")

RegisterEvent(6, "Switch.", function()
    if IsAtLeast(MapVar(7), 1) then return end
    evt.StatusText("You flip the switch and hear grating off in the distance.")
    evt.SetTexture(-1392, "d8s2on")
    evt.SetDoorState(6, DoorAction.Trigger)
    AddValue(MapVar(7), 1)
end, "Switch.")

RegisterEvent(8, "Old bones.", function()
    evt.DamagePlayer(Players.Current, const.Damage.Air, 10)
end, "Old bones.")

RegisterEvent(9, "Wall with missing bricks.", function(continueStep)
    if continueStep == 2 then
        AddValue(Insane, 1)
    end
    if continueStep ~= nil then return end
    evt.SetMessage("Something slimey moves behind this brick wall.")
    evt._PressAnyKey(9, 2)
end, "Wall with missing bricks.")

RegisterEvent(10, "Wall with missing bricks.", function()
    evt.StatusText("Something slimey moves behind this brick wall.")
    AddValue(Insane, 2)
end, "Wall with missing bricks.")

RegisterEvent(11, "Wall with missing bricks.", function()
    evt.StatusText("Something slimey moves behind this brick wall.")
    AddValue(Insane, 2)
end, "Wall with missing bricks.")

RegisterEvent(12, "Chest.", function()
    evt.OpenChest(0)
end, "Chest.")

RegisterEvent(13, "Chest.", function()
    evt.OpenChest(1)
end, "Chest.")

RegisterEvent(14, nil, function()
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Close)
end)

RegisterEvent(19, "Old bones.", function()
    evt.StatusText("You get a bad feeling from the bones.")
    evt.ForPlayer(6)
    AddValue(Asleep, 1)
end, "Old bones.")

RegisterEvent(20, "Iron Maiden", function()
    evt.StatusText("There's nothing but spikes in the Iron maiden.")
end, "Iron Maiden")

RegisterEvent(21, "Button", function()
    if not IsAtLeast(MapVar(21), 2) then
        evt.SetDoorState(10, DoorAction.Open)
        evt.SetDoorState(11, DoorAction.Open)
        evt.SetDoorState(9, DoorAction.Close)
        SetValue(MapVar(21), 0)
        SetValue(MapVar(20), 0)
        AddValue(MapVar(18), 1)
        return
    end
    evt.SetDoorState(9, DoorAction.Trigger)
    evt.SetDoorState(12, DoorAction.Trigger)
end, "Button")

RegisterEvent(22, "Button", function()
    if not IsAtLeast(MapVar(18), 1) then
        if not IsAtLeast(MapVar(20), 1) then
            AddValue(MapVar(21), 1)
            evt.SetDoorState(10, DoorAction.Close)
            return
        end
    end
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Open)
    SetValue(MapVar(18), 0)
    SetValue(MapVar(20), 0)
end, "Button")

RegisterEvent(23, "Button", function()
    if not IsAtLeast(MapVar(21), 1) then
        evt.SetDoorState(9, DoorAction.Open)
        evt.SetDoorState(10, DoorAction.Open)
        evt.SetDoorState(11, DoorAction.Close)
        AddValue(MapVar(20), 1)
        SetValue(MapVar(21), 0)
        SetValue(MapVar(18), 0)
        return
    end
    AddValue(MapVar(21), 1)
    evt.SetDoorState(11, DoorAction.Close)
end, "Button")

RegisterEvent(25, "Burial niche", function()
    if IsAtLeast(MapVar(24), 1) then return end
    local randomStep = PickRandomOption(25, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(24), 1)
end, "Burial niche")

RegisterEvent(26, "Burial niche", function(continueStep)
    local function Step_0()
        if IsAtLeast(MapVar(25), 1) then return 15 end
        return 1
    end
    local function Step_1()
        return PickRandomOption(26, 1, {2, 5, 8, 12})
    end
    local function Step_2()
        evt.StatusText("You search the Burial niche and find some gold.")
        return 3
    end
    local function Step_3()
        AddValue(Gold, 300)
        return 4
    end
    local function Step_4()
        return 14
    end
    local function Step_5()
        evt.StatusText("The bones seems to charge with electricity !!.")
        return 6
    end
    local function Step_6()
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
        return 7
    end
    local function Step_7()
        return 14
    end
    local function Step_8()
        evt.StatusText("These are really old bones...really old.")
        return 9
    end
    local function Step_9()
        evt._PressAnyKey(26, 10)
        return nil
    end
    local function Step_10()
        AddValue(Age, 5)
        return 11
    end
    local function Step_11()
        return 14
    end
    local function Step_12()
        evt.StatusText("You gain knowledge from these ancient bones.")
        return 13
    end
    local function Step_13()
        AddValue(Experience, 400)
        return 14
    end
    local function Step_14()
        AddValue(MapVar(25), 1)
        return 15
    end
    local function Step_15()
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
        elseif step == 12 then
            step = Step_12()
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
end, "Burial niche")

RegisterEvent(27, "Burial niche", function()
    if IsAtLeast(MapVar(26), 1) then return end
    local randomStep = PickRandomOption(27, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(26), 1)
end, "Burial niche")

RegisterEvent(28, "Burial niche", function()
    if IsAtLeast(MapVar(27), 1) then return end
    local randomStep = PickRandomOption(28, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 800)
    end
    AddValue(MapVar(27), 1)
end, "Burial niche")

RegisterEvent(29, "Burial niche", function()
    if IsAtLeast(MapVar(28), 1) then return end
    local randomStep = PickRandomOption(29, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(28), 1)
end, "Burial niche")

RegisterEvent(30, "Burial niche", function()
    if IsAtLeast(MapVar(29), 1) then return end
    local randomStep = PickRandomOption(30, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(29), 1)
end, "Burial niche")

RegisterEvent(31, "Burial niche", function()
    if IsAtLeast(MapVar(30), 1) then return end
    local randomStep = PickRandomOption(31, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(30), 1)
end, "Burial niche")

RegisterEvent(32, "Burial niche", function()
    if IsAtLeast(MapVar(31), 1) then return end
    local randomStep = PickRandomOption(32, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 500)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 900)
    end
    AddValue(MapVar(31), 1)
end, "Burial niche")

RegisterEvent(33, "Burial niche", function()
    if IsAtLeast(MapVar(32), 1) then return end
    local randomStep = PickRandomOption(33, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 400)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(Players.Current, const.Damage.Fire, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(32), 1)
end, "Burial niche")

RegisterEvent(34, "Long dead adventurer.", function()
    if IsAtLeast(MapVar(33), 1) then return end
    evt.StatusText("You search the body and find some gold.")
    AddValue(Gold, 300)
    AddValue(MapVar(33), 1)
end, "Long dead adventurer.")

RegisterEvent(35, "Skeleton in a cage.", function()
    evt.StatusText("The skeleton grabs for you.")
    AddValue(Insane, 1)
end, "Skeleton in a cage.")

RegisterEvent(37, nil, function()
    evt.StatusText("A strange force reaches out of the wall and grabs you.")
    evt.MoveToMap(12416, 3200, -2304, 0, 0, 0, 0, 0)
end)

RegisterEvent(38, "Door.", function(continueStep)
    if continueStep == 2 then
    end
    if continueStep ~= nil then return end
    evt.StatusText("The door will not budge.")
    evt._PressAnyKey(38, 2)
end, "Door.")

RegisterEvent(39, "Sack", function()
    if IsAtLeast(MapVar(41), 1) then return end
    evt.StatusText("You find some half decent food in the sack.")
    AddValue(Food, 5)
    AddValue(MapVar(41), 1)
end, "Sack")

RegisterEvent(40, "Sack", function()
    if IsAtLeast(MapVar(42), 1) then return end
    evt.StatusText("You find some half decent food in the sack.")
    AddValue(Food, 5)
    AddValue(MapVar(42), 1)
end, "Sack")

RegisterEvent(41, "Sack", function()
    if IsAtLeast(MapVar(43), 1) then return end
    evt.StatusText("You find some half decent food in the sack.")
    AddValue(Food, 5)
    AddValue(MapVar(43), 1)
end, "Sack")

RegisterEvent(42, "Door.", function()
    evt.StatusText("The door will not budge.")
end, "Door.")

RegisterEvent(43, "Door.", function(continueStep)
    if continueStep == 2 then
    end
    if continueStep ~= nil then return end
    evt.SetMessage("A scrawled message on the brick reads   2=1  3=2  1=3")
    evt._PressAnyKey(43, 2)
end, "Door.")

