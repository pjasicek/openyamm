-- Avlee
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 250},
    onLeave = {},
    openedChestIds = {
    [151] = {1},
    [152] = {2},
    [153] = {3},
    [154] = {4},
    [155] = {5},
    [156] = {6},
    [157] = {7},
    [158] = {8},
    [159] = {9},
    [160] = {10},
    [161] = {11},
    [162] = {12},
    [163] = {13},
    [164] = {14},
    [165] = {15},
    [166] = {16},
    [167] = {17},
    [168] = {18},
    [169] = {19},
    [170] = {0},
    },
    textureNames = {},
    spriteNames = {"0", "7tree13", "7tree14", "7tree15", "7tree16", "7tree17", "7tree18", "7tree22", "7tree24", "7tree30", "tree37"},
    castSpellIds = {},
    timers = {
    },
})

RegisterEvent(1, "Legacy event 1", function()
    if IsQBitSet(QBit(611)) then return end -- Chose the path of Light
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1)
end)

RegisterEvent(3, "Avlee Outpost", function()
    evt.EnterHouse(56) -- Avlee Outpost
end, "Avlee Outpost")

RegisterEvent(4, "Avlee Outpost", nil, "Avlee Outpost")

RegisterEvent(5, "Plush Coaches", function()
    evt.EnterHouse(467) -- Plush Coaches
end, "Plush Coaches")

RegisterEvent(6, "Plush Coaches", nil, "Plush Coaches")

RegisterEvent(7, "Wind Runner", function()
    evt.EnterHouse(492) -- Wind Runner
end, "Wind Runner")

RegisterEvent(8, "Wind Runner", nil, "Wind Runner")

RegisterEvent(9, "Temple of Tranquility", function()
    evt.EnterHouse(320) -- Temple of Tranquility
end, "Temple of Tranquility")

RegisterEvent(10, "Temple of Tranquility", nil, "Temple of Tranquility")

RegisterEvent(11, "Avlee Gymnaisium", function()
    evt.EnterHouse(1578) -- Avlee Gymnaisium
end, "Avlee Gymnaisium")

RegisterEvent(12, "Avlee Gymnaisium", nil, "Avlee Gymnaisium")

RegisterEvent(13, "The Potted Pixie", function()
    evt.EnterHouse(251) -- The Potted Pixie
end, "The Potted Pixie")

RegisterEvent(14, "The Potted Pixie", nil, "The Potted Pixie")

RegisterEvent(15, "Halls of Gold", function()
    evt.EnterHouse(292) -- Halls of Gold
end, "Halls of Gold")

RegisterEvent(16, "Halls of Gold", nil, "Halls of Gold")

RegisterEvent(17, "Paramount Guild of Mind", function()
    evt.EnterHouse(161) -- Paramount Guild of Mind
end, "Paramount Guild of Mind")

RegisterEvent(18, "Paramount Guild of Mind", nil, "Paramount Guild of Mind")

RegisterEvent(19, "Paramount Guild of Body", function()
    evt.EnterHouse(167) -- Paramount Guild of Body
end, "Paramount Guild of Body")

RegisterEvent(20, "Paramount Guild of Body", nil, "Paramount Guild of Body")

RegisterEvent(21, "The Knocked Bow", function()
    evt.EnterHouse(16) -- The Knocked Bow
end, "The Knocked Bow")

RegisterEvent(22, "The Knocked Bow", nil, "The Knocked Bow")

RegisterEvent(51, "House", nil, "House")

RegisterEvent(52, "Featherwind Residence", function()
    evt.EnterHouse(1014) -- Featherwind Residence
end, "Featherwind Residence")

RegisterEvent(53, "Ravenhair Residence", function()
    evt.EnterHouse(1015) -- Ravenhair Residence
end, "Ravenhair Residence")

RegisterEvent(54, "Snick House", function()
    evt.EnterHouse(1020) -- Snick House
end, "Snick House")

RegisterEvent(55, "Infernon's House", function()
    evt.EnterHouse(1021) -- Infernon's House
end, "Infernon's House")

RegisterEvent(56, "Deerhunter Residence", function()
    evt.EnterHouse(1022) -- Deerhunter Residence
end, "Deerhunter Residence")

RegisterEvent(57, "Swiftfoot's House", function()
    evt.EnterHouse(1023) -- Swiftfoot's House
end, "Swiftfoot's House")

