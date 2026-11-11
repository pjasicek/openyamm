-- The Barrow Downs
-- generated from legacy EVT/STR

SetMapMetadata({
    onLoad = {1, 250},
    onLeave = {},
    openedChestIds = {
    [201] = {1},
    [202] = {2},
    [203] = {3},
    [204] = {4},
    [205] = {5},
    [206] = {6},
    [207] = {7},
    [208] = {8},
    [209] = {9},
    [210] = {10},
    [211] = {11},
    [212] = {12},
    [213] = {13},
    [214] = {14},
    [215] = {15},
    [216] = {16},
    [217] = {17},
    [218] = {18},
    [219] = {19},
    [220] = {0},
    },
    contextActions = {
    [3] = { kind = "enter_house", source = "opcode", houseId = 249, targetName = "Miner's Only" },
    [101] = { kind = "enter_house", source = "opcode", houseId = 1151, targetName = "Dallia's Home" },
    [102] = { kind = "enter_house", source = "opcode", houseId = 1152, targetName = "Gemstone Residence" },
    [103] = { kind = "enter_house", source = "opcode", houseId = 1153, targetName = "Feldspar's Home" },
    [104] = { kind = "enter_house", source = "opcode", houseId = 1154, targetName = "Fissure Residence" },
    [105] = { kind = "enter_house", source = "opcode", houseId = 1155, targetName = "Garnet House" },
    [106] = { kind = "enter_house", source = "opcode", houseId = 1156, targetName = "Rivenrock Residence" },
    [201] = { kind = "open_chest", source = "opcode", chestIds = {1} },
    [202] = { kind = "open_chest", source = "opcode", chestIds = {2} },
    [203] = { kind = "open_chest", source = "opcode", chestIds = {3} },
    [204] = { kind = "open_chest", source = "opcode", chestIds = {4} },
    [205] = { kind = "open_chest", source = "opcode", chestIds = {5} },
    [206] = { kind = "open_chest", source = "opcode", chestIds = {6} },
    [207] = { kind = "open_chest", source = "opcode", chestIds = {7} },
    [208] = { kind = "open_chest", source = "opcode", chestIds = {8} },
    [209] = { kind = "open_chest", source = "opcode", chestIds = {9} },
    [210] = { kind = "open_chest", source = "opcode", chestIds = {10} },
    [211] = { kind = "open_chest", source = "opcode", chestIds = {11} },
    [212] = { kind = "open_chest", source = "opcode", chestIds = {12} },
    [213] = { kind = "open_chest", source = "opcode", chestIds = {13} },
    [214] = { kind = "open_chest", source = "opcode", chestIds = {14} },
    [215] = { kind = "open_chest", source = "opcode", chestIds = {15} },
    [216] = { kind = "open_chest", source = "opcode", chestIds = {16} },
    [217] = { kind = "open_chest", source = "opcode", chestIds = {17} },
    [218] = { kind = "open_chest", source = "opcode", chestIds = {18} },
    [219] = { kind = "open_chest", source = "opcode", chestIds = {19} },
    [220] = { kind = "open_chest", source = "opcode", chestIds = {0} },
    [251] = { kind = "generic_event", source = "opcode" },
    [252] = { kind = "generic_event", source = "opcode" },
    [253] = { kind = "generic_event", source = "opcode" },
    [254] = { kind = "generic_event", source = "opcode" },
    [255] = { kind = "generic_event", source = "opcode" },
    [256] = { kind = "generic_event", source = "opcode" },
    [321] = { kind = "well", source = "title" },
    [322] = { kind = "well", source = "title" },
    [452] = { kind = "shrine", source = "title" },
    [453] = { kind = "obelisk", source = "title" },
    [501] = { kind = "enter_dungeon", source = "opcode", targetMap = "7d24.blv", targetName = "Stone City" },
    [502] = { kind = "enter_dungeon", source = "opcode", targetMap = "7d37.blv", targetName = "The Haunted Mansion" },
    [503] = { kind = "enter_dungeon", source = "opcode", targetMap = "mdt01.blv", targetName = "Barrow IX" },
    [504] = { kind = "enter_dungeon", source = "opcode", targetMap = "mdr01.blv", targetName = "Barrow X" },
    [505] = { kind = "enter_dungeon", source = "opcode", targetMap = "mdk01.blv", targetName = "Barrow VII" },
    },
    learnedEffect = {
    [321] = { autonote = 282, effect = "+25 Fire Resistance (Temporary)" },
    },
    textureNames = {},
    spriteNames = {"0", "7tree13", "7tree14", "7tree15", "7tree16", "7tree17", "7tree18", "7tree22", "7tree24", "7tree30", "tree37"},
    castSpellIds = {},
    timers = {
    { eventId = 65535, sourceEventId = 321, triggerStep = 9, origin = "legacy", triggerKind = "long", scheduleKind = "daily", startHour = 1, startMinute = 0, startSecond = 0 },
    },
})

