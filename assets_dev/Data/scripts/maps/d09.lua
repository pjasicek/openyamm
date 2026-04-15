-- Merchant House of Alvar
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {2, 3, 4, 5},
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

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterNoOpEvent(5, "Legacy event 5")

RegisterNoOpEvent(6, "Legacy event 6")

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterNoOpEvent(10, "Legacy event 10")

RegisterEvent(11, "Crate", function()
    evt.SetDoorState(1, 0)
    return
end, "Crate")

RegisterEvent(12, "Bookshelf", function()
    if not IsQBitSet(QBit(13)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    end
    evt.SetDoorState(2, 0)
    return
end, "Bookshelf")

RegisterEvent(13, "Door", function()
    evt.SetDoorState(3, 0)
    evt.SetDoorState(5, 0)
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

RegisterEvent(171, "Council Chamber Door", function()
    if IsQBitSet(QBit(57)) then
        evt.FaceAnimation(FaceAnimation.DoorLocked)
        return
    elseif IsQBitSet(QBit(37)) then
        evt.SetNPCTopic(53, 1, 111)
        evt.SetNPCTopic(65, 0, 118)
        evt.SetNPCTopic(66, 0, 125)
        evt.SetNPCTopic(67, 0, 132)
        evt.SetNPCTopic(68, 0, 139)
        evt.SetNPCTopic(69, 0, 146)
        evt.EnterHouse(175) -- Council Chamber Door
        return
    elseif IsQBitSet(QBit(34)) then
        evt.EnterHouse(175) -- Council Chamber Door
        return
    elseif IsQBitSet(QBit(19)) then
        if IsQBitSet(QBit(21)) then
            if IsQBitSet(QBit(23)) then
                SetQBit(QBit(34))
                evt.SetNPCTopic(53, 0, 106)
                evt.SetNPCTopic(53, 1, 108)
                evt.SetNPCTopic(65, 0, 117)
                evt.SetNPCTopic(66, 0, 124)
                evt.SetNPCTopic(67, 0, 131)
                evt.SetNPCTopic(68, 0, 138)
                evt.SetNPCTopic(69, 0, 145)
                ClearQBit(QBit(13))
            end
            evt.EnterHouse(175) -- Council Chamber Door
            return
        elseif IsQBitSet(QBit(22)) then
            if IsQBitSet(QBit(23)) then
                SetQBit(QBit(34))
                evt.SetNPCTopic(53, 0, 106)
                evt.SetNPCTopic(53, 1, 108)
                evt.SetNPCTopic(65, 0, 117)
                evt.SetNPCTopic(66, 0, 124)
                evt.SetNPCTopic(67, 0, 131)
                evt.SetNPCTopic(68, 0, 138)
                evt.SetNPCTopic(69, 0, 145)
                ClearQBit(QBit(13))
            end
            evt.EnterHouse(175) -- Council Chamber Door
            return
        else
            evt.EnterHouse(175) -- Council Chamber Door
            return
        end
    elseif IsQBitSet(QBit(20)) then
        if IsQBitSet(QBit(21)) then
            if IsQBitSet(QBit(23)) then
                SetQBit(QBit(34))
                evt.SetNPCTopic(53, 0, 106)
                evt.SetNPCTopic(53, 1, 108)
                evt.SetNPCTopic(65, 0, 117)
                evt.SetNPCTopic(66, 0, 124)
                evt.SetNPCTopic(67, 0, 131)
                evt.SetNPCTopic(68, 0, 138)
                evt.SetNPCTopic(69, 0, 145)
                ClearQBit(QBit(13))
            end
            evt.EnterHouse(175) -- Council Chamber Door
            return
        elseif IsQBitSet(QBit(22)) then
            if IsQBitSet(QBit(23)) then
                SetQBit(QBit(34))
                evt.SetNPCTopic(53, 0, 106)
                evt.SetNPCTopic(53, 1, 108)
                evt.SetNPCTopic(65, 0, 117)
                evt.SetNPCTopic(66, 0, 124)
                evt.SetNPCTopic(67, 0, 131)
                evt.SetNPCTopic(68, 0, 138)
                evt.SetNPCTopic(69, 0, 145)
                ClearQBit(QBit(13))
            end
            evt.EnterHouse(175) -- Council Chamber Door
            return
        else
            evt.EnterHouse(175) -- Council Chamber Door
            return
        end
    else
        evt.EnterHouse(175) -- Council Chamber Door
        return
    end
end, "Council Chamber Door")

RegisterEvent(452, "Bookshelf", function()
    if IsAtLeast(MapVar(54), 1) then return end
    local randomStep = PickRandomOption(452, 2, {2, 2, 2, 4, 15, 16})
    if randomStep == 2 then
        evt.GiveItem(3, ItemType.Scroll_)
        AddValue(MapVar(54), 1)
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(452, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(414), 414) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(479), 479) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(467), 467) -- Heal
        end
        local randomStep = PickRandomOption(452, 15, {15, 15, 15, 15, 16, 16})
        if randomStep == 15 then
            AddValue(MapVar(54), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(54), 1)
    end
    return
end, "Bookshelf")