RegisterEvent(58, "Tempus' House", function()
    evt.EnterHouse(1140) -- Tempus' House
end, "Tempus' House")

RegisterEvent(59, "Kaine's", function()
    evt.EnterHouse(1141) -- Kaine's
end, "Kaine's")

RegisterEvent(60, "Apple Residence", function()
    evt.EnterHouse(1142) -- Apple Residence
end, "Apple Residence")

RegisterEvent(61, "Tent", nil, "Tent")

RegisterEvent(63, "Jillian's House", function()
    evt.EnterHouse(1016) -- Jillian's House
end, "Jillian's House")

RegisterEvent(64, "Greenstorm Residence", function()
    evt.EnterHouse(1017) -- Greenstorm Residence
end, "Greenstorm Residence")

RegisterEvent(67, "Brightspear Residence", function()
    evt.EnterHouse(1008) -- Brightspear Residence
end, "Brightspear Residence")

RegisterEvent(68, "Holden Residence", function()
    evt.EnterHouse(1009) -- Holden Residence
end, "Holden Residence")

RegisterEvent(151, "Chest ", function()
    evt.OpenChest(1)
end, "Chest ")

RegisterEvent(152, "Chest ", function()
    evt.OpenChest(2)
end, "Chest ")

RegisterEvent(153, "Chest ", function()
    evt.OpenChest(3)
end, "Chest ")

RegisterEvent(154, "Chest ", function()
    evt.OpenChest(4)
end, "Chest ")

RegisterEvent(155, "Chest ", function()
    evt.OpenChest(5)
end, "Chest ")

RegisterEvent(156, "Chest ", function()
    evt.OpenChest(6)
end, "Chest ")

RegisterEvent(157, "Chest ", function()
    evt.OpenChest(7)
end, "Chest ")

RegisterEvent(158, "Chest ", function()
    evt.OpenChest(8)
end, "Chest ")

RegisterEvent(159, "Chest ", function()
    evt.OpenChest(9)
end, "Chest ")

RegisterEvent(160, "Chest ", function()
    evt.OpenChest(10)
end, "Chest ")

RegisterEvent(161, "Chest ", function()
    evt.OpenChest(11)
end, "Chest ")

RegisterEvent(162, "Chest ", function()
    evt.OpenChest(12)
end, "Chest ")

RegisterEvent(163, "Chest ", function()
    evt.OpenChest(13)
end, "Chest ")

RegisterEvent(164, "Chest ", function()
    evt.OpenChest(14)
end, "Chest ")

RegisterEvent(165, "Chest ", function()
    evt.OpenChest(15)
end, "Chest ")

RegisterEvent(166, "Chest ", function()
    evt.OpenChest(16)
end, "Chest ")

RegisterEvent(167, "Chest ", function()
    evt.OpenChest(17)
end, "Chest ")

RegisterEvent(168, "Chest ", function()
    evt.OpenChest(18)
end, "Chest ")

RegisterEvent(169, "Chest ", function()
    evt.OpenChest(19)
end, "Chest ")

RegisterEvent(170, "Chest ", function()
    evt.OpenChest(0)
    if IsQBitSet(QBit(581)) then -- Placed Golem left arm
        return
    elseif IsQBitSet(QBit(734)) then -- Left arm - I lost it
        return
    else
        SetQBit(QBit(734)) -- Left arm - I lost it
        return
    end
end, "Chest ")

RegisterEvent(201, "Well", nil, "Well")

