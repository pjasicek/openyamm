-- Necromancers' Guild
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 2, 3, 4, 5},
    onLeave = {6, 7, 8, 9, 10},
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
    if IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(5, DoorAction.Close)
        return
    elseif IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        if not IsAtLeast(Counter(9), 1344) then
            evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
            evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
            evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
            evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
            SetValue(MapVar(11), 2)
            evt.SetDoorState(5, DoorAction.Close)
            return
        end
        SetValue(MapVar(11), 0)
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 0) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 0) -- actor group 42: spawn Necromancer (monster) A
        ClearQBit(QBit(229)) -- You have Pissed off the Necros
        evt.SetDoorState(5, DoorAction.Close)
        return
    else
        evt.SetDoorState(5, DoorAction.Close)
        return
    end
end)

RegisterEvent(2, "Legacy event 2", function()
    evt.SetDoorState(8, DoorAction.Close)
    evt.SetDoorState(9, DoorAction.Open)
    evt.SetDoorState(10, DoorAction.Close)
    evt.SetDoorState(11, DoorAction.Open)
    evt.SetDoorState(12, DoorAction.Open)
    evt.SetDoorState(13, DoorAction.Open)
    evt.SetDoorState(14, DoorAction.Open)
    evt.SetDoorState(15, DoorAction.Open)
    evt.SetDoorState(16, DoorAction.Open)
    SetValue(MapVar(21), 0)
end)

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.MoveNPC(9, 0) -- Sandro -> removed
        evt.MoveNPC(56, 751) -- Sandro -> Council Chamber Door
        evt.MoveNPC(63, 213) -- Thant -> Sandro/Thant's Throne Room
    end
    if IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        return
    elseif IsAtLeast(MapVar(11), 2) then
        SetQBit(QBit(229)) -- You have Pissed off the Necros
        SetValue(Counter(9), 0)
    else
        SetValue(MapVar(11), 0)
    end
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, DoorAction.Open)
end, "Door")

RegisterEvent(12, "Button", function()
    evt.SetDoorState(2, DoorAction.Trigger)
end, "Button")

RegisterEvent(13, "Button", function()
    evt.SetDoorState(3, DoorAction.Trigger)
end, "Button")

RegisterEvent(14, "Button", function()
    evt.SetDoorState(4, DoorAction.Trigger)
    evt.SetDoorState(5, DoorAction.Close)
end, "Button")

RegisterEvent(15, "Door", function()
    if not IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        if not HasPlayer(34) then -- Dyson Leyland
            evt.SetNPCGreeting(45, 107) -- Guard greeting: Halt! These areas are off limits to guests! Guild members only!
            if not IsAtLeast(Invisible, 0) then
                evt.SpeakNPC(45) -- Guard
            end
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        if not evt._IsNpcInParty(34) then
            evt.SetNPCGreeting(45, 0) -- Guard greeting cleared
            if not IsAtLeast(Invisible, 0) then
                evt.SpeakNPC(45) -- Guard
            end
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
    end
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, DoorAction.Open)
end, "Door")

RegisterEvent(18, "Button", function()
    if not IsAtLeast(MapVar(21), 15) then
        evt.SetDoorState(8, DoorAction.Open)
        evt.SetDoorState(9, DoorAction.Close)
        evt.SetDoorState(10, DoorAction.Open)
        if IsAtLeast(MapVar(21), 6) then
            SubtractValue(MapVar(21), 1)
        end
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Button")

RegisterEvent(19, "Button", function()
    if not IsAtLeast(MapVar(21), 15) then
        if IsAtLeast(MapVar(21), 5) then
            evt.SetDoorState(8, DoorAction.Close)
            evt.SetDoorState(9, DoorAction.Open)
            evt.SetDoorState(10, DoorAction.Close)
            AddValue(MapVar(21), 1)
            return
        end
    end
    evt.StatusText("The Door will not move")
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
            evt.SetDoorState(11, DoorAction.Open)
            SubtractValue(MapVar(21), 1)
        else
            evt.SetDoorState(11, DoorAction.Close)
            AddValue(MapVar(21), 1)
        end
    return
    end
    evt.StatusText("The lever will not move")
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
        evt.SetDoorState(12, DoorAction.Open)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.SetDoorState(12, DoorAction.Close)
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
        evt.SetDoorState(13, DoorAction.Open)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.SetDoorState(13, DoorAction.Close)
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
        evt.SetDoorState(14, DoorAction.Open)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 4) then
        evt.SetDoorState(14, DoorAction.Close)
        AddValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 2) then
        evt.StatusText("The lever will not move")
        return
    elseif IsAtLeast(MapVar(21), 1) then
        evt.SetDoorState(14, DoorAction.Open)
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
        evt.SetDoorState(15, DoorAction.Open)
        SubtractValue(MapVar(21), 1)
        return
    elseif IsAtLeast(MapVar(21), 3) then
        evt.SetDoorState(15, DoorAction.Close)
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
        evt.SetDoorState(16, DoorAction.Close)
        SetValue(MapVar(21), 15)
        return
    end
    evt.SetDoorState(16, DoorAction.Open)
    SetValue(MapVar(21), 6)
