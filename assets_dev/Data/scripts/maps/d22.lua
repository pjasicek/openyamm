-- Temple of the Sun
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
    { eventId = 451, repeating = true, intervalGameMinutes = 5, remainingGameMinutes = 5 },
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    if IsQBitSet(QBit(19)) then
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 1)
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 1)
        if not IsAtLeast(Player(34), 34) then
            evt.SetFacetBit(5, FacetBits.IsSecret, 0)
            return
        end
        if evt._IsNpcInParty(34) then
            if IsQBitSet(QBit(28)) then
                evt.SetFacetBit(5, FacetBits.IsSecret, 1)
                return
            end
        end
        evt.SetFacetBit(5, FacetBits.IsSecret, 0)
        return
    elseif IsQBitSet(QBit(230)) then
        if not IsAtLeast(Counter(10), 1344) then
            evt.SetMonGroupBit(39, MonsterBits.Hostile, 1)
            evt.SetMonGroupBit(40, MonsterBits.Hostile, 1)
            if not IsAtLeast(Player(34), 34) then
                evt.SetFacetBit(5, FacetBits.IsSecret, 0)
                return
            end
            if evt._IsNpcInParty(34) then
                if IsQBitSet(QBit(28)) then
                    evt.SetFacetBit(5, FacetBits.IsSecret, 1)
                    return
                end
            end
            evt.SetFacetBit(5, FacetBits.IsSecret, 0)
            return
        end
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 0)
        ClearQBit(QBit(230))
    else
        evt.SetMonGroupBit(39, MonsterBits.Hostile, 0)
        evt.SetMonGroupBit(40, MonsterBits.Hostile, 0)
        ClearQBit(QBit(230))
    end
if not IsAtLeast(Player(34), 34) then
    evt.SetFacetBit(5, FacetBits.IsSecret, 0)
    return
end
if evt._IsNpcInParty(34) then
    if IsQBitSet(QBit(28)) then
        evt.SetFacetBit(5, FacetBits.IsSecret, 1)
        return
    end
end
evt.SetFacetBit(5, FacetBits.IsSecret, 0)
return
end)

RegisterEvent(6, "Legacy event 6", function()
    if IsQBitSet(QBit(20)) then
        evt.MoveNPC(37, 0)
        evt.MoveNPC(67, 175)
        if not IsQBitSet(QBit(230)) then return end
        return
    elseif IsQBitSet(QBit(230)) then
        return
    else
        return
    end
end)

RegisterEvent(7, "Legacy event 7", function()
    evt.ForPlayer(Players.All)
    if not HasItem(604) then return end -- Nightshade Brazier
    evt.SetDoorState(1, 1)
    evt.SetDoorState(3, 0)
    evt.SetDoorState(4, 0)
    SetQBit(QBit(230))
    evt.SetMonGroupBit(39, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(40, MonsterBits.Hostile, 1)
    SetQBit(QBit(203))
    return
end)

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

RegisterEvent(201, "Temple of the Sun Leader Room", function()
    if not IsQBitSet(QBit(19)) then
        evt.EnterHouse(182) -- Temple of the Sun Leader Room
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    return
end, "Temple of the Sun Leader Room")

RegisterEvent(451, "Legacy event 451", function()
    evt.ForPlayer(Players.All)
    if not HasItem(604) then return end -- Nightshade Brazier
    evt.SetDoorState(1, 1)
    evt.SetDoorState(3, 0)
    evt.SetDoorState(4, 0)
    SetQBit(QBit(230))
    evt.SetMonGroupBit(39, MonsterBits.Hostile, 1)
    evt.SetMonGroupBit(40, MonsterBits.Hostile, 1)
    SetQBit(QBit(203))
    return
end)

RegisterEvent(452, "Legacy event 452", function()
    if not IsQBitSet(QBit(28)) then return end
    if not IsAtLeast(Player(34), 34) then return end
    evt.SetDoorState(1, 0)
    return
end)

RegisterEvent(501, "Leave the Temple of the Sun", function()
    evt.MoveToMap(-9754, -10226, 1890, 0, 0, 0, 0, 0, "Out07.odm")
    return
end, "Leave the Temple of the Sun")