RegisterEvent(202, "Drink from the Well", function()
    if not IsAtLeast(MaxHealth, 0) then
        AddValue(CurrentHealth, 25)
        evt.StatusText("+25 Hit Points")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(203, "Drink from the Well", function()
    if not IsAtLeast(BankGold, 99) then
        if IsAtLeast(Gold, 199) then
            evt.StatusText("Refreshing!")
            return
        elseif IsAtLeast(MapVar(21), 1) then
            evt.StatusText("Refreshing!")
            return
        else
            AddValue(Gold, 200)
            SetValue(MapVar(21), 1)
            evt.StatusText("Refreshing!")
            return
        end
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(204, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(23)) then
        if not IsAutonoteSet(287) then -- 20 points of temporary Water resistance from the well in the northwest section of Spaward in Avlee.
            SetAutonote(287) -- 20 points of temporary Water resistance from the well in the northwest section of Spaward in Avlee.
        end
        AddValue(WaterResistanceBonus, 20)
        SetPlayerBit(PlayerBit(23))
        evt.StatusText("+20 Water Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(205, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(22)) then
        if not IsAutonoteSet(286) then -- 2 points of permanent Endurance from the well in the northeast section of Spaward in Avlee.
            SetAutonote(286) -- 2 points of permanent Endurance from the well in the northeast section of Spaward in Avlee.
        end
        AddValue(BaseEndurance, 2)
        SetPlayerBit(PlayerBit(22))
        evt.StatusText("+2 Endurance (Permanent)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(206, "Temple of Baa", nil, "Temple of Baa")

RegisterEvent(207, "Titan Stronghold", nil, "Titan Stronghold")

RegisterEvent(208, "Hall under the Hill", nil, "Hall under the Hill")

RegisterEvent(209, "Legacy event 209", nil)

RegisterEvent(250, "Legacy event 250", function()
    if evt.CheckSeason(2) then
        goto step_16
    end
    if evt.CheckSeason(3) then
        goto step_20
    end
    evt.SetSprite(5, 1, "7tree13")
    evt.SetSprite(6, 1, "7tree16")
    evt.SetSprite(7, 1, "7tree22")
    evt.SetSprite(10, 1, "0")
    goto step_36
    ::step_8::
    if evt.CheckSeason(1) then
        goto step_12
    end
    if evt.CheckSeason(0) then
        goto step_14
    end
    do return end
    ::step_12::
    evt.StatusText("You received an apple")
    goto step_35
    ::step_14::
    evt.StatusText("Fruit Tree")
    goto step_35
    ::step_16::
    evt.SetSprite(5, 1, "7tree14")
    evt.SetSprite(6, 1, "7tree17")
    goto step_23
    ::step_20::
    evt.SetSprite(5, 1, "7tree15")
    evt.SetSprite(6, 1, "7tree18")
    ::step_23::
    evt.SetSprite(7, 1, "7tree24")
    evt.SetSprite(10, 0, "0")
    evt.SetSprite(51, 1, "7tree30")
    evt.SetSprite(52, 1, "7tree30")
    evt.SetSprite(53, 1, "7tree30")
    evt.SetSprite(54, 1, "7tree30")
    evt.SetSprite(55, 1, "7tree30")
    evt.SetSprite(56, 1, "7tree30")
    evt.SetSprite(57, 1, "7tree30")
    evt.SetSprite(58, 1, "7tree30")
    evt.SetSprite(59, 1, "7tree30")
    evt.SetSprite(60, 1, "7tree30")
    ::step_35::
    do return end
    ::step_36::
    if IsAtLeast(MapVar(52), 1) then
        goto step_39
    end
    evt.SetSprite(51, 1, "0")
    goto step_40
    ::step_39::
    evt.SetSprite(51, 1, "0")
    ::step_40::
    if IsAtLeast(MapVar(53), 1) then
        goto step_43
    end
    evt.SetSprite(52, 1, "0")
    goto step_44
    ::step_43::
    evt.SetSprite(52, 1, "0")
    ::step_44::
    if IsAtLeast(MapVar(54), 1) then
        goto step_47
    end
    evt.SetSprite(53, 1, "0")
    goto step_48
    ::step_47::
    evt.SetSprite(53, 1, "0")
    ::step_48::
    if IsAtLeast(MapVar(55), 1) then
        goto step_51
    end
    evt.SetSprite(54, 1, "0")
    goto step_52
    ::step_51::
    evt.SetSprite(54, 1, "0")
    ::step_52::
    if IsAtLeast(MapVar(56), 1) then
        goto step_55
    end
    evt.SetSprite(55, 1, "0")
    goto step_56
    ::step_55::
    evt.SetSprite(55, 1, "0")
    ::step_56::
    if IsAtLeast(MapVar(57), 1) then
        goto step_59
    end
    evt.SetSprite(56, 1, "0")
    goto step_60
    ::step_59::
    evt.SetSprite(56, 1, "0")
    ::step_60::
    if IsAtLeast(MapVar(58), 1) then
        goto step_63
    end
    evt.SetSprite(57, 1, "0")
    goto step_64
    ::step_63::
    evt.SetSprite(57, 1, "0")
    ::step_64::
    if IsAtLeast(MapVar(59), 1) then
        goto step_67
    end
    evt.SetSprite(58, 1, "0")
    goto step_68
    ::step_67::
    evt.SetSprite(58, 1, "0")
    ::step_68::
    if IsAtLeast(MapVar(60), 1) then
        goto step_71
    end
    evt.SetSprite(59, 1, "0")
    goto step_72
    ::step_71::
    evt.SetSprite(59, 1, "0")
    ::step_72::
    if IsAtLeast(MapVar(61), 1) then
        goto step_75
    end
    evt.SetSprite(60, 1, "0")
    goto step_76
    ::step_75::
    evt.SetSprite(60, 1, "0")
    ::step_76::
    goto step_8
end)

RegisterEvent(251, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(52), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(52), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(51, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(252, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(53), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(53), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(52, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(253, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(54), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(54), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(53, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(254, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(55), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(55), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(54, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(255, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(56), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(56), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(55, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(256, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(57), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(57), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(56, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(257, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(58), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(58), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(57, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(258, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(59), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(59), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(58, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(259, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(60), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(60), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(59, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(260, "Fruit Tree", function()
    if evt.CheckSeason(3) then return end
    if evt.CheckSeason(2) then return end
    if IsAtLeast(MapVar(61), 1) then return end
    AddValue(InventoryItem(1432), 1432) -- Red Apple
    SetValue(MapVar(61), 1)
    evt.StatusText("You received an apple")
    evt.SetSprite(60, 1, "tree37")
end, "Fruit Tree")

RegisterEvent(401, "Altar", function()
    if not IsQBitSet(QBit(561)) then return end -- Visit the three stonehenge monoliths in Tatalia, the Evenmorn Islands, and Avlee, then return to Anthony Green in the Tularean Forest.
    if IsQBitSet(QBit(562)) then -- Visited all stonehenges
        return
    elseif IsQBitSet(QBit(565)) then -- Visited stonehenge 3 (area 14)
        return
    else
        evt.ForPlayer(Players.All)
        SetQBit(QBit(565)) -- Visited stonehenge 3 (area 14)
        evt.ForPlayer(Players.All)
        SetQBit(QBit(757)) -- Congratulations - For Blinging
        ClearQBit(QBit(757)) -- Congratulations - For Blinging
        if IsQBitSet(QBit(563)) and IsQBitSet(QBit(564)) then -- Visited stonehenge 1 (area 9)
            evt.ForPlayer(Players.All)
            SetQBit(QBit(562)) -- Visited all stonehenges
        else
        end
        return
    end
end, "Altar")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if IsQBitSet(QBit(713)) then return end -- Placed item 617 in out14(statue)
    if not IsQBitSet(QBit(712)) then return end -- Retrieve the three statuettes and place them on the shrines in the Bracada Desert, Tatalia, and Avlee, then return to Thom Lumbra in the Tularean Forest.
    evt.ForPlayer(Players.All)
    if HasItem(1419) then -- Knight Statuette
        evt.SetSprite(25, 1, "0")
        RemoveItem(1419) -- Knight Statuette
        SetQBit(QBit(713)) -- Placed item 617 in out14(statue)
    end
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(688)) then return end -- Visited Obelisk in Area 14
    evt.StatusText("__dn_r_n")
    SetAutonote(321) -- Obelisk message #13: __dn_r_n
    evt.ForPlayer(Players.All)
    SetQBit(QBit(688)) -- Visited Obelisk in Area 14
end, "Obelisk")

RegisterEvent(454, "Avlee", nil, "Avlee")

RegisterEvent(455, "East to the Tularean Forest", nil, "East to the Tularean Forest")

RegisterEvent(456, "Docks", nil, "Docks")

RegisterEvent(501, "Enter the The Titan Stronghold", function()
    evt.MoveToMap(-1707, -21848, -1007, 512, 0, 0, 157, 1, "\t7d09.blv")
end, "Enter the The Titan Stronghold")

RegisterEvent(502, "Enter the Temple of Baa", function()
    evt.MoveToMap(1, -2772, 1, 512, 0, 0, 158, 1, "\td04.blv")
end, "Enter the Temple of Baa")

RegisterEvent(503, "Enter the Hall under the Hill", function()
    evt.MoveToMap(-1114, 2778, 1, 1280, 0, 0, 159, 1, "7d22.blv")
end, "Enter the Hall under the Hill")

