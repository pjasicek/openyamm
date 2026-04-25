-- Escaton's Crystal
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
    textureNames = {"gcrysc1", "gcrysc2", "gcrysc3", "gcrysc4", "gcryswal"},
    spriteNames = {},
    castSpellIds = {},
    timers = {
    { eventId = 151, repeating = true, intervalGameMinutes = 0.5, remainingGameMinutes = 0.5 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    if not IsAtLeast(MapVar(12), 10) then
        evt.SetTexture(10, "gcryswal")
        evt.SetLight(10, 0)
        return
    end
    evt.SetTexture(10, "gcrysc4")
    evt.SetLight(10, 1)
    evt.SetTexture(14, "gcryswal")
    evt.SetTexture(15, "gcryswal")
    evt.SetTexture(16, "gcryswal")
    evt.SetLight(14, 0)
    evt.SetLight(15, 0)
    evt.SetLight(16, 0)
    return
end)

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, 0)
    return
end, "Door")

RegisterEvent(12, "Door", function()
    evt.SetDoorState(2, 0)
    return
end, "Door")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(3, 0)
    return
end, "Door")

RegisterEvent(14, "Door", function()
    evt.SetDoorState(4, 0)
    return
end, "Door")

RegisterEvent(15, "Door", function()
    evt.SetDoorState(5, 0)
    return
end, "Door")

RegisterEvent(16, "Door", function()
    evt.SetDoorState(6, 0)
    return
end, "Door")

RegisterEvent(17, "Door", function()
    evt.SetDoorState(7, 0)
    return
end, "Door")

RegisterEvent(18, "Door", function()
    evt.SetDoorState(8, 0)
    return
end, "Door")

RegisterEvent(19, "Door", function()
    evt.SetDoorState(9, 0)
    return
end, "Door")

RegisterEvent(20, "Door", function()
    evt.SetDoorState(10, 0)
    return
end, "Door")

RegisterEvent(21, "Door", function()
    evt.SetDoorState(11, 0)
    return
end, "Door")

RegisterEvent(22, "Door", function()
    evt.SetDoorState(12, 0)
    return
end, "Door")

RegisterEvent(23, "Door", function()
    evt.SetDoorState(13, 0)
    return
end, "Door")

RegisterEvent(24, "Door", function()
    evt.SetDoorState(14, 0)
    return
end, "Door")

RegisterEvent(25, "Door", function()
    evt.SetDoorState(15, 0)
    return
end, "Door")

RegisterEvent(26, "Door", function()
    evt.SetDoorState(16, 0)
    return
end, "Door")

RegisterEvent(27, "Door", function()
    evt.SetDoorState(17, 0)
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

RegisterEvent(151, "Legacy event 151", function()
    if IsAtLeast(MapVar(11), 10) then
        SetValue(MapVar(11), 0)
        evt.SetTexture(11, "gcryswal")
        evt.SetTexture(12, "gcryswal")
        evt.SetTexture(13, "gcryswal")
        return
    elseif IsAtLeast(MapVar(11), 1) then
        if IsAtLeast(MapVar(11), 9) then
            evt.SetTexture(11, "gcrysc3")
            evt.SetTexture(12, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(475, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 8) then
            evt.SetTexture(13, "gcrysc2")
            evt.SetTexture(11, "gcryswal")
            evt.SetTexture(12, "gcryswal")
            evt.PlaySound(476, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 7) then
            evt.SetTexture(11, "gcrysc3")
            evt.SetTexture(12, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(475, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 6) then
            evt.SetTexture(13, "gcrysc2")
            evt.SetTexture(11, "gcryswal")
            evt.SetTexture(12, "gcryswal")
            evt.PlaySound(476, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 5) then
            evt.SetTexture(12, "gcrysc1")
            evt.SetTexture(11, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(477, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 4) then
            evt.SetTexture(11, "gcrysc3")
            evt.SetTexture(12, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(475, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 3) then
            evt.SetTexture(12, "gcrysc1")
            evt.SetTexture(11, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(477, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 2) then
            evt.SetTexture(13, "gcrysc2")
            evt.SetTexture(11, "gcryswal")
            evt.SetTexture(12, "gcryswal")
            evt.PlaySound(476, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        elseif IsAtLeast(MapVar(11), 1) then
            evt.SetTexture(11, "gcrysc3")
            evt.SetTexture(12, "gcryswal")
            evt.SetTexture(13, "gcryswal")
            evt.PlaySound(475, -14194, -3197)
            AddValue(MapVar(11), 1)
            return
        else
            return
        end
    else
        return
    end
end)

RegisterEvent(152, "Legacy event 152", function()
    if IsAtLeast(MapVar(12), 10) then return end
    if IsAtLeast(MapVar(11), 1) then return end
    SetValue(MapVar(11), 1)
    SetValue(MapVar(12), 1)
    return
end)

RegisterEvent(153, "Legacy event 153", function()
    if IsAtLeast(MapVar(12), 10) then
        return
    elseif IsAtLeast(MapVar(12), 9) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 1)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(475, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 8) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 7) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 1)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(475, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 6) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 5) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 4) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 1)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(475, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 3) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 2) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 1) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 1)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(475, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    else
        return
    end
end)

RegisterEvent(154, "Legacy event 154", function()
    if IsAtLeast(MapVar(12), 10) then
        return
    elseif IsAtLeast(MapVar(12), 9) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 8) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(16, "gcrysc2")
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetLight(16, 1)
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.PlaySound(476, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 7) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 6) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(16, "gcrysc2")
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetLight(16, 1)
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.PlaySound(476, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 5) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 4) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 3) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 2) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(16, "gcrysc2")
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetLight(16, 1)
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.PlaySound(476, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 1) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    else
        return
    end
end)

RegisterEvent(155, "Legacy event 155", function()
    if IsAtLeast(MapVar(12), 10) then
        return
    elseif IsAtLeast(MapVar(12), 9) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 8) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 7) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 6) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 5) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(15, 1)
        evt.SetLight(14, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(476, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 4) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 3) then
        AddValue(MapVar(12), 1)
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(15, 1)
        evt.SetLight(14, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(476, -14194, -3197)
        if not IsAtLeast(MapVar(12), 10) then return end
        evt.SetTexture(10, "gcrysc4")
        evt.SetLight(10, 1)
        evt.SetTexture(14, "gcryswal")
        evt.SetTexture(15, "gcryswal")
        evt.SetTexture(16, "gcryswal")
        evt.SetLight(14, 0)
        evt.SetLight(15, 0)
        evt.SetLight(16, 0)
        evt.PlaySound(474, -14244, -2307)
        return
    elseif IsAtLeast(MapVar(12), 2) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    elseif IsAtLeast(MapVar(12), 1) then
        evt.SetTexture(14, "gcrysc3")
        evt.SetTexture(15, "gcrysc1")
        evt.SetTexture(16, "gcrysc2")
        SetValue(MapVar(12), 1)
        evt.SetLight(14, 1)
        evt.SetLight(15, 1)
        evt.SetLight(16, 1)
        evt.PlaySound(358, -14194, -3197)
        return
    else
        return
    end
end)

RegisterEvent(501, "Leave Escaton's Crystal", function()
    evt.MoveToMap(15574, -9880, 321, 2047, 0, 0, 0, 0, "Out02.odm")
    return
end, "Leave Escaton's Crystal")

RegisterEvent(502, "Leave Escaton's Crystal", function()
    if not IsAtLeast(MapVar(12), 10) then return end
    evt.MoveToMap(1395, 20751, 1152, 1536, 0, 0, 0, 0, "pbp.odm")
    return
end, "Leave Escaton's Crystal")

