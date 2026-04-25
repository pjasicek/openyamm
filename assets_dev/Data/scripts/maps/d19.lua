-- Necromancers' Guild
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
    openedChestIds = {
    [81] = {0},
    [82] = {1},
    [83] = {2},
    [84] = {3},
    [85] = {4},
    [86] = {5},
    [87] = {6},
    [88] = {7},
    [89] = {8},
    [90] = {9},
    [91] = {10},
    [92] = {11},
    [93] = {12},
    [94] = {13},
    [95] = {14},
    [96] = {15},
    [97] = {16},
    [98] = {17},
    [99] = {18},
    [100] = {19},
    },
    textureNames = {},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(20)) then
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(5, 1)
        return
    elseif IsQBitSet(QBit(229)) then
        if not IsAtLeast(88080639, 1344) then
            evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
            evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
            SetValue(MapVar(11), 2)
            evt.SetDoorState(5, 1)
            return
        end
        ClearQBit(QBit(229))
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 0)
        ClearQBit(QBit(229))
    else
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 1)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 0)
        ClearQBit(QBit(229))
    end
evt.SetDoorState(5, 1)
return
end)

RegisterEvent(2, "Legacy event 2", function()
    evt.SetDoorState(8, 1)
    evt.SetDoorState(9, 0)
    evt.SetDoorState(10, 1)
    evt.SetDoorState(11, 0)
    evt.SetDoorState(12, 0)
    evt.SetDoorState(13, 0)
    evt.SetDoorState(14, 0)
    evt.SetDoorState(15, 0)
    evt.SetDoorState(16, 0)
    SetValue(MapVar(21), 0)
    return
end)

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(19)) then
        evt.MoveNPC(9, 0)
        evt.MoveNPC(69, 175)
        evt.MoveNPC(76, 180)
        if IsQBitSet(QBit(229)) then
            return
        elseif IsAtLeast(MapVar(11), 2) then
            SetQBit(QBit(229))
            SetValue(255, 0)
            return
        else
            return
        end
    elseif IsQBitSet(QBit(229)) then
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(229))
        SetValue(255, 0)
        return
    else
        return
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, 0)
    return
end, "Door")

RegisterEvent(12, "Button", function()
    evt.SetDoorState(2, 2)
    return
end, "Button")

RegisterEvent(13, "Button", function()
    evt.SetDoorState(3, 2)
    return
end, "Button")

RegisterEvent(14, "Button", function()
    evt.SetDoorState(4, 2)
    evt.SetDoorState(5, 1)
    return
end, "Button")

RegisterEvent(15, "Door", function()
    if not IsQBitSet(QBit(20)) then
        if not IsAtLeast(Player(34), 34) then
            evt.SetNPCGreeting(58, 107)
            if not IsAtLeast(316, 0) then
                evt.SpeakNPC(58) -- Guard
            end
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        if not evt._IsNpcInParty(34) then
            evt.SetNPCGreeting(58, 144)
            if not IsAtLeast(316, 0) then
                evt.SpeakNPC(58) -- Guard
            end
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
    end
    evt.SetDoorState(5, 0)
    return
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, 0)
    return
end, "Door")

RegisterEvent(18, "Button", function()
    if not IsAtLeast(MapVar(21), 15) then
        evt.SetDoorState(8, 0)
        evt.SetDoorState(9, 1)
        evt.SetDoorState(10, 0)
        if not IsAtLeast(MapVar(21), 6) then return end
        SubtractValue(MapVar(21), 1)
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    return
end, "Button")

RegisterEvent(19, "Button", function()
    if not IsAtLeast(MapVar(21), 15) then
        if IsAtLeast(MapVar(21), 5) then
            evt.SetDoorState(8, 1)
            evt.SetDoorState(9, 0)
            evt.SetDoorState(10, 1)
            AddValue(MapVar(21), 1)
            return
        end
    end
    evt.StatusText("The Door will not move")
    return
end, "Button")

RegisterEvent(20, "Lever", function()
    if not IsAtLeast(MapVar(21), 15) then
        if IsAtLeast(MapVar(21), 6) then
            evt.StatusText("The lever will not move")
            return
        elseif IsAtLeast(MapVar(21), 5) then
            evt.StatusText("The lever will not move")
            return
        elseif IsAtLeast(MapVar(21), 4) then
            evt.StatusText("The lever will not move")
            return
        elseif IsAtLeast(MapVar(21), 3) then
            evt.StatusText("The lever will not move")
            return
        elseif IsAtLeast(MapVar(21), 2) then
            evt.StatusText("The lever will not move")
            return
        elseif IsAtLeast(MapVar(21), 1) then
            evt.SetDoorState(11, 0)
            SubtractValue(MapVar(21), 1)
        else
            evt.SetDoorState(11, 1)
            AddValue(MapVar(21), 1)
        end
    return
    end
    evt.StatusText("The lever will not move")
    return
end, "Lever")