end, "Door Beam")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(59, DoorAction.Close)
    evt.SetDoorState(60, DoorAction.Close)
    evt.SetDoorState(61, DoorAction.Close)
    evt.SetDoorState(62, DoorAction.Close)
end, "Door")

RegisterEvent(27, "Door", function()
    if not IsAtLeast(MapVar(21), 15) then
        evt.SetDoorState(8, DoorAction.Open)
        evt.SetDoorState(9, DoorAction.Close)
        evt.SetDoorState(10, DoorAction.Open)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetDoorState(7, DoorAction.Open)
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
end, "Door")

RegisterEvent(28, "Door", function()
    evt.SetDoorState(18, DoorAction.Open)
end, "Door")

RegisterEvent(29, "Door", function()
    evt.SetDoorState(19, DoorAction.Open)
end, "Door")

RegisterEvent(30, "Door", function()
    evt.SetDoorState(20, DoorAction.Open)
end, "Door")

RegisterEvent(31, "Door", function()
    evt.SetDoorState(21, DoorAction.Open)
end, "Door")

RegisterEvent(32, "Door", function()
    evt.SetDoorState(22, DoorAction.Open)
end, "Door")

RegisterEvent(33, "Door", function()
    evt.SetDoorState(23, DoorAction.Open)
end, "Door")

RegisterEvent(34, "Door", function()
    evt.SetDoorState(24, DoorAction.Open)
end, "Door")

RegisterEvent(35, "Door", function()
    evt.SetDoorState(25, DoorAction.Open)
end, "Door")

RegisterEvent(36, "Door", function()
    evt.SetDoorState(26, DoorAction.Open)
end, "Door")

RegisterEvent(37, "Door", function()
    evt.SetDoorState(27, DoorAction.Open)
end, "Door")

RegisterEvent(38, "Door", function()
    evt.SetDoorState(28, DoorAction.Open)
end, "Door")

RegisterEvent(39, "Door", function()
    evt.SetDoorState(29, DoorAction.Open)
end, "Door")

RegisterEvent(40, "Door", function()
    evt.SetDoorState(30, DoorAction.Open)
end, "Door")

RegisterEvent(41, "Door", function()
    evt.SetDoorState(31, DoorAction.Open)
end, "Door")

RegisterEvent(42, "Door", function()
    evt.SetDoorState(32, DoorAction.Open)
end, "Door")

RegisterEvent(43, "Door", function()
    evt.SetDoorState(33, DoorAction.Open)
end, "Door")

RegisterEvent(44, "Door", function()
    evt.SetDoorState(34, DoorAction.Open)
end, "Door")

RegisterEvent(45, "Door", function()
    evt.SetDoorState(35, DoorAction.Open)
end, "Door")

RegisterEvent(46, "Door", function()
    evt.SetDoorState(36, DoorAction.Open)
end, "Door")

RegisterEvent(47, "Door", function()
    evt.SetDoorState(37, DoorAction.Open)
end, "Door")

RegisterEvent(48, "Door", function()
    evt.SetDoorState(38, DoorAction.Open)
end, "Door")

RegisterEvent(49, "Door", function()
    evt.SetDoorState(39, DoorAction.Open)
end, "Door")

RegisterEvent(50, "Door", function()
    evt.SetDoorState(40, DoorAction.Open)
end, "Door")

RegisterEvent(51, "Door", function()
    evt.SetDoorState(41, DoorAction.Open)
end, "Door")

RegisterEvent(52, "Door", function()
    evt.SetDoorState(42, DoorAction.Open)
end, "Door")

RegisterEvent(53, "Door", function()
    evt.SetDoorState(43, DoorAction.Open)
end, "Door")

RegisterEvent(54, "Door", function()
    evt.SetDoorState(44, DoorAction.Open)
end, "Door")

RegisterEvent(55, "Door", function()
    evt.SetDoorState(45, DoorAction.Open)
end, "Door")

