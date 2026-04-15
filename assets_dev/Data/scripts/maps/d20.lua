-- Mad Necromancer's Lab
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
    castSpellIds = {6, 39},
    timers = {
    },
})

RegisterNoOpEvent(1, "Legacy event 1")

RegisterNoOpEvent(2, "Legacy event 2")

RegisterNoOpEvent(3, "Legacy event 3")

RegisterNoOpEvent(4, "Legacy event 4")

RegisterEvent(5, "Legacy event 5", function()
    evt.SetMonGroupBit(10, MonsterBits.Hostile, 1)
    return
end)

RegisterEvent(6, "Legacy event 6", function()
    evt.ForPlayer(Players.All)
    if not HasItem(539) then return end -- Ebonest
    SetQBit(QBit(199))
    return
end)

RegisterNoOpEvent(7, "Legacy event 7")

RegisterNoOpEvent(8, "Legacy event 8")

RegisterNoOpEvent(9, "Legacy event 9")

RegisterEvent(10, "Legacy event 10", function()
    if not IsQBitSet(QBit(71)) then return end
    evt.SetMonGroupBit(10, MonsterBits.Invisible, 1)
    return
end)

RegisterEvent(11, "Door", function()
    evt.SetDoorState(1, 2)
    return
end, "Door")

RegisterEvent(12, "Button", function()
    evt.SetDoorState(2, 2)
    evt.SetDoorState(1, 2)
    return
end, "Button")

RegisterEvent(13, "Button", function()
    evt.SetDoorState(3, 2)
    evt.SetDoorState(1, 2)
    return
end, "Button")

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

RegisterEvent(61, "Door", function()
    evt.SetDoorState(51, 0)
    evt.SetDoorState(52, 0)
    return
end, "Door")

RegisterEvent(62, "Door", function()
    evt.SetDoorState(53, 0)
    evt.SetDoorState(54, 0)
    return
end, "Door")

RegisterEvent(63, "Door", function()
    evt.SetDoorState(55, 0)
    evt.SetDoorState(56, 0)
    return
end, "Door")

RegisterEvent(64, "Door", function()
    evt.SetDoorState(57, 0)
    evt.SetDoorState(58, 0)
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

RegisterEvent(101, "Legacy event 101", nil)

RegisterEvent(102, "Legacy event 102", function()
    evt.CastSpell(39, 20, 4, -1018, 3344, -862, 890, 3344, -862) -- Blades
    evt.CastSpell(39, 20, 4, 890, 3344, -862, -1018, 3344, -862) -- Blades
    return
end)

RegisterEvent(103, "Legacy event 103", function()
    evt.CastSpell(6, 20, 4, 1498, 2195, -560, 1498, 2195, -1024) -- Fireball
    evt.CastSpell(6, 20, 4, 2552, 2195, -560, 2552, 2195, -1024) -- Fireball
    return
end)

RegisterEvent(104, "Legacy event 104", nil)

RegisterEvent(105, "Legacy event 105", nil)

RegisterEvent(106, "Legacy event 106", nil)

RegisterEvent(131, "Legacy event 131", function()
    if not IsQBitSet(QBit(435)) then
        evt.SpeakNPC(295) -- Blazen Stormlance
        return
    end
    evt.FaceAnimation(FaceAnimation.DoorLocked)
    return
end)

RegisterEvent(451, "Take a Drink", function()
    evt.StatusText("Refreshing !")
    return
end, "Take a Drink")

RegisterEvent(452, "Bookshelf", function()
    if not IsAtLeast(MapVar(41), 3) then
        local randomStep = PickRandomOption(452, 2, {3, 5, 7, 9, 11, 14})
        if randomStep == 3 then
            evt.GiveItem(5, ItemType.Scroll_, 368) -- Body Resistance
        elseif randomStep == 5 then
            evt.GiveItem(5, ItemType.Scroll_, 357) -- Mind Resistance
        elseif randomStep == 7 then
            evt.GiveItem(5, ItemType.Scroll_, 346) -- Fate
        elseif randomStep == 9 then
            evt.GiveItem(5, ItemType.Scroll_, 335) -- Earth Resistance
        elseif randomStep == 11 then
            evt.GiveItem(5, ItemType.Scroll_, 302) -- Fire Resistance
        elseif randomStep == 14 then
        end
        AddValue(MapVar(41), 1)
        return
    end
    AddValue(MapVar(41), 1)
    return
end, "Bookshelf")

RegisterEvent(453, "Bookshelf", function()
    if not IsAtLeast(MapVar(42), 3) then
        local randomStep = PickRandomOption(453, 2, {3, 5, 7, 9, 11, 14})
        if randomStep == 3 then
            evt.GiveItem(5, ItemType.Scroll_, 334) -- Slow
        elseif randomStep == 5 then
            evt.GiveItem(5, ItemType.Scroll_, 355) -- Telepathy
        elseif randomStep == 7 then
            evt.GiveItem(5, ItemType.Scroll_, 356) -- Remove Fear
        elseif randomStep == 9 then
            evt.GiveItem(5, ItemType.Scroll_, 357) -- Mind Resistance
        elseif randomStep == 11 then
            evt.GiveItem(5, ItemType.Scroll_, 367) -- Heal
        elseif randomStep == 14 then
        end
        AddValue(MapVar(42), 1)
        return
    end
    AddValue(MapVar(42), 1)
    return
end, "Bookshelf")

RegisterEvent(454, "Bookshelf", function()
    if not IsAtLeast(MapVar(43), 1) then
        local randomStep = PickRandomOption(454, 2, {3, 5, 7, 9, 11, 14})
        if randomStep == 3 then
            AddValue(InventoryItem(424), 424) -- Water Resistance
        elseif randomStep == 5 then
            AddValue(InventoryItem(435), 435) -- Earth Resistance
        elseif randomStep == 7 then
            AddValue(InventoryItem(446), 446) -- Fate
        elseif randomStep == 9 then
            AddValue(InventoryItem(457), 457) -- Mind Resistance
        elseif randomStep == 11 then
            AddValue(InventoryItem(468), 468) -- Body Resistance
        elseif randomStep == 14 then
        end
        AddValue(MapVar(43), 1)
        return
    end
    AddValue(MapVar(43), 1)
    return
end, "Bookshelf")

RegisterEvent(455, "Bookshelf", function()
    if not IsAtLeast(MapVar(44), 1) then
        local randomStep = PickRandomOption(455, 2, {3, 5, 7, 9, 11, 14})
        if randomStep == 3 then
            AddValue(InventoryItem(401), 401) -- Fire Bolt
        elseif randomStep == 5 then
            AddValue(InventoryItem(412), 412) -- Feather Fall
        elseif randomStep == 7 then
            AddValue(InventoryItem(411), 411) -- Wizard Eye
        elseif randomStep == 9 then
            AddValue(InventoryItem(423), 423) -- Poison Spray
        elseif randomStep == 11 then
            AddValue(InventoryItem(434), 434) -- Slow
        elseif randomStep == 14 then
        end
        AddValue(MapVar(44), 1)
        return
    end
    AddValue(MapVar(44), 1)
    return
end, "Bookshelf")

RegisterEvent(501, "Leave the Mad Necromancer's Lab", function()
    evt.MoveToMap(-13071, 16397, 1057, 1536, 0, 0, 0, 0, "Out06.odm")
    return
end, "Leave the Mad Necromancer's Lab")