RegisterEvent(453, "Bookshelf", function()
    if IsAtLeast(MapVar(41), 1) then return end
    AddValue(InventoryItem(744), 744) -- History of the Vault of Time
    AddValue(MapVar(41), 1)
    return
end, "Bookshelf")

RegisterEvent(454, "Bookshelf", function()
    if IsAtLeast(MapVar(51), 1) then return end
    local randomStep = PickRandomOption(454, 2, {2, 2, 2, 4, 15, 16})
    if randomStep == 2 then
        evt.GiveItem(3, ItemType.Scroll_)
        AddValue(MapVar(51), 1)
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(454, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(414), 414) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(479), 479) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(467), 467) -- Heal
        end
        local randomStep = PickRandomOption(454, 15, {15, 15, 15, 15, 16, 16})
        if randomStep == 15 then
            AddValue(MapVar(51), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(51), 1)
    end
    return
end, "Bookshelf")

RegisterEvent(455, "Bookshelf", function()
    if IsAtLeast(MapVar(52), 1) then return end
    local randomStep = PickRandomOption(455, 2, {2, 2, 2, 4, 15, 16})
    if randomStep == 2 then
        evt.GiveItem(5, ItemType.Scroll_)
        AddValue(MapVar(52), 1)
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(455, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(414), 414) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(479), 479) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(467), 467) -- Heal
        end
        local randomStep = PickRandomOption(455, 15, {15, 15, 15, 15, 16, 16})
        if randomStep == 15 then
            AddValue(MapVar(52), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(52), 1)
    end
    return
end, "Bookshelf")

RegisterEvent(456, "Bookshelf", function()
    if IsAtLeast(MapVar(53), 1) then return end
    local randomStep = PickRandomOption(456, 2, {2, 2, 2, 4, 15, 16})
    if randomStep == 2 then
        evt.GiveItem(2, ItemType.Scroll_)
        AddValue(MapVar(53), 1)
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(456, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(414), 414) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(479), 479) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(467), 467) -- Heal
        end
        local randomStep = PickRandomOption(456, 15, {15, 15, 15, 15, 16, 16})
        if randomStep == 15 then
            AddValue(MapVar(53), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(53), 1)
    end
    return
end, "Bookshelf")

RegisterEvent(457, "Bookshelf", function()
    if IsAtLeast(MapVar(55), 1) then return end
    local randomStep = PickRandomOption(457, 2, {2, 2, 2, 4, 15, 16})
    if randomStep == 2 then
        evt.GiveItem(2, ItemType.Scroll_)
        AddValue(MapVar(55), 1)
    elseif randomStep == 4 then
        local randomStep = PickRandomOption(457, 5, {5, 7, 9, 11, 13, 14})
        if randomStep == 5 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 7 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 9 then
            AddValue(InventoryItem(414), 414) -- Sparks
        elseif randomStep == 11 then
            AddValue(InventoryItem(479), 479) -- Dispel Magic
        elseif randomStep == 13 then
            AddValue(InventoryItem(467), 467) -- Heal
        end
        local randomStep = PickRandomOption(457, 15, {15, 15, 15, 15, 16, 16})
        if randomStep == 15 then
            AddValue(MapVar(55), 1)
        end
    elseif randomStep == 15 then
        AddValue(MapVar(55), 1)
    end
    return
end, "Bookshelf")

RegisterEvent(458, "Bookshelf", function()
    if IsAtLeast(MapVar(42), 1) then return end
    AddValue(InventoryItem(747), 747) -- Page Torn from a Book
    AddValue(MapVar(42), 1)
    return
end, "Bookshelf")

RegisterEvent(459, "Bookshelf", nil, "Bookshelf")

RegisterEvent(460, "Bookshelf", nil, "Bookshelf")

RegisterEvent(461, "Bookshelf", nil, "Bookshelf")

RegisterEvent(462, "Bookshelf", nil, "Bookshelf")

RegisterEvent(463, "Bookshelf", nil, "Bookshelf")

RegisterEvent(464, "Bookshelf", nil, "Bookshelf")

RegisterEvent(465, "Bookshelf", nil, "Bookshelf")

RegisterEvent(466, "Bookshelf", nil, "Bookshelf")

RegisterEvent(467, "Bookshelf", nil, "Bookshelf")

RegisterEvent(468, "Bookshelf", nil, "Bookshelf")

RegisterEvent(469, "Bookshelf", nil, "Bookshelf")

RegisterEvent(470, "Bookshelf", nil, "Bookshelf")

RegisterEvent(471, "Bookshelf", nil, "Bookshelf")

RegisterEvent(501, "Leave Merchant House of Alvar", function()
    evt.MoveToMap(12894, -12153, 257, 1536, 0, 0, 0, 0, "Out02.odm")
    return
end, "Leave Merchant House of Alvar")

RegisterEvent(502, "Leave Merchant House of Alvar", function()
    evt.MoveToMap(11284, -11009, 258, 1024, 0, 0, 0, 0, "Out02.odm")
    return
end, "Leave Merchant House of Alvar")