RegisterEvent(1, nil, function()
    evt.SetMonGroupBit(56, MonsterBits.Hostile, 1) -- actor group 56: spawn AGog A, spawn Gargoyle A, spawn Ghost A
end)

RegisterEvent(3, "Miner's Only", function()
    evt.EnterHouse(249) -- Miner's Only
end, "Miner's Only")

RegisterEvent(4, "Miner's Only", nil, "Miner's Only")

RegisterEvent(100, "House", nil, "House")

RegisterEvent(101, "Dallia's Home", function()
    evt.EnterHouse(1151) -- Dallia's Home
end, "Dallia's Home")

RegisterEvent(102, "Gemstone Residence", function()
    evt.EnterHouse(1152) -- Gemstone Residence
end, "Gemstone Residence")

RegisterEvent(103, "Feldspar's Home", function()
    evt.EnterHouse(1153) -- Feldspar's Home
end, "Feldspar's Home")

RegisterEvent(104, "Fissure Residence", function()
    evt.EnterHouse(1154) -- Fissure Residence
end, "Fissure Residence")

RegisterEvent(105, "Garnet House", function()
    evt.EnterHouse(1155) -- Garnet House
end, "Garnet House")

RegisterEvent(106, "Rivenrock Residence", function()
    evt.EnterHouse(1156) -- Rivenrock Residence
end, "Rivenrock Residence")

RegisterEvent(201, "Chest ", function()
    evt.OpenChest(1)
end, "Chest ")

RegisterEvent(202, "Chest ", function()
    evt.OpenChest(2)
end, "Chest ")

RegisterEvent(203, "Chest ", function()
    evt.OpenChest(3)
end, "Chest ")

RegisterEvent(204, "Chest ", function()
    evt.OpenChest(4)
end, "Chest ")

RegisterEvent(205, "Chest ", function()
    evt.OpenChest(5)
end, "Chest ")

RegisterEvent(206, "Chest ", function()
    evt.OpenChest(6)
end, "Chest ")

RegisterEvent(207, "Chest ", function()
    evt.OpenChest(7)
end, "Chest ")

RegisterEvent(208, "Chest ", function()
    evt.OpenChest(8)
    evt.MoveToMap(3072, -416, 0, 0, 0, 0, 0, 0)
end, "Chest ")

RegisterEvent(209, "Chest ", function()
    evt.OpenChest(9)
end, "Chest ")

RegisterEvent(210, "Chest ", function()
    evt.OpenChest(10)
end, "Chest ")

RegisterEvent(211, "Chest ", function()
    evt.OpenChest(11)
end, "Chest ")

RegisterEvent(212, "Chest ", function()
    evt.OpenChest(12)
end, "Chest ")

RegisterEvent(213, "Chest ", function()
    evt.OpenChest(13)
end, "Chest ")

RegisterEvent(214, "Chest ", function()
    evt.OpenChest(14)
end, "Chest ")

RegisterEvent(215, "Chest ", function()
    evt.OpenChest(15)
end, "Chest ")

RegisterEvent(216, "Chest ", function()
    evt.OpenChest(16)
end, "Chest ")

RegisterEvent(217, "Chest ", function()
    evt.OpenChest(17)
end, "Chest ")

RegisterEvent(218, "Chest ", function()
    evt.OpenChest(18)
end, "Chest ")

RegisterEvent(219, "Chest ", function()
    evt.OpenChest(19)
end, "Chest ")

RegisterEvent(220, "Chest ", function()
    evt.OpenChest(0)
    if IsQBitSet(QBit(578)) then -- Placed Golem torso
        return
    elseif IsQBitSet(QBit(737)) then -- Torso - I lost it
        return
    else
        SetQBit(QBit(737)) -- Torso - I lost it
        return
    end
end, "Chest ")