RegisterEvent(21, "Lever", function()
    if IsAtLeast(MapVar(21), 15) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 6) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 5) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 4) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.SetDoorState(12, 0)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.SetDoorState(12, 1)
        AddValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.StatusText("The lever will not move")
        return
    else
        evt.StatusText("The lever will not move")
        return
    end
end, "Lever")

RegisterEvent(22, "Lever", function()
    if IsAtLeast(MapVar(21), 15) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 6) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 5) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 4) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.SetDoorState(13, 0)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.SetDoorState(13, 1)
        AddValue(MapVar(21), 1)
    else
        evt.StatusText("The lever will not move")
    end
return
end, "Lever")

RegisterEvent(23, "Lever", function()
    if IsAtLeast(MapVar(21), 15) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 6) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 5) then
        evt.SetDoorState(14, 0)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 4) then
        evt.SetDoorState(14, 1)
        AddValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.SetDoorState(14, 0)
        SubtractValue(MapVar(21), 1)
    else
        evt.StatusText("The lever will not move")
    end
return
end, "Lever")

RegisterEvent(24, "Lever", function()
    if IsAtLeast(MapVar(21), 15) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 6) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 5) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 4) then
        evt.SetDoorState(15, 0)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.SetDoorState(15, 1)
        AddValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.StatusText("The lever will not move")
        return
    else
        evt.StatusText("The lever will not move")
        return
    end
end, "Lever")

RegisterEvent(25, "Door Beam", function()
    if not IsAtLeast(MapVar(21), 6) then
        evt.StatusText("The Beam will not move")
        return
    end
    if not IsAtLeast(MapVar(21), 15) then
        evt.SetDoorState(16, 1)
        SetValue(MapVar(21), 15)
        return
    end
    evt.SetDoorState(16, 0)
    SetValue(MapVar(21), 6)
    return
end, "Door Beam")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(59, 1)
    evt.SetDoorState(60, 1)
    evt.SetDoorState(61, 1)
    evt.SetDoorState(62, 1)
    return
end, "Door")

RegisterEvent(27, "Door", function()
    if not IsAtLeast(MapVar(21), 15) then
        evt.SetDoorState(8, 0)
        evt.SetDoorState(9, 1)
        evt.SetDoorState(10, 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        evt.SetDoorState(7, 0)
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    return
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, 0)
    return
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, 0)
    return
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, 0)
    return
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, 0)
    return
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, 0)
    return
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, 0)
    return
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, 0)
    return
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, 0)
    return
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, 0)
    return
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, 0)
    return
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, 0)
    return
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, 0)
    return
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, 0)
    return
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, 0)
    return
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, 0)
    return
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, 0)
    return
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, 0)
    return
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, 0)
    return
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, 0)
    return
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, 0)
    return
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, 0)
    return
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, 0)
    return
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, 0)
    return
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, 0)
    return
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, 0)
    return
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, 0)
    return
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, 0)
    return
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, 0)
    return
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, 0)
    return
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, 0)
    return
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, 0)
    return
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, 0)
    return
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, 0)
    return
end, "Door")

RegisterEvent(61, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(51, 0)
        evt.SetDoorState(52, 0)
        return
    elseif IsQBitSet(QBit(229)) then
        evt.SetDoorState(51, 0)
        evt.SetDoorState(52, 0)
        return
    elseif IsQBitSet(QBit(20)) then
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(51, 0)
        evt.SetDoorState(52, 0)
        return
    elseif IsQBitSet(QBit(19)) then
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(38) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229))
        SetValue(255, 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(51, 0)
        evt.SetDoorState(52, 0)
    else
        evt.SpeakNPC(38) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(62, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(53, 0)
        evt.SetDoorState(54, 0)
        return
    elseif IsQBitSet(QBit(229)) then
        evt.SetDoorState(53, 0)
        evt.SetDoorState(54, 0)
        return
    elseif IsQBitSet(QBit(20)) then
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(53, 0)
        evt.SetDoorState(54, 0)
        return
    elseif IsQBitSet(QBit(19)) then
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(38) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229))
        SetValue(255, 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(53, 0)
        evt.SetDoorState(54, 0)
    else
        evt.SpeakNPC(38) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(63, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(55, 0)
        evt.SetDoorState(56, 0)
        return
    elseif IsQBitSet(QBit(229)) then
        evt.SetDoorState(55, 0)
        evt.SetDoorState(56, 0)
        return
    elseif IsQBitSet(QBit(20)) then
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(55, 0)
        evt.SetDoorState(56, 0)
        return
    elseif IsQBitSet(QBit(19)) then
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(38) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229))
        SetValue(255, 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(55, 0)
        evt.SetDoorState(56, 0)
    else
        evt.SpeakNPC(38) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(64, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(57, 0)
        evt.SetDoorState(58, 0)
        return
    elseif IsQBitSet(QBit(229)) then
        evt.SetDoorState(57, 0)
        evt.SetDoorState(58, 0)
        return
    elseif IsQBitSet(QBit(20)) then
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(57, 0)
        evt.SetDoorState(58, 0)
        return
    elseif IsQBitSet(QBit(19)) then
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(38) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229))
        SetValue(255, 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
        SetValue(MapVar(11), 2)
        evt.SetDoorState(57, 0)
        evt.SetDoorState(58, 0)
    else
        evt.SpeakNPC(38) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(65, "Door", function()
    evt.SetDoorState(59, 0)
    evt.SetDoorState(60, 0)
    return
end, "Door")

RegisterEvent(66, "Door", function()
    evt.SetDoorState(61, 0)
    evt.SetDoorState(62, 0)
    return
end, "Door")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
    return
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
    return
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
    return
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
    return
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
    return
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
    return
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
    return
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
    return
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
    return
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
    return
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
    return
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
    return
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
    return
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
    return
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
    return
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
    return
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
    return
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
    return
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
    return
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
    return
end, "Chest")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(27)) then return end
    if not IsQBitSet(QBit(26)) then return end
    if not IsAtLeast(Player(34), 34) then return end
    if not IsAtLeast(MapVar(21), 15) then return end
    if not evt._IsNpcInParty(34) then return end
    SetQBit(QBit(27))
    evt.ShowMovie("\"skeltrans\" ", false)
    evt.SetFacetBit(30, FacetBits.Untouchable, 1)
    evt.SetFacetBit(30, FacetBits.Invisible, 1)
    return
