-- Hall of the Fire Lord
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [41] = {1},
    [42] = {2, 2, 12},
    [43] = {3},
    [44] = {4},
    [45] = {5},
    [46] = {6},
    [47] = {7},
    [48] = {8},
    [49] = {9},
    [53] = {10},
    [59] = {11},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {83},
    timers = {
    { eventId = 56, repeating = false, targetHour = 12, intervalGameMinutes = 720, remainingGameMinutes = 180 },
    },
})

RegisterEvent(2, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(3, "Door", function()
    evt.SetDoorState(3, DoorAction.Close)
end, "Door")

RegisterEvent(4, "Door", function()
    evt.SetDoorState(4, DoorAction.Close)
end, "Door")

RegisterEvent(5, "Door", function()
    evt.SetDoorState(5, DoorAction.Close)
end, "Door")

RegisterEvent(6, "Door", function()
    evt.SetDoorState(6, DoorAction.Close)
end, "Door")

RegisterEvent(7, "Door", function()
    evt.SetDoorState(7, DoorAction.Close)
end, "Door")

RegisterEvent(8, "Door", function()
    evt.SetDoorState(8, DoorAction.Close)
end, "Door")

RegisterEvent(9, "Door", function()
    evt.SetDoorState(9, DoorAction.Close)
end, "Door")

RegisterEvent(10, "Door", function()
    if IsQBitSet(QBit(1095)) then -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    elseif IsAtLeast(MapVar(11), 1) then
        if not IsAtLeast(MapVar(21), 1) then
            evt.StatusText("All wards must be destroyed.")
            return
        end
        SetQBit(QBit(1095)) -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    elseif IsQBitSet(QBit(1065)) then -- Bruce
        if not HasItem(2102) then -- Amber
            evt.StatusText("The Door is warded.")
            return
        end
        RemoveItem(2102) -- Amber
        SetValue(MapVar(11), 1)
        if not IsAtLeast(MapVar(21), 1) then
            evt.StatusText("All wards must be destroyed.")
            return
        end
        SetQBit(QBit(1095)) -- Walt
        evt.SetDoorState(10, DoorAction.Close)
        evt.SetDoorState(20, DoorAction.Close)
    else
        evt.StatusText("The Door is warded.")
        return
    end
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(12, DoorAction.Close)
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(13, DoorAction.Close)
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(15, DoorAction.Close)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
    evt.SetDoorState(45, DoorAction.Open)
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(19, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    if not IsQBitSet(QBit(1095)) then -- Walt
        if IsAtLeast(MapVar(21), 1) then
            if not IsAtLeast(MapVar(11), 1) then
                evt.StatusText("All wards must be destroyed.")
                return
            end
            SetQBit(QBit(1095)) -- Walt
            evt.SetDoorState(20, DoorAction.Close)
        elseif IsQBitSet(QBit(1065)) then -- Bruce
            if not HasItem(2102) then -- Amber
                evt.StatusText("The Door is warded.")
                return
            end
            RemoveItem(2102) -- Amber
            SetValue(MapVar(21), 1)
            if not IsAtLeast(MapVar(11), 1) then
                evt.StatusText("All wards must be destroyed.")
                return
            end
            SetQBit(QBit(1095)) -- Walt
            evt.SetDoorState(20, DoorAction.Close)
        else
            evt.StatusText("The Door is warded.")
            return
        end
    end
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Door")

RegisterEvent(25, "Legacy event 25", function()
    evt.SetDoorState(25, DoorAction.Trigger)
end)

RegisterEvent(27, "Stone Face", function()
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(0, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(1, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(2, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(3, 4, 50)
            SetValue(MapVar(2), 1)
        end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(28, "Legacy event 28", function()
    evt.MoveToMap(-2853, 1600, -2655, 1024, 0, 0, 0, 0)
end)

RegisterEvent(29, "Legacy event 29", function()
    evt.MoveToMap(2823, 1534, -2655, 45, 0, 0, 0, 0)
end)

RegisterEvent(30, "Door", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Door")

RegisterEvent(31, "Legacy event 31", function()
    evt.SetDoorState(30, DoorAction.Open)
end)

RegisterEvent(32, "Legacy event 32", function()
    evt.SetDoorState(45, DoorAction.Close)
    evt.SetDoorState(46, DoorAction.Close)
end)

RegisterEvent(33, "Legacy event 33", function()
    evt.SetDoorState(18, DoorAction.Open)
end)

RegisterEvent(41, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(42, "Chest", function()
    if not IsAtLeast(MapVar(12), 1) then
        if IsQBitSet(QBit(1099)) then -- Lisa
            evt.OpenChest(12)
        elseif HasItem(2179) then -- Chest Key
            evt.OpenChest(2)
            RemoveItem(2179) -- Chest Key
            SetValue(MapVar(12), 1)
            SetQBit(QBit(1099)) -- Lisa
        else
            evt.StatusText("The chest is locked.")
        end
        return
    end
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(43, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(46, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(47, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(48, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(50, "Legacy event 50", function()
    if IsAtLeast(MapVar(3), 1) then return end
    evt.CastSpell(83, 4, 1, 0, 0, 0, 0, 0, 0) -- Day of the Gods
    SetValue(MapVar(3), 1)
    evt.StatusText("Magically Refreshing!")
end)

RegisterEvent(51, "Exit", function()
    evt.MoveToMap(16387, -20005, 225, 512, 0, 0, 0, 0, "outd2.odm")
end, "Exit")

RegisterEvent(52, "Lord of Fire", function()
    evt.SetDoorState(51, DoorAction.Close)
    evt.SetDoorState(52, DoorAction.Close)
    SetQBit(QBit(1065)) -- Bruce
    evt.SpeakNPC(1083) -- Lord of Fire
end, "Lord of Fire")

RegisterEvent(53, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(54, "Stone Face", function()
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(0, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(1, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(2, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(3, 4, 50)
            SetValue(MapVar(2), 1)
        end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(55, DoorAction.Close)
end, "Door")

RegisterEvent(56, "Legacy event 56", function()
    SetValue(MapVar(3), 0)
end)

RegisterEvent(57, "Legacy event 57", function()
    SetValue(MapVar(3), 0)
end)

RegisterEvent(58, "Stone Face", function()
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(0, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(1, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(2, 4, 50)
            SetValue(MapVar(2), 1)
        end
        evt.ForPlayer(player)
        if not HasItem(2102) then -- Amber
            evt.DamagePlayer(3, 4, 50)
            SetValue(MapVar(2), 1)
        end
    if not IsAtLeast(MapVar(2), 1) then
        evt.StatusText("\"Ah, delicious amber!\"")
        evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
        return
    end
    evt.StatusText("All must have amber.  Take life force!")
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1792, -19, 1, 1, 0, 0, 0, 0)
end, "Stone Face")

RegisterEvent(59, "Bag", function()
    evt.OpenChest(11)
end, "Bag")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(58, DoorAction.Close)
end, "Door")