RegisterEvent(250, nil, function()
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
    goto step_32
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
    goto step_31
    ::step_14::
    evt.StatusText("Fruit Tree")
    goto step_31
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
    ::step_31::
    do return end
    ::step_32::
    if IsAtLeast(MapVar(52), 1) then
        goto step_35
    end
    evt.SetSprite(51, 1, "0")
    goto step_36
    ::step_35::
    evt.SetSprite(51, 1, "0")
    ::step_36::
    if IsAtLeast(MapVar(53), 1) then
        goto step_39
    end
    evt.SetSprite(52, 1, "0")
    goto step_40
    ::step_39::
    evt.SetSprite(52, 1, "0")
    ::step_40::
    if IsAtLeast(MapVar(54), 1) then
        goto step_43
    end
    evt.SetSprite(53, 1, "0")
    goto step_44
    ::step_43::
    evt.SetSprite(53, 1, "0")
    ::step_44::
    if IsAtLeast(MapVar(55), 1) then
        goto step_47
    end
    evt.SetSprite(54, 1, "0")
    goto step_48
    ::step_47::
    evt.SetSprite(54, 1, "0")
    ::step_48::
    if IsAtLeast(MapVar(56), 1) then
        goto step_51
    end
    evt.SetSprite(55, 1, "0")
    goto step_52
    ::step_51::
    evt.SetSprite(55, 1, "0")
    ::step_52::
    if IsAtLeast(MapVar(57), 1) then
        goto step_55
    end
    evt.SetSprite(56, 1, "0")
    goto step_56
    ::step_55::
    evt.SetSprite(56, 1, "0")
    ::step_56::
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

RegisterEvent(317, "Stone City", nil, "Stone City")

RegisterEvent(318, "Dwarven Barrow", nil, "Dwarven Barrow")

RegisterEvent(319, "Mansion", nil, "Mansion")

RegisterEvent(320, "Well", nil, "Well")

RegisterEvent(321, "Drink from the Well", function()
    if not IsPlayerBitSet(PlayerBit(18)) then
        if not IsAutonoteSet(282) then -- 25 points of temporary Fire resistance from the well in the southwestern village in the Barrow Downs.
            SetAutonote(282) -- 25 points of temporary Fire resistance from the well in the southwestern village in the Barrow Downs.
        end
        AddValue(FireResistanceBonus, 25)
        SetPlayerBit(PlayerBit(18))
        evt.StatusText("+25 Fire Resistance (Temporary)")
        return
    end
    evt.StatusText("Refreshing!")
end, "Drink from the Well")

RegisterEvent(322, "Drink from the Well", function()
    if not IsAtLeast(Dead, 0) then
        evt.StatusText("Refreshing!")
        return
    end
    SetValue(MapVar(1), 0)
    evt.StatusText("Paralysis Relieved")
end, "Drink from the Well")

RegisterEvent(451, "Shrine", nil, "Shrine")

RegisterEvent(452, "Altar", function()
    if not IsPlayerBitSet(PlayerBit(29)) then
        AddValue(BaseEndurance, 10)
        AddValue(BaseMight, 10)
        SetPlayerBit(PlayerBit(29))
        evt.StatusText("+10 Endurance and Might(Permanent)")
        return
    end
    evt.StatusText("You Pray")
end, "Altar")

RegisterEvent(453, "Obelisk", function()
    if IsQBitSet(QBit(685)) then return end -- Visited Obelisk in Area 11
    evt.StatusText("ivg_whn_")
    SetAutonote(318) -- Obelisk message #10: ivg_whn_
    evt.ForPlayer(Players.All)
    SetQBit(QBit(685)) -- Visited Obelisk in Area 11
end, "Obelisk")

RegisterEvent(501, "Enter Stone City", function()
    evt.MoveToMap(245, -5362, 34, 512, 0, 0, 152, 1, "7d24.blv") -- Stone City
end, "Enter Stone City")

RegisterEvent(502, "Enter Mansion", function()
    evt.MoveToMap(2, -1096, -31, 512, 0, 0, 0, 0, "7d37.blv") -- The Haunted Mansion
end, "Enter Mansion")

RegisterEvent(503, "Enter Dwarven Barrow", function()
    evt.MoveToMap(382, 324, -15, 1280, 0, 0, 61, 4, "mdt01.blv") -- Barrow IX
end, "Enter Dwarven Barrow")

RegisterEvent(504, "Enter Dwarven Barrow", function()
    evt.MoveToMap(106, -666, 49, 256, 0, 0, 61, 4, "mdr01.blv") -- Barrow X
end, "Enter Dwarven Barrow")

RegisterEvent(505, "Enter Dwarven Barrow", function()
    evt.MoveToMap(-384, -983, 1, 256, 0, 0, 61, 4, "mdk01.blv") -- Barrow VII
end, "Enter Dwarven Barrow")

RegisterEvent(65535, "", function()
    evt.ForPlayer(Players.All)
    ClearPlayerBit(PlayerBit(18))
end)