end)

RegisterEvent(201, "Sandro/Thant's Throne Room", function()
    if IsQBitSet(QBit(27)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsAtLeast(MapVar(11), 2) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(20)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(19)) then
        evt.EnterHouse(180) -- Sandro/Thant's Throne Room
        return
    else
        evt.ForPlayer(Players.All)
        if HasItem(604) then -- Nightshade Brazier
            RemoveItem(604) -- Nightshade Brazier
            ClearQBit(QBit(14))
            ClearQBit(QBit(15))
            ClearQBit(QBit(28))
            ClearQBit(QBit(26))
            SetQBit(QBit(19))
            evt.MoveNPC(10, 0)
            evt.SetNPCTopic(9, 0, 0)
            evt.SetNPCTopic(9, 1, 101)
            evt.SetNPCGreeting(9, 32)
            evt.ForPlayer(Players.All)
            SetAward(Award(10))
            AddValue(Experience, 12500)
            evt.ForPlayer(Players.Current)
            AddValue(Gold, 8000)
            evt.ShowMovie("\"nightshade\" ", false)
            AddValue(History(12), 0)
            ClearQBit(QBit(203))
        end
        evt.EnterHouse(180) -- Sandro/Thant's Throne Room
        return
    end
end, "Sandro/Thant's Throne Room")

RegisterEvent(203, "Dyson Leland's Room", function()
    SetValue(MapVar(31), 5)
    if IsQBitSet(QBit(89)) then
        evt.SetNPCTopic(11, 3, 634)
        if IsQBitSet(QBit(26)) then
            SetValue(MapVar(31), 4)
            if not IsQBitSet(QBit(28)) then
                evt.SetNPCGreeting(11, 35)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34)
            evt.EnterHouse(181) -- Dyson Leland's Room
            return
        elseif IsQBitSet(QBit(28)) then
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34)
        else
            evt.SetNPCGreeting(11, 35)
        end
    evt.EnterHouse(181) -- Dyson Leland's Room
    return
    elseif IsQBitSet(QBit(90)) then
        evt.SetNPCTopic(11, 3, 634)
        if IsQBitSet(QBit(26)) then
            SetValue(MapVar(31), 4)
            if not IsQBitSet(QBit(28)) then
                evt.SetNPCGreeting(11, 35)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34)
            evt.EnterHouse(181) -- Dyson Leland's Room
            return
        elseif IsQBitSet(QBit(28)) then
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36)
                evt.EnterHouse(181) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34)
        else
            evt.SetNPCGreeting(11, 35)
        end
    evt.EnterHouse(181) -- Dyson Leland's Room
    return
    else
        evt.EnterHouse(181) -- Dyson Leland's Room
        return
    end
end, "Dyson Leland's Room")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
    return
end)

RegisterEvent(452, "Door", function()
    evt.SetDoorState(5, 0)
    return
end, "Door")

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(316, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(38) -- Guard
    SetValue(MapVar(11), 1)
    return
end)

RegisterEvent(454, "Legacy event 454", function()
    if IsAtLeast(MapVar(11), 2) then return end
    if IsAtLeast(316, 0) then return end
    evt.SetMonGroupBit(41, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(42, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(10, MonsterBits.Invisible, 0)
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
    SetValue(MapVar(11), 2)
    evt.SetDoorState(7, 0)
    return
end)

RegisterEvent(501, "Leave the Necromancers' Guild", function()
    evt.MoveToMap(15620, -11571, 4480, 1536, 0, 0, 0, 0, "Out06.odm")
    return
end, "Leave the Necromancers' Guild")

