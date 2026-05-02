-- Dragoons' Caverns
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {},
    onLeave = {},
    openedChestIds = {
    [37] = {1},
    [38] = {0, 9},
    [39] = {3},
    [40] = {4},
    [41] = {5},
    [42] = {6},
    [43] = {7, 2},
    [44] = {8},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Door", function()
    evt.SetDoorState(1, DoorAction.Close)
end, "Door")

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

RegisterEvent(8, "Switch", function()
    evt.SetDoorState(8, DoorAction.Trigger)
    evt.SetDoorState(9, DoorAction.Trigger)
end, "Switch")

RegisterEvent(10, "Door", function()
    evt.SetDoorState(10, DoorAction.Close)
end, "Door")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(11, DoorAction.Close)
end, "Door")

RegisterEvent(12, "Lever", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(12, DoorAction.Trigger)
        evt.SetDoorState(13, DoorAction.Trigger)
        evt.SetFacetBit(2667, FacetBits.Untouchable, 1)
        SetValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(12, DoorAction.Trigger)
    evt.SetDoorState(13, DoorAction.Trigger)
    evt.SetFacetBit(2667, FacetBits.Untouchable, 0)
    SetValue(MapVar(2), 0)
end, "Lever")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(14, DoorAction.Close)
end, "Door")

RegisterEvent(15, "Switch", function()
    evt.SetDoorState(15, DoorAction.Trigger)
    evt.SetDoorState(19, DoorAction.Trigger)
end, "Switch")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(16, DoorAction.Close)
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(17, DoorAction.Close)
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(18, DoorAction.Close)
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(20, DoorAction.Close)
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(21, DoorAction.Close)
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(22, DoorAction.Close)
end, "Door")

RegisterEvent(23, "Switch", function()
    evt.SetDoorState(23, DoorAction.Trigger)
    evt.SetDoorState(24, DoorAction.Trigger)
end, "Switch")

RegisterEvent(25, "Lever", function()
    if not IsAtLeast(MapVar(2), 1) then
        evt.SetDoorState(25, DoorAction.Trigger)
        evt.SetDoorState(26, DoorAction.Trigger)
        evt.SetFacetBit(2668, FacetBits.Untouchable, 1)
        SetValue(MapVar(2), 1)
        return
    end
    evt.SetDoorState(25, DoorAction.Trigger)
    evt.SetDoorState(26, DoorAction.Trigger)
    evt.SetFacetBit(2668, FacetBits.Untouchable, 0)
    SetValue(MapVar(2), 0)
end, "Lever")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(27, DoorAction.Close)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(28, DoorAction.Close)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(29, DoorAction.Close)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(30, DoorAction.Close)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(31, DoorAction.Close)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(32, DoorAction.Close)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(33, DoorAction.Close)
end, "Door")

RegisterEvent(34, "Double Door", function()
    evt.SetDoorState(34, DoorAction.Close)
    evt.SetDoorState(35, DoorAction.Close)
end, "Double Door")

RegisterEvent(36, "Legacy event 36", function()
    evt.SetDoorState(36, DoorAction.Close)
end)

RegisterEvent(37, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(38, "Chest", function()
    if not IsAtLeast(MapVar(4), 1) then
        if not IsQBitSet(QBit(1038)) then -- 14 D6, given when Message 504 given out.
            evt.OpenChest(0)
            SetQBit(QBit(1038)) -- 14 D6, given when Message 504 given out.
            SetValue(MapVar(4), 1)
            return
        end
        evt.OpenChest(9)
    end
    evt.OpenChest(0)
    SetQBit(QBit(1038)) -- 14 D6, given when Message 504 given out.
    SetValue(MapVar(4), 1)
end, "Chest")

RegisterEvent(39, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(40, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(41, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(42, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(43, "Chest", function()
    if not IsAtLeast(MapVar(3), 1) then
        if IsAtLeast(MapVar(3), 1) then
            evt.OpenChest(7)
            SetQBit(QBit(1027)) -- 3 D06, given when harp is recovered
            SetValue(MapVar(3), 1)
            return
        elseif IsQBitSet(QBit(1027)) then -- 3 D06, given when harp is recovered
            evt.OpenChest(2)
        else
            evt.OpenChest(7)
            SetQBit(QBit(1027)) -- 3 D06, given when harp is recovered
            SetValue(MapVar(3), 1)
            return
        end
    end
    evt.OpenChest(7)
    SetQBit(QBit(1027)) -- 3 D06, given when harp is recovered
    SetValue(MapVar(3), 1)
end, "Chest")

RegisterEvent(44, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(45, "Chest", function()
    local randomStep = PickRandomOption(45, 1, {1, 3, 5, 7, 9, 11})
    if randomStep == 1 then
        evt.MoveToMap(2752, -256, 0, 1024, 0, 0, 0, 0)
        return
    elseif randomStep == 3 then
        evt.MoveToMap(3222, -2076, -31, 1012, 0, 0, 0, 0)
        return
    elseif randomStep == 5 then
        evt.MoveToMap(1152, -5193, -511, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 7 then
        evt.MoveToMap(-59, 1997, -896, 512, 0, 0, 0, 0)
        return
    elseif randomStep == 9 then
        evt.MoveToMap(-831, 3109, -128, 0, 0, 0, 0, 0)
        return
    elseif randomStep == 11 then
        local randomStep = PickRandomOption(45, 12, {13, 15, 17, 19})
        if randomStep == 13 then
            evt.MoveToMap(-7023, -1413, -383, 512, 0, 0, 0, 0)
            return
        elseif randomStep == 15 then
            evt.MoveToMap(1847, 8410, -767, 1536, 0, 0, 0, 0)
            return
        elseif randomStep == 17 then
            evt.MoveToMap(-843, 6440, -767, 1024, 0, 0, 0, 0)
            return
        elseif randomStep == 19 then
            evt.MoveToMap(-3622, 5464, -639, 1024, 0, 0, 0, 0)
            return
        end
    end
end, "Chest")

RegisterEvent(46, "Door", function()
    evt.StatusText("The door won't budge")
end, "Door")

RegisterEvent(50, "Exit", function()
    evt.MoveToMap(16495, -14570, 96, 1536, 0, 0, 0, 0, "outd3.odm")
end, "Exit")

RegisterEvent(51, "Legacy event 51", function()
    if IsQBitSet(QBit(1330)) then return end -- NPC
    SetQBit(QBit(1330)) -- NPC
    AddValue(BaseLuck, 10)
end)

