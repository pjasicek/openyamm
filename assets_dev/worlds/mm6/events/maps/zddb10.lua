-- pending
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [12] = {0},
    [13] = {1},
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
    evt.SetTexture(1392, "d8s2on")
    evt.SetDoorState(6, DoorAction.Trigger)
    AddValue(MapVar(7), 1)
end, "Switch.")

RegisterEvent(8, "Old bones.", function()
    evt.DamagePlayer(7, 1, 10)
end, "Old bones.")

RegisterEvent(9, "Wall with missing bricks.", function()
    evt.SimpleMessage("Something slimey moves behind this brick wall.")
    AddValue(Insane, 1)
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

RegisterEvent(14, "Legacy event 14", function()
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
        evt.DamagePlayer(7, 0, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 11 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(24), 1)
end, "Burial niche")

RegisterEvent(26, "Burial niche", function()
    if IsAtLeast(MapVar(25), 1) then return end
    local randomStep = PickRandomOption(26, 2, {2, 5, 8, 12})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(7, 0, 10)
    elseif randomStep == 8 then
        evt.StatusText("These are really old bones...really old.")
        AddValue(Age, 5)
    elseif randomStep == 12 then
        evt.StatusText("You gain knowledge from these ancient bones.")
        AddValue(Experience, 400)
    end
    AddValue(MapVar(25), 1)
end, "Burial niche")

RegisterEvent(27, "Burial niche", function()
    if IsAtLeast(MapVar(26), 1) then return end
    local randomStep = PickRandomOption(27, 2, {2, 5, 8, 11})
    if randomStep == 2 then
        evt.StatusText("You search the Burial niche and find some gold.")
        AddValue(Gold, 300)
    elseif randomStep == 5 then
        evt.StatusText("The bones seems to charge with electricity !!.")
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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
        evt.DamagePlayer(7, 0, 10)
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

RegisterEvent(37, "Legacy event 37", function()
    evt.StatusText("A strange force reaches out of the wall and grabs you.")
    evt.MoveToMap(12416, 3200, -2304, 0, 0, 0, 0, 0)
end)

RegisterEvent(38, "Door.", function()
    evt.StatusText("The door will not budge.")
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

RegisterEvent(43, "Door.", function()
    evt.SimpleMessage("A scrawled message on the brick reads   2=1  3=2  1=3")
end, "Door.")

