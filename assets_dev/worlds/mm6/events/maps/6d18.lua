-- Gharik's Forge
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {52},
    onLeave = {},
    openedChestIds = {
    [44] = {1},
    [45] = {2},
    [46] = {3},
    [47] = {4},
    [48] = {5, 8},
    [49] = {6},
    [50] = {7},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 54, repeating = true, intervalGameMinutes = 1, remainingGameMinutes = 1 },
    { eventId = 56, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    { eventId = 57, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    { eventId = 58, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    { eventId = 59, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    { eventId = 60, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    { eventId = 61, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(2, DoorAction.Close)
end, "Door")

RegisterEvent(2, "Legacy event 2", function()
    evt.SetDoorState(1, DoorAction.Close)
    evt.SetDoorState(2, DoorAction.Close)
end)

RegisterEvent(3, "Lever", function()
    evt.SetDoorState(3, DoorAction.Close)
    evt.SetDoorState(4, DoorAction.Close)
end, "Lever")

RegisterEvent(4, "Lever", function()
    evt.SetDoorState(5, DoorAction.Close)
    evt.SetDoorState(6, DoorAction.Close)
end, "Lever")

RegisterEvent(5, "Lever", function()
    evt.SetDoorState(7, DoorAction.Close)
    evt.SetDoorState(8, DoorAction.Close)
end, "Lever")

RegisterEvent(6, "Lever", function()
    evt.SetDoorState(9, DoorAction.Close)
    evt.SetDoorState(10, DoorAction.Close)
end, "Lever")

RegisterEvent(7, "Lever", function()
    evt.SetDoorState(11, DoorAction.Close)
    evt.SetDoorState(12, DoorAction.Close)
end, "Lever")

RegisterEvent(8, "Lever", function()
    evt.SetDoorState(13, DoorAction.Close)
    evt.SetDoorState(14, DoorAction.Close)
    evt.SetDoorState(49, DoorAction.Open)
end, "Lever")

RegisterEvent(9, "Lever", function()
    evt.SetDoorState(15, DoorAction.Close)
    evt.SetDoorState(16, DoorAction.Close)
end, "Lever")

RegisterEvent(10, "Lever", function()
    evt.SetDoorState(17, DoorAction.Close)
    evt.SetDoorState(18, DoorAction.Close)
end, "Lever")

RegisterEvent(11, "Lever", function()
    evt.SetDoorState(19, DoorAction.Close)
    evt.SetDoorState(20, DoorAction.Close)
end, "Lever")

RegisterEvent(12, "Lever", function()
    evt.SetDoorState(21, DoorAction.Close)
    evt.SetDoorState(22, DoorAction.Close)
end, "Lever")

RegisterEvent(13, "Lever", function()
    evt.SetDoorState(23, DoorAction.Close)
    evt.SetDoorState(24, DoorAction.Close)
end, "Lever")

RegisterEvent(14, "Lever", function()
    evt.SetDoorState(25, DoorAction.Close)
    evt.SetDoorState(26, DoorAction.Close)
end, "Lever")

RegisterEvent(15, "Lever", function()
    evt.SetDoorState(27, DoorAction.Trigger)
    evt.SetDoorState(28, DoorAction.Trigger)
end, "Lever")

RegisterEvent(16, "Lever", function()
    if IsQBitSet(QBit(1035)) then -- 11 D7, opens tomb in D18.
        if IsQBitSet(QBit(1223)) then -- Quest item bits for seer
            evt.ForPlayer(Players.All)
            if HasItem(2107) then -- Key to Gharik's Laboratory
                evt.SetDoorState(29, DoorAction.Close)
                evt.SetDoorState(30, DoorAction.Close)
                RemoveItem(2107) -- Key to Gharik's Laboratory
                SetQBit(QBit(1400)) -- NPC
                ClearQBit(QBit(1223)) -- Quest item bits for seer
            elseif IsQBitSet(QBit(1400)) then -- NPC
                evt.SetDoorState(29, DoorAction.Close)
                evt.SetDoorState(30, DoorAction.Close)
                RemoveItem(2107) -- Key to Gharik's Laboratory
                SetQBit(QBit(1400)) -- NPC
                ClearQBit(QBit(1223)) -- Quest item bits for seer
            else
                evt.StatusText("The Door is locked")
                return
            end
        end
        evt.SetDoorState(29, DoorAction.Close)
        evt.SetDoorState(30, DoorAction.Close)
        RemoveItem(2107) -- Key to Gharik's Laboratory
        SetQBit(QBit(1400)) -- NPC
        ClearQBit(QBit(1223)) -- Quest item bits for seer
    end
    evt.ForPlayer(Players.All)
    if HasItem(2107) then -- Key to Gharik's Laboratory
        evt.SetDoorState(29, DoorAction.Close)
        evt.SetDoorState(30, DoorAction.Close)
        RemoveItem(2107) -- Key to Gharik's Laboratory
        SetQBit(QBit(1400)) -- NPC
        ClearQBit(QBit(1223)) -- Quest item bits for seer
    elseif IsQBitSet(QBit(1400)) then -- NPC
        evt.SetDoorState(29, DoorAction.Close)
        evt.SetDoorState(30, DoorAction.Close)
        RemoveItem(2107) -- Key to Gharik's Laboratory
        SetQBit(QBit(1400)) -- NPC
        ClearQBit(QBit(1223)) -- Quest item bits for seer
    else
        evt.StatusText("The Door is locked")
        return
    end
end, "Lever")

RegisterEvent(17, "Lever", function()
    evt.SetDoorState(31, DoorAction.Close)
    evt.SetDoorState(32, DoorAction.Close)
end, "Lever")

RegisterEvent(18, "Lever", function()
    evt.SetDoorState(33, DoorAction.Close)
    evt.SetDoorState(34, DoorAction.Close)
end, "Lever")

RegisterEvent(19, "Lever", function()
    evt.SetDoorState(35, DoorAction.Close)
    evt.SetDoorState(36, DoorAction.Close)
end, "Lever")

RegisterEvent(20, "Lever", function()
    evt.SetDoorState(37, DoorAction.Close)
    evt.SetDoorState(38, DoorAction.Close)
end, "Lever")

RegisterEvent(21, "Lever", function()
    evt.SetDoorState(39, DoorAction.Close)
    evt.SetDoorState(40, DoorAction.Close)
end, "Lever")

RegisterEvent(22, "Lever", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Lever")

RegisterEvent(23, "Lever", function()
    evt.SetDoorState(23, DoorAction.Close)
end, "Lever")

RegisterEvent(24, "Lever", function()
    evt.SetDoorState(24, DoorAction.Close)
end, "Lever")

RegisterEvent(25, "Lever", function()
    evt.SetDoorState(25, DoorAction.Close)
end, "Lever")

RegisterEvent(26, "Lever", function()
    evt.SetDoorState(26, DoorAction.Close)
end, "Lever")

RegisterEvent(29, "Lever", function()
    evt.SetDoorState(29, DoorAction.Close)
end, "Lever")

RegisterEvent(30, "Lever", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Lever")

RegisterEvent(31, "Tile", function()
    SetValue(MapVar(2), 0)
    evt.MoveToMap(1916, 6618, 1, 502, 0, 0, 0, 0)
end, "Tile")

RegisterEvent(32, "Tile", function()
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-2688, 1152, 1152, 1550, 0, 0, 0, 0)
end, "Tile")

RegisterEvent(33, "Lever", function()
    evt.SetDoorState(48, DoorAction.Trigger)
    evt.SetDoorState(41, DoorAction.Trigger)
end, "Lever")

RegisterEvent(34, "Lever", function()
    evt.SetDoorState(42, DoorAction.Trigger)
    evt.SetDoorState(50, DoorAction.Trigger)
end, "Lever")

RegisterEvent(35, "Lever", function()
    evt.SetDoorState(43, DoorAction.Trigger)
    evt.SetDoorState(53, DoorAction.Trigger)
end, "Lever")

RegisterEvent(36, "Lever", function()
    evt.SetDoorState(44, DoorAction.Trigger)
    evt.SetDoorState(51, DoorAction.Trigger)
end, "Lever")

RegisterEvent(38, "Lever", function()
    evt.SetDoorState(45, DoorAction.Trigger)
    evt.SetDoorState(48, DoorAction.Trigger)
end, "Lever")

RegisterEvent(39, "Lever", function()
    evt.SetDoorState(46, DoorAction.Trigger)
    evt.SetDoorState(52, DoorAction.Trigger)
    evt.SetDoorState(49, DoorAction.Open)
end, "Lever")

RegisterEvent(40, "Lever", function()
    evt.SetDoorState(47, DoorAction.Trigger)
    evt.SetDoorState(49, DoorAction.Trigger)
end, "Lever")

RegisterEvent(41, "Tile", function()
    SetValue(MapVar(2), 0)
    evt.MoveToMap(-1822, 4049, 1, 502, 0, 0, 0, 0)
end, "Tile")

RegisterEvent(42, "Tile", function()
    SetValue(MapVar(2), 0)
    evt.MoveToMap(134, 1151, 1, 502, 0, 0, 0, 0)
end, "Tile")

RegisterEvent(43, "Tile", function()
    SetValue(MapVar(2), 0)
    evt.MoveToMap(2324, -141, -2047, 896, 0, 0, 0, 0)
end, "Tile")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(45, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(46, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(47, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(48, "Chest", function()
    if not IsAtLeast(MapVar(51), 1) then
        if not IsQBitSet(QBit(1029)) then -- 5 D18, questbit for getting hourglass
            SetValue(MapVar(51), 1)
            evt.OpenChest(5)
            SetQBit(QBit(1029)) -- 5 D18, questbit for getting hourglass
            SetQBit(QBit(1207)) -- Quest item bits for seer
            return
        end
        evt.OpenChest(8)
    end
    evt.OpenChest(5)
    SetQBit(QBit(1029)) -- 5 D18, questbit for getting hourglass
    SetQBit(QBit(1207)) -- Quest item bits for seer
end, "Chest")

RegisterEvent(49, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(50, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(51, "Legacy event 51", function()
    SetValue(MapVar(2), 1)
end)

RegisterEvent(52, "Legacy event 52", function()
    SetValue(MapVar(2), 0)
end)

RegisterEvent(53, "Legacy event 53", function()
    SetValue(MapVar(2), 0)
end)

RegisterEvent(54, "Legacy event 54", function()
    if IsAtLeast(MapVar(2), 1) then
        evt.DamagePlayer(5, 5, 25)
    end
end)

RegisterEvent(55, "Door", function()
    evt.StatusText("The Door won't budge.")
end, "Door")

RegisterEvent(56, "Legacy event 56", function()
    local randomStep = PickRandomOption(56, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.SummonObject(1000, -1792, 1536, -508, 1000, 2, false) -- Gold
        return
    elseif randomStep == 4 then
        evt.SummonObject(1050, -1024, 1408, -508, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 6 then
        evt.SummonObject(1000, -1920, 640, -508, 1000, 2, false) -- Gold
        return
    elseif randomStep == 8 then
        evt.SummonObject(1050, -1664, 256, -508, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 10 then
        evt.SummonObject(1050, -1280, 128, -508, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 12 then
        evt.SummonObject(1050, -1280, -256, -508, 1000, 2, true) -- Fireball
    end
end)

RegisterEvent(57, "Legacy event 57", function()
    local randomStep = PickRandomOption(57, 2, {2, 4, 6, 8, 10})
    if randomStep == 2 then
        evt.SummonObject(1000, 2688, 6016, -765, 1000, 2, true) -- Gold
        return
    elseif randomStep == 4 then
        evt.SummonObject(1050, 3328, 5888, -765, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 6 then
        evt.SummonObject(1000, 1664, 5888, -765, 1000, 2, false) -- Gold
        return
    elseif randomStep == 8 then
        evt.SummonObject(1050, 2650, 6528, -765, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 10 then
        evt.SummonObject(1050, 2650, 5248, -765, 1000, 2, false) -- Fireball
    end
end)

RegisterEvent(58, "Legacy event 58", function()
    local randomStep = PickRandomOption(58, 2, {2, 4, 6, 8, 10, 12})
    if randomStep == 2 then
        evt.SummonObject(1000, 4608, 256, -2044, 1000, 2, true) -- Gold
        return
    elseif randomStep == 4 then
        evt.SummonObject(1050, 4736, 0, -2044, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 6 then
        evt.SummonObject(1050, 4736, -640, -2044, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 8 then
        evt.SummonObject(1000, 4608, -2816, -2044, 1000, 2, false) -- Gold
        return
    elseif randomStep == 10 then
        evt.SummonObject(1050, 3456, -3456, -2044, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 12 then
        evt.SummonObject(1050, 2816, -3072, -2044, 1000, 2, false) -- Fireball
    end
end)

RegisterEvent(59, "Legacy event 59", function()
    local randomStep = PickRandomOption(59, 2, {2, 4, 6, 8})
    if randomStep == 2 then
        evt.SummonObject(1050, -2432, -2304, -2044, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 4 then
        evt.SummonObject(1050, 1408, -1280, -2044, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 6 then
        evt.SummonObject(1050, 512, -1152, -2044, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 8 then
        evt.SummonObject(1000, -1024, -1024, -2044, 1000, 2, false) -- Gold
    end
end)

RegisterEvent(60, "Legacy event 60", function()
    local randomStep = PickRandomOption(60, 2, {2, 4, 6, 8})
    if randomStep == 2 then
        evt.SummonObject(1050, 2560, 2304, -1404, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 4 then
        evt.SummonObject(1000, 2560, 1664, -1404, 1000, 2, true) -- Gold
        return
    elseif randomStep == 6 then
        evt.SummonObject(1050, 3456, 2304, -1404, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 8 then
        evt.SummonObject(1050, 3456, 1792, -1404, 1000, 2, false) -- Fireball
    end
end)

RegisterEvent(61, "Legacy event 61", function()
    local randomStep = PickRandomOption(61, 2, {2, 4, 6, 8, 10})
    if randomStep == 2 then
        evt.SummonObject(1000, 896, 2816, -765, 1000, 2, true) -- Gold
        return
    elseif randomStep == 4 then
        evt.SummonObject(1050, 1280, 2432, -765, 1000, 2, true) -- Fireball
        return
    elseif randomStep == 6 then
        evt.SummonObject(1000, -512, 2688, -765, 1000, 2, false) -- Gold
        return
    elseif randomStep == 8 then
        evt.SummonObject(1050, -1024, 2304, -765, 1000, 2, false) -- Fireball
        return
    elseif randomStep == 10 then
        evt.SummonObject(1050, -256, 2816, -765, 1000, 2, false) -- Fireball
    end
end)

RegisterEvent(62, "Bookcase", function()
    if IsAtLeast(MapVar(3), 4) then return end
    AddValue(MapVar(3), 1)
    evt.StatusText("Found something!")
    local randomStep = PickRandomOption(62, 4, {4, 6, 8, 10, 12, 14})
    if randomStep == 4 then
        AddValue(InventoryItem(1961), 1961) -- Preservation
        return
    elseif randomStep == 6 then
        AddValue(InventoryItem(1973), 1973) -- Charm
        return
    elseif randomStep == 8 then
        AddValue(InventoryItem(1976), 1976) -- Mass Fear
        return
    elseif randomStep == 10 then
        AddValue(InventoryItem(1988), 1988) -- Hammerhands
        return
    elseif randomStep == 12 then
        AddValue(InventoryItem(1965), 1965) -- Shared Life
        return
    elseif randomStep == 14 then
        AddValue(InventoryItem(1962), 1962) -- Heroism
        return
    end
end, "Bookcase")

RegisterEvent(90, "Exit", function()
    evt.MoveToMap(15585, 11125, 97, 512, 0, 0, 0, 0, "oute3.odm")
end, "Exit")

RegisterEvent(91, "Legacy event 91", function()
    if IsAtLeast(MapVar(46), 1) then
        return
    elseif IsPlayerBitSet(PlayerBit(59)) then
        return
    else
        SetValue(MapVar(46), 1)
        SetPlayerBit(PlayerBit(59))
        AddValue(FireResistance, 25)
        return
    end
end)