RegisterEvent(56, "Door", function()
    evt.SetDoorState(46, DoorAction.Open)
end, "Door")

RegisterEvent(57, "Door", function()
    evt.SetDoorState(47, DoorAction.Open)
end, "Door")

RegisterEvent(58, "Door", function()
    evt.SetDoorState(48, DoorAction.Open)
end, "Door")

RegisterEvent(59, "Door", function()
    evt.SetDoorState(49, DoorAction.Open)
end, "Door")

RegisterEvent(60, "Door", function()
    evt.SetDoorState(50, DoorAction.Open)
end, "Door")

RegisterEvent(61, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(52, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(52, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(52, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(34) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229)) -- You have Pissed off the Necros
        SetValue(Counter(9), 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(51, DoorAction.Open)
        evt.SetDoorState(52, DoorAction.Open)
    else
        evt.SpeakNPC(34) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(62, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(53, DoorAction.Open)
        evt.SetDoorState(54, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        evt.SetDoorState(53, DoorAction.Open)
        evt.SetDoorState(54, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(53, DoorAction.Open)
        evt.SetDoorState(54, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(34) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229)) -- You have Pissed off the Necros
        SetValue(Counter(9), 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(53, DoorAction.Open)
        evt.SetDoorState(54, DoorAction.Open)
    else
        evt.SpeakNPC(34) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(63, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetDoorState(56, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetDoorState(56, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetDoorState(56, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(34) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229)) -- You have Pissed off the Necros
        SetValue(Counter(9), 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(55, DoorAction.Open)
        evt.SetDoorState(56, DoorAction.Open)
    else
        evt.SpeakNPC(34) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(64, "Door", function()
    if IsAtLeast(MapVar(11), 2) then
        evt.SetDoorState(57, DoorAction.Open)
        evt.SetDoorState(58, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(229)) then -- You have Pissed off the Necros
        evt.SetDoorState(57, DoorAction.Open)
        evt.SetDoorState(58, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(57, DoorAction.Open)
        evt.SetDoorState(58, DoorAction.Open)
        return
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        if not IsAtLeast(MapVar(11), 1) then
            SetValue(MapVar(11), 1)
            evt.SpeakNPC(34) -- Guard
            evt.FaceAnimation(FaceAnimation.DoorLocked)
            return
        end
        SetQBit(QBit(229)) -- You have Pissed off the Necros
        SetValue(Counter(9), 0)
        evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
        evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
        SetValue(MapVar(11), 2)
        evt.SetDoorState(57, DoorAction.Open)
        evt.SetDoorState(58, DoorAction.Open)
    else
        evt.SpeakNPC(34) -- Guard
        evt.FaceAnimation(FaceAnimation.DoorLocked)
    end
return
end, "Door")

RegisterEvent(65, "Door", function()
    evt.SetDoorState(59, DoorAction.Open)
    evt.SetDoorState(60, DoorAction.Open)
end, "Door")

RegisterEvent(66, "Door", function()
    evt.SetDoorState(61, DoorAction.Open)
    evt.SetDoorState(62, DoorAction.Open)
end, "Door")

RegisterEvent(81, "Chest", function()
    evt.OpenChest(0)
end, "Chest")

RegisterEvent(82, "Chest", function()
    evt.OpenChest(1)
end, "Chest")

RegisterEvent(83, "Chest", function()
    evt.OpenChest(2)
end, "Chest")

RegisterEvent(84, "Chest", function()
    evt.OpenChest(3)
end, "Chest")

RegisterEvent(85, "Chest", function()
    evt.OpenChest(4)
end, "Chest")

RegisterEvent(86, "Chest", function()
    evt.OpenChest(5)
end, "Chest")

RegisterEvent(87, "Chest", function()
    evt.OpenChest(6)
end, "Chest")

RegisterEvent(88, "Chest", function()
    evt.OpenChest(7)
end, "Chest")

RegisterEvent(89, "Chest", function()
    evt.OpenChest(8)
end, "Chest")

RegisterEvent(90, "Chest", function()
    evt.OpenChest(9)
end, "Chest")

RegisterEvent(91, "Chest", function()
    evt.OpenChest(10)
end, "Chest")

RegisterEvent(92, "Chest", function()
    evt.OpenChest(11)
end, "Chest")

RegisterEvent(93, "Chest", function()
    evt.OpenChest(12)
end, "Chest")

RegisterEvent(94, "Chest", function()
    evt.OpenChest(13)
end, "Chest")

RegisterEvent(95, "Chest", function()
    evt.OpenChest(14)
end, "Chest")

RegisterEvent(96, "Chest", function()
    evt.OpenChest(15)
end, "Chest")

RegisterEvent(97, "Chest", function()
    evt.OpenChest(16)
end, "Chest")

RegisterEvent(98, "Chest", function()
    evt.OpenChest(17)
end, "Chest")

RegisterEvent(99, "Chest", function()
    evt.OpenChest(18)
end, "Chest")

RegisterEvent(100, "Chest", function()
    evt.OpenChest(19)
end, "Chest")

RegisterEvent(131, "Legacy event 131", function()
    if IsQBitSet(QBit(27)) then return end -- Skeleton Transformer Destroyed.
    if not IsQBitSet(QBit(26)) then return end -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
    if not HasPlayer(34) then return end -- Dyson Leyland
    if not IsAtLeast(MapVar(21), 15) then return end
    if evt._IsNpcInParty(34) then
        SetQBit(QBit(27)) -- Skeleton Transformer Destroyed.
        evt.ShowMovie("\"skeltrans\"", true)
        evt.SetFacetBit(30, FacetBits.Untouchable, 1)
        evt.SetFacetBit(30, FacetBits.Invisible, 1)
    end
end)

RegisterEvent(201, "Sandro/Thant's Throne Room", function()
    if IsQBitSet(QBit(27)) then -- Skeleton Transformer Destroyed.
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsAtLeast(MapVar(11), 2) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(20)) then -- Allied with Temple of the Sun. Destroy the Skeleton Transformer done.
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(19)) then -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
        evt.EnterHouse(213) -- Sandro/Thant's Throne Room
        return
    else
        evt.ForPlayer(Players.All)
        if HasItem(604) then -- Nightshade Brazier
            RemoveItem(604) -- Nightshade Brazier
            ClearQBit(QBit(14)) -- Form an alliance with the Necromancers' Guild in Shadowspire. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Sandro (area 6) or when quest 15 is done.
            ClearQBit(QBit(15)) -- Form an alliance with the Temple of the Sun in Murmurwoods. - Given by Bastian Lourdrin (area 3). Activates Merchanthouse in Alvar. Taken by Oskar Tyre (area 7), or when quest 27 is done.
            ClearQBit(QBit(28)) -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
            ClearQBit(QBit(26)) -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
            SetQBit(QBit(19)) -- Allied with Necromancers Guild. Steal Nightshade Brazier done.
            evt.MoveNPC(10, 0) -- Thant -> removed
            evt.SetNPCTopic(9, 0, 0) -- Sandro topic 0 cleared
            evt.SetNPCTopic(9, 1, 101) -- Sandro topic 1: Thant
            evt.SetNPCGreeting(9, 32) -- Sandro greeting: Hah! The only advantage that the Sun Temple had against us is no more. With the Nightshade Brazier back in our possession, we no longer need worry about the daytime defense of Shadowspire. We can march our undead to their very doors. We will destroy their temple and wipe them from the face of Jadame! Now that the tide of battle has turned in our favor, we of the Necromancers' Guild can more generously consider the request made by our friend, Bastian Loudrin. Thant can take over here while I am away sitting on your alliance council.
            evt.ForPlayer(Players.All)
            SetAward(Award(10)) -- Formed an alliance with the Necromancers' Guild.
            AddValue(Experience, 12500)
            evt.ForPlayer(Players.Current)
            AddValue(Gold, 8000)
            evt.ShowMovie("\"nightshade\"", true)
            AddValue(History(12), 0)
            ClearQBit(QBit(203)) -- Nightshade Brazier - I lost it
        end
        evt.EnterHouse(213) -- Sandro/Thant's Throne Room
        return
    end
end, "Sandro/Thant's Throne Room")

RegisterEvent(203, "Dyson Leland's Room", function()
    SetValue(MapVar(31), 5)
    if IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
        if IsQBitSet(QBit(89)) and IsQBitSet(QBit(90)) then -- Dyson Leland talks to you about the Necromancers. For global event 97-100.
            evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
            if IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
                SetValue(MapVar(31), 4)
            end
            if not IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
                evt.SetNPCGreeting(11, 35) -- Dyson Leland greeting: Ah, you are sent by his high holiness…Oskar Tyre thinks to activate his agent. Though I would wish him no good, I will do as he asks. Yes, I have knowledge of the guild's Skeleton Transformer and believe I can destroy it. Very well, let us do this thing against the Necromancers' Guild. I will at least be able to strike against one of my enemies!
                evt.EnterHouse(754) -- Dyson Leland's Room
                return
            end
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36) -- Dyson Leland greeting: Hah! So both Sandro and Oskar Tyre seek to use me against the other. I have thought of the possibility of this occurring. I believe that if I were to strike against one, it would become impossible for me to strike the other.So I guess we have a choice--help the guild or the temple. Which? I don't know, as my hatred for both is equal. I suppose I'll have to do with a half measure of revenge.
                evt.EnterHouse(754) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34) -- Dyson Leland greeting: So, Sandro has asked you to strike a blow against the Sun Temple! Though I hate the guild. I would be willing to help you. Half a serving of revenge is better than none.
        else
        end
        evt.EnterHouse(754) -- Dyson Leland's Room
        return
    elseif IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
        if IsQBitSet(QBit(89)) and IsQBitSet(QBit(90)) then -- Dyson Leland talks to you about the Necromancers. For global event 97-100.
            evt.SetNPCTopic(11, 3, 634) -- Dyson Leland topic 3: Roster Join Event
            if IsQBitSet(QBit(26)) then -- Find the skeleton transformer in the Shadowspire Necromancers' Guild. Destroy it and return to Oskar Tyre. - Given and taken by Oskar Tyre (area 7). Taken when Qbit 29 set.
                SetValue(MapVar(31), 4)
            end
            if not IsQBitSet(QBit(28)) then -- Bring the Nightshade Brazier to the Necromancers' Guild leader, Sandro. The Brazier is in the Temple of the Sun. - Given and taken by Sandro (area 6). Taken when Qbit 27 set.
                evt.SetNPCGreeting(11, 35) -- Dyson Leland greeting: Ah, you are sent by his high holiness…Oskar Tyre thinks to activate his agent. Though I would wish him no good, I will do as he asks. Yes, I have knowledge of the guild's Skeleton Transformer and believe I can destroy it. Very well, let us do this thing against the Necromancers' Guild. I will at least be able to strike against one of my enemies!
                evt.EnterHouse(754) -- Dyson Leland's Room
                return
            end
            if not IsAtLeast(MapVar(31), 5) then
                evt.SetNPCGreeting(11, 36) -- Dyson Leland greeting: Hah! So both Sandro and Oskar Tyre seek to use me against the other. I have thought of the possibility of this occurring. I believe that if I were to strike against one, it would become impossible for me to strike the other.So I guess we have a choice--help the guild or the temple. Which? I don't know, as my hatred for both is equal. I suppose I'll have to do with a half measure of revenge.
                evt.EnterHouse(754) -- Dyson Leland's Room
                return
            end
            evt.SetNPCGreeting(11, 34) -- Dyson Leland greeting: So, Sandro has asked you to strike a blow against the Sun Temple! Though I hate the guild. I would be willing to help you. Half a serving of revenge is better than none.
        else
        end
        evt.EnterHouse(754) -- Dyson Leland's Room
        return
    else
        evt.EnterHouse(754) -- Dyson Leland's Room
        return
    end
end, "Dyson Leland's Room")

RegisterEvent(451, "Legacy event 451", function()
    if IsAtLeast(MapVar(11), 2) then return end
    SetValue(MapVar(11), 0)
end)

RegisterEvent(452, "Door", function()
    evt.SetDoorState(5, DoorAction.Open)
end, "Door")

RegisterEvent(453, "Legacy event 453", function()
    if IsAtLeast(Invisible, 0) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    evt.SpeakNPC(34) -- Guard
    SetValue(MapVar(11), 1)
end)

RegisterEvent(454, "Legacy event 454", function()
    if IsAtLeast(MapVar(11), 2) then return end
    if IsAtLeast(Invisible, 0) then return end
    evt.SetMonGroupBit(41, MonsterBits.Hostile, 1) -- actor group 41: Necromancer, spawn Necromancer (monster) A
    evt.SetMonGroupBit(42, MonsterBits.Hostile, 1) -- actor group 42: spawn Necromancer (monster) A
    evt.SetMonGroupBit(10, MonsterBits.Invisible, 0) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1) -- actor group 10: spawn Necromancer (monster) A, spawn Skeletons Archer A, spawn Vampire (monster) A
    SetValue(MapVar(11), 2)
    evt.SetDoorState(7, DoorAction.Open)
end)

RegisterEvent(501, "Leave the Necromancers' Guild", function()
    evt.MoveToMap(15620, -11571, 4480, 1536, 0, 0, 0, 1, "out06.odm") -- Shadowspire
end, "Leave the Necromancers' Guild")

